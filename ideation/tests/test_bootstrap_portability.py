"""Dry-run portability checks; no package installation, Git network or GPU use."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Path(__file__).resolve().parents[2]
        cls.script = cls.repo / "scripts" / "bootstrap-node.sh"
        cls.python = shutil.which("python3.12")
        candidate = Path.home() / ".local/bin/python3.12"
        if not cls.python and candidate.exists():
            cls.python = str(candidate)
        if not cls.python and sys.version_info >= (3, 11):
            cls.python = sys.executable
        if not cls.python:
            raise unittest.SkipTest("Python 3.11+ is required for bootstrap tests")

    def invoke(self, *args):
        return subprocess.run(["bash", str(self.script), "--python", self.python, "--dry-run", *args],
                              text=True, capture_output=True, timeout=15)

    def test_dry_run_leaves_state_and_environment_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary) / "state"
            venv = Path(temporary) / "venv"
            result = self.invoke("--state-root", str(state), "--venv-root", str(venv), "--storage")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("No changes made", result.stdout)
            self.assertFalse(state.exists())
            self.assertFalse(venv.exists())

    def test_rejects_nested_state_and_symlink_escape(self):
        result = self.invoke("--state-root", str(self.repo / "state"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the research checkout", result.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            link = Path(temporary) / "code-link"
            link.symlink_to(self.repo, target_is_directory=True)
            result = self.invoke("--state-root", str(link / "state"))
            self.assertNotEqual(result.returncode, 0)

    def test_rejects_credential_url_and_option_like_ref(self):
        result = self.invoke("--bitlane-repo", "https://user:fake-secret@example.invalid/repo.git")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("fake-secret", result.stdout + result.stderr)
        result = self.invoke("--bitlane-ref", "--force")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid Bitlane ref", result.stderr)

    def test_rejects_nested_code_checkouts(self):
        result = self.invoke("--bitlane-dir", str(self.repo / "bitlane"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("separate code checkout", result.stderr)


if __name__ == "__main__":
    unittest.main()
