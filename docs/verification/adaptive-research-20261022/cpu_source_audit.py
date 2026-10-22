"""Offline source-dependency and benchmark-exposure audit; imports no GPU library."""
import ast
import hashlib
import json
import pathlib
import platform
import statistics

ROOT = pathlib.Path(__file__).resolve().parent
source = ROOT / "source-audit/vllm__models__deepseek_v41__common__engram.py"
tree = ast.parse(source.read_text())
engram = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Engram")
forward = next(n for n in engram.body if isinstance(n, ast.FunctionDef) and n.name == "forward")
calls = [n for n in ast.walk(forward) if isinstance(n, ast.Call)
         and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
         and n.func.value.id == "self" and n.func.attr == "wkv"]
assert len(calls) == 2
projection_inputs = []
for call in calls:
    names = sorted({n.id for arg in call.args for n in ast.walk(arg) if isinstance(n, ast.Name)})
    assert "hidden_states" not in names
    assert "token_mask" not in names
    projection_inputs.append({"line": call.lineno, "call": ast.unparse(call), "direct_names": names})
batch = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "EngramBatch")
batch_wkv_calls = [ast.unparse(n) for n in ast.walk(batch) if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr == "wkv"]
assert batch_wkv_calls == []
lookup = next(n for n in engram.body if isinstance(n, ast.FunctionDef) and n.name == "_start_prefetch")
assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "lookup"
           for n in ast.walk(lookup))
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "wkv"
               for n in ast.walk(lookup))

expected = {
    "median": "52802e6c3d00062527fbb968b44928f5d5b71349be5b99a2b2d2759855086f0e",
    "burst": "6892a59dc5b7ab5d661826c9a937fbbd44ed0f259719bca491bc9b67bb0d9566",
    "cache-heavy": "6fec019f57d0bc7cae2bde1a5136338071b10670c9f8009b56f96af87e7ee9ea",
}
workloads = []
for name, digest in expected.items():
    path = ROOT / "workloads" / (name + ".jsonl")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    out = [r["output_length"] for r in rows]
    inp = [r["input_length"] for r in rows]
    total_output = sum(out)
    cohorts = {str(n): {"requests": sum(x >= n for x in out),
                       "output_tokens": sum(x for x in out if x >= n),
                       "request_fraction": sum(x >= n for x in out) / len(rows),
                       "output_token_fraction": sum(x for x in out if x >= n) / total_output}
               for n in [256, 512, 1024]}
    workloads.append({"name": name, "sha256": digest, "requests": len(rows),
                      "input_mean": statistics.mean(inp), "input_max": max(inp),
                      "output_mean": statistics.mean(out), "output_max": max(out),
                      "output_tokens": total_output, "long_output_cohorts": cohorts,
                      "time_span_in_trace_units": max(r["timestamp"] for r in rows)-min(r["timestamp"] for r in rows)})

result = {
    "scope": "static_source_and_workload_metadata_only",
    "environment": {"python": platform.python_version(), "machine": platform.machine()},
    "source_commit": "c4557869393db4d75c483d92edd02a5125500883",
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "probe_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    "projection_calls": projection_inputs,
    "batch_staging_executes_wkv": False,
    "existing_prefetch_executes_wkv": False,
    "direct_projection_inputs_depend_on_hidden_states": False,
    "workloads": workloads,
    "limitations": [
        "Direct AST dependencies are not a proof that the GEMM backend is stream-safe or pure.",
        "The inspected research-fork commit is not linked to the installed image digest.",
        "Input/output lengths are planned trace metadata, not measured completions, cache misses or iteration shapes.",
        "No device timing, target quality, overlap, hardware availability or service improvement is measured.",
    ],
    "gpu_calls": 0,
}
(ROOT / "cpu_source_audit.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
