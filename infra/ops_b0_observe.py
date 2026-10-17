"""Lightweight host GPU timeline for live B0 AIPerf cells."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path


QUERY = ["nvidia-smi", "--query-gpu=timestamp,uuid,memory.used,utilization.gpu,power.draw",
         "--format=csv,noheader"]


class GPURecorder:
    def __init__(self, path: Path, period_s: float = 2.0):
        self.path = path
        self.period_s = period_s
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        with self.path.open("w") as stream:
            stream.write("timestamp,uuid,memory_used,utilization_gpu,power_draw\n")
            while not self.stop_event.is_set():
                result = subprocess.run(QUERY, capture_output=True, text=True,
                                        timeout=10, check=False)
                if result.returncode == 0:
                    stream.write(result.stdout)
                    stream.flush()
                self.stop_event.wait(self.period_s)

    def __enter__(self) -> "GPURecorder":
        self.thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop_event.set()
        self.thread.join(timeout=12)
