from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lib import serve_recipe as serve


class C03LauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.c03 = self.root / "c03"
        self.destination = "vllm/v1/worker/gpu/dp_utils.py"
        base = self.c03 / "source/base" / self.destination
        base.parent.mkdir(parents=True)
        base.write_text("BASE = True\n")
        self.base_hash = hashlib.sha256(base.read_bytes()).hexdigest()
        source = self.c03 / "source/diagnostic-base" / self.destination
        source.parent.mkdir(parents=True)
        source.write_text("BASE = True\n# diagnostic observation only\n")
        self.source = source
        self.manifest = self.c03 / "diagnostic-manifest.json"
        self.payload = {
            "schema_version": 1, "image": serve.C03_IMAGE,
            "files": [{"path": self.destination,
                       "source": str(source.relative_to(self.c03)),
                       "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "base_sha256": self.base_hash}],
        }
        (self.c03 / "source/snapshot-manifest.json").write_text(json.dumps({
            "image": serve.C03_IMAGE,
            "files": [{"path": self.destination, "sha256": self.base_hash}],
        }))
        self.environment = {
            "MODEL_STORAGE_ROOT": str(self.root / "storage"),
            "HF_HOME": str(self.root / "hf"),
            "ENGINE_CACHE_ROOT": str(self.root / "cache"),
            "PROFILER_CACHE_ROOT": str(self.root / "profiles"),
            "MODEL": "deepseek-ai/DeepSeek-V4.1-Flash",
            "SERVED_MODEL": "deepseek-v4.1-flash",
            "MODEL_REVISION": "2cba9e42aa026125f3ed06c6d98c1db82f7ca027",
            "SKIP_PREFLIGHT": "1",
        }

    def load(self):
        self.manifest.write_text(json.dumps(self.payload))
        with mock.patch.object(serve, "ROOT", self.root):
            return serve.load_c03_source_manifest(self.manifest, serve.C03_IMAGE)

    def test_readonly_mounts_and_replica_identity_preserve_binary_image(self):
        overlay = self.load()
        commands = []
        with mock.patch.dict(os.environ, self.environment, clear=True):
            for replica in range(2):
                commands.append(serve.common_docker(
                    name=f"replica-{replica}", gpu_ids="0,1,2,3",
                    image=serve.C03_IMAGE, engine="vllm", extra_env={},
                    engine_args=["serve", "model"], nsys_output=None,
                    c03_sources=overlay, replica_id=replica,
                ))
        for replica, command in enumerate(commands):
            mount = command[command.index("--mount") + 1]
            self.assertIn(f"dst={serve.C03_PACKAGE_ROOT}/{self.destination}", mount)
            self.assertTrue(mount.endswith(",readonly"))
            self.assertLess(command.index("--mount"), command.index(serve.C03_IMAGE))
            self.assertIn("PYTHONPYCACHEPREFIX=/tmp/c03-pycache", command)
            self.assertIn(f"C03_REPLICA_ID={replica}", command)
            self.assertEqual(command[-4:], ["vllm", serve.C03_IMAGE, "serve", "model"])
        self.assertEqual(commands[0][commands[0].index("--mount") + 1],
                         commands[1][commands[1].index("--mount") + 1])

    def test_changed_source_or_original_is_rejected(self):
        self.source.write_text("UNREVIEWED = True\n")
        with self.assertRaisesRegex(ValueError, "source hash mismatch"):
            self.load()
        self.payload["files"][0]["sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        (self.c03 / "source/base" / self.destination).write_text("BASE_CHANGED = True\n")
        with self.assertRaisesRegex(ValueError, "baseline hash mismatch"):
            self.load()

    def test_path_escape_duplicate_and_unapproved_target_are_rejected(self):
        item = self.payload["files"][0]
        original = dict(item)
        for mutation in ({"source": "../outside.py"},
                         {"path": "/etc/passwd"},
                         {"path": "vllm/../sitecustomize.py"}):
            with self.subTest(mutation=mutation):
                item.update(mutation)
                with self.assertRaises(ValueError):
                    self.load()
                item.clear()
                item.update(original)
        self.payload["files"].append(dict(item))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.load()

    def test_digest_and_base_sha_are_required(self):
        self.payload["image"] = "vllm:latest"
        with self.assertRaisesRegex(ValueError, "digest"):
            self.load()
        self.payload["image"] = serve.C03_IMAGE
        self.payload["files"][0]["base_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "baseline hash"):
            self.load()

    def test_diagnostic_helper_and_output_are_scoped(self):
        helper = self.c03 / "helper.py"
        helper.write_text("ENABLED = True\n")
        self.payload["files"].append({
            "path": serve.C03_DIAGNOSTIC_HELPER, "source": "helper.py",
            "sha256": hashlib.sha256(helper.read_bytes()).hexdigest(), "base_sha256": None,
        })
        self.payload["environment"] = {
            "C03_DIAGNOSTIC": "1", "C03_DIAGNOSTIC_EPOCH": "A-001",
            "C03_DIAGNOSTIC_DIR": "/profiles/c03/A-001",
        }
        self.assertEqual(self.load()["environment"], self.payload["environment"])
        self.payload["environment"]["PYTHONPATH"] = "/unreviewed"
        with self.assertRaisesRegex(ValueError, "environment override"):
            self.load()
        del self.payload["environment"]["PYTHONPATH"]
        self.payload["environment"]["C03_DIAGNOSTIC_DIR"] = "/profiles/c03/../other"
        with self.assertRaisesRegex(ValueError, "output"):
            self.load()

    def test_empty_baseline_overlay_has_same_cache_policy_without_probe(self):
        self.payload["files"] = []
        overlay = self.load()
        self.assertEqual(overlay["mounts"], [])
        self.assertEqual(overlay["environment"], {})

    def test_backend_only_render_and_lifecycle_never_start_router(self):
        # Read existing profile inputs, but never start a process or touch GPUs.
        base = serve.load_yaml(serve.ROOT / "serving/h200/vllm/base.yaml")
        images = serve.load_yaml(serve.ROOT / "serving/h200/vllm/images.yaml")
        profile = serve.load_yaml(serve.ROOT / "serving/h200/vllm/profiles/latency-2xdep4-sla.yaml")
        argv = ["serve_recipe.py", "--hardware", "h200", "--engine", "vllm",
                "--profile", "latency-2xdep4-sla", "--backends-only"]
        with mock.patch.dict(os.environ, self.environment, clear=True), \
             mock.patch.object(serve, "load_yaml", side_effect=[base, images, profile]), \
             mock.patch("sys.argv", argv + ["--dry-run"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                serve.main()
        commands = [shlex.split(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(command[:2] == ["docker", "run"] for command in commands))
        self.assertFalse(any("router.py" in word for command in commands for word in command))
        process = mock.Mock()
        process.poll.return_value = 0
        with mock.patch.dict(os.environ, self.environment, clear=True), \
             mock.patch.object(serve, "load_yaml", side_effect=[base, images, profile]), \
             mock.patch("sys.argv", argv), \
             mock.patch.object(serve, "wait_ready") as ready, \
             mock.patch.object(serve.subprocess, "Popen", return_value=process) as popen, \
             mock.patch.object(serve.signal, "signal"):
            with self.assertRaises(SystemExit) as stopped:
                serve.main()
        self.assertEqual(stopped.exception.code, 0)
        self.assertEqual(popen.call_count, 2)
        self.assertEqual(ready.call_count, 2)
        self.assertFalse(any("router.py" in word for call in popen.call_args_list
                             for word in call.args[0]))

    def test_overlay_requires_exact_profile_and_backend_only(self):
        with mock.patch("sys.argv", ["serve_recipe.py", "--hardware", "h200",
                         "--engine", "vllm", "--profile", "balanced",
                         "--c03-source-manifest", str(self.manifest)]), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:
                serve.main()
        self.assertEqual(stopped.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
