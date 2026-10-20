"""Root-owned bounded container execution; no experiment expectations here."""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time

RUN = Path(__file__).resolve().parent
IMAGE = "vllm/vllm-openai@sha256:3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c"
GPU = "GPU-fc81ee05-2051-5148-0563-47bdb726dbc4"
MODEL = Path("/home/jl_fs/models/DeepSeek-V4.1-Flash").resolve()


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--timeout-seconds", type=int, required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--input", action="append", required=True)
    parser.add_argument("--mount-model", action="store_true")
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("Simple unique experiment ID required")
    if not 1 <= args.timeout_seconds <= 3600:
        raise ValueError("Component allocation cannot exceed one hour")
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not argv:
        raise ValueError("Missing exact reviewed command")
    files = [Path(x).resolve() for x in [args.contract, args.review] + args.input]
    files.append(Path(__file__).resolve())
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    out = RUN / "executions" / args.id
    out.mkdir(parents=True, exist_ok=False)
    with Path("/tmp/autoresearch-h200-gpu.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Conservatively require the whole shared node idle before this pilot.
        processes = command("nvidia-smi", "--query-compute-apps=pid,gpu_uuid", "--format=csv,noheader")
        if processes:
            raise RuntimeError("GPU processes present: " + processes)
        if command("docker", "ps", "-q"):
            raise RuntimeError("A running container needs review before GPU allocation")
        name = "h200-overnight-" + args.id
        docker = ["docker", "run", "--rm", "--name", name, "--network", "none",
                  "--gpus", "device=" + GPU, "--shm-size", "1g",
                  "--env", "VLLM_NO_USAGE_STATS=1", "--env", "DO_NOT_TRACK=1",
                  "--env", "HF_HUB_OFFLINE=1", "--env", "PYTHONDONTWRITEBYTECODE=1",
                  "--env", "TRITON_CACHE_DIR=/out/cache/triton",
                  "--env", "TORCHINDUCTOR_CACHE_DIR=/out/cache/inductor",
                  "--volume", str(RUN) + ":/work:ro",
                  "--volume", str(out) + ":/out:rw"]
        if args.mount_model:
            docker.extend(["--volume", str(MODEL) + ":/model:ro"])
        docker.extend(["--workdir", "/work", "--entrypoint", "python3", IMAGE] + argv)
        record = {"id": args.id, "started_at_utc": stamp(), "input_sha256": hashes,
                  "contract": args.contract, "independent_review": args.review,
                  "host": command("hostname"), "gpu": GPU, "allocated_gpus": 1,
                  "timeout_seconds": args.timeout_seconds, "command": docker,
                  "gpu_before": command("nvidia-smi", "--query-gpu=index,uuid,memory.used,utilization.gpu", "--format=csv,noheader"),
                  "state": "running", "service_attempts_consumed": 0}
        write(out / "execution.json", record)
        with (RUN / "journal.jsonl").open("a") as journal:
            journal.write(json.dumps({"time_utc": stamp(), "event": "component_started", "id": args.id, "receipt": str(out / "execution.json")}) + "\n")
        start = time.monotonic()
        try:
            with (out / "stdout.log").open("w") as output:
                process = subprocess.Popen(docker, stdout=output, stderr=subprocess.STDOUT)
                try:
                    record["exit_code"] = process.wait(timeout=args.timeout_seconds)
                    record["state"] = "completed" if record["exit_code"] == 0 else "failed"
                except subprocess.TimeoutExpired:
                    record["state"] = "timeout"
                    subprocess.run(["docker", "stop", "--time", "10", name], capture_output=True)
                    process.wait(timeout=30)
                    record["exit_code"] = process.returncode
        finally:
            cleanup = subprocess.run(["docker", "rm", "-f", name], capture_output=True, text=True)
            record["cleanup"] = {"returncode": cleanup.returncode, "stdout": cleanup.stdout, "stderr": cleanup.stderr}
            record["wall_seconds"] = time.monotonic() - start
            record["allocated_GPU_hours"] = record["wall_seconds"] / 3600
            record["eight_GPU_node_equivalent_hours"] = record["wall_seconds"] * 8 / 3600
            record["cost_note"] = "One GPU visible; all-node idle/exclusive checks also retained. Eight-GPU node equivalent shown separately; node price unknown."
            record["finished_at_utc"] = stamp()
            record["changed_inputs"] = [str(p) for p in files if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != hashes[str(p)]]
            record["gpu_after"] = command("nvidia-smi", "--query-gpu=index,uuid,memory.used,utilization.gpu", "--format=csv,noheader")
            record["gpu_processes_after"] = command("nvidia-smi", "--query-compute-apps=pid,gpu_uuid", "--format=csv,noheader")
            record["running_containers_after"] = command("docker", "ps", "--format", "{{.Names}}")
            write(out / "execution.json", record)
            with (RUN / "journal.jsonl").open("a") as journal:
                journal.write(json.dumps({"time_utc": stamp(), "event": "component_finished", "id": args.id, "state": record["state"], "GPU_hours": record["allocated_GPU_hours"]}) + "\n")
        print(json.dumps(record, indent=2))
        if record["state"] != "completed" or record["changed_inputs"] or record["gpu_processes_after"] or record["running_containers_after"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
