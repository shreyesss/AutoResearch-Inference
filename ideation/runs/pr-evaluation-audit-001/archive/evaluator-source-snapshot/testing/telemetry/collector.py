#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import psutil
from prometheus_client.parser import text_string_to_metric_families
from pynvml import (
    NVMLError,
    nvmlDeviceGetClockInfo,
    nvmlDeviceGetCount,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetName,
    nvmlDeviceGetPcieThroughput,
    nvmlDeviceGetPowerUsage,
    nvmlDeviceGetTemperature,
    nvmlDeviceGetUtilizationRates,
    nvmlInit,
    nvmlShutdown,
)

STOP = False


def stop(*_: object) -> None:
    global STOP
    STOP = True


def prometheus_snapshot(client: httpx.Client, url: str, prefix: str) -> dict[str, float]:
    response = client.get(url)
    response.raise_for_status()
    values: dict[str, float] = {}
    for family in text_string_to_metric_families(response.text):
        for sample in family.samples:
            labels = ",".join(f"{key}={value}" for key, value in sorted(sample.labels.items()))
            key = f"{prefix}.{sample.name}"
            if labels:
                key += "{" + labels + "}"
            values[key] = float(sample.value)
    return values


def vmstat() -> dict[str, int]:
    wanted = {"numa_hit", "numa_miss", "numa_foreign", "pgmajfault"}
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/vmstat").read_text().splitlines():
            key, raw = line.split()
            if key in wanted:
                values[f"host.{key}"] = int(raw)
    except (OSError, ValueError):
        pass
    return values


def gpu_snapshot() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for index in range(nvmlDeviceGetCount()):
        handle = nvmlDeviceGetHandleByIndex(index)
        prefix = f"gpu.{index}"
        memory = nvmlDeviceGetMemoryInfo(handle)
        utilization = nvmlDeviceGetUtilizationRates(handle)
        values[f"{prefix}.name"] = nvmlDeviceGetName(handle)
        values[f"{prefix}.sm_util_percent"] = utilization.gpu
        values[f"{prefix}.memory_util_percent"] = utilization.memory
        values[f"{prefix}.hbm_used_bytes"] = memory.used
        values[f"{prefix}.hbm_total_bytes"] = memory.total
        queries = (
            ("power_w", nvmlDeviceGetPowerUsage, (handle,), 0.001),
            ("temperature_c", nvmlDeviceGetTemperature, (handle, 0), 1.0),
            ("sm_clock_mhz", nvmlDeviceGetClockInfo, (handle, 1), 1.0),
            ("memory_clock_mhz", nvmlDeviceGetClockInfo, (handle, 2), 1.0),
            ("pcie_rx_kib_s", nvmlDeviceGetPcieThroughput, (handle, 0), 1.0),
            ("pcie_tx_kib_s", nvmlDeviceGetPcieThroughput, (handle, 1), 1.0),
        )
        for name, query, query_args, scale in queries:
            try:
                values[f"{prefix}.{name}"] = query(*query_args) * scale
            except NVMLError:
                values[f"{prefix}.{name}"] = None
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--duration", type=float, default=0)
    parser.add_argument("--engine-metrics-url", action="append", default=[])
    parser.add_argument("--dcgm-metrics-url")
    parser.add_argument("--pid", type=int, action="append", default=[])
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be positive")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl = args.output_dir / "telemetry.jsonl"
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    nvmlInit()
    psutil.cpu_percent(interval=None)
    network_previous = psutil.net_io_counters()
    started = time.monotonic()
    rows: list[dict[str, Any]] = []
    client = httpx.Client(timeout=5)
    try:
        with jsonl.open("w") as handle:
            while not STOP:
                loop_started = time.monotonic()
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                network = psutil.net_io_counters()
                row: dict[str, Any] = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "elapsed_s": loop_started - started,
                    "host.cpu_percent": psutil.cpu_percent(interval=None),
                    "host.memory_used_bytes": memory.used,
                    "host.memory_available_bytes": memory.available,
                    "host.swap_used_bytes": swap.used,
                    "host.net_bytes_sent_delta": network.bytes_sent
                    - network_previous.bytes_sent,
                    "host.net_bytes_recv_delta": network.bytes_recv
                    - network_previous.bytes_recv,
                }
                network_previous = network
                row.update(vmstat())
                for process_id in args.pid:
                    try:
                        process = psutil.Process(process_id)
                        process_memory = process.memory_full_info()
                        row[f"process.{process_id}.rss_bytes"] = process_memory.rss
                        row[f"process.{process_id}.uss_bytes"] = getattr(
                            process_memory, "uss", None
                        )
                        row[f"process.{process_id}.cpu_percent"] = process.cpu_percent()
                        row[f"process.{process_id}.threads"] = process.num_threads()
                    except (psutil.Error, OSError) as exc:
                        row[f"process.{process_id}.error"] = str(exc)
                try:
                    row.update(gpu_snapshot())
                except NVMLError as exc:
                    row["gpu.error"] = str(exc)
                for index, url in enumerate(args.engine_metrics_url):
                    try:
                        row.update(prometheus_snapshot(client, url, f"engine{index}"))
                    except Exception as exc:
                        row[f"engine{index}.scrape_error"] = str(exc)
                if args.dcgm_metrics_url:
                    try:
                        row.update(
                            prometheus_snapshot(client, args.dcgm_metrics_url, "dcgm")
                        )
                    except Exception as exc:
                        row["dcgm.scrape_error"] = str(exc)
                rows.append(row)
                handle.write(json.dumps(row, default=str) + "\n")
                handle.flush()
                if args.duration and loop_started - started >= args.duration:
                    break
                time.sleep(max(0.0, args.interval - (time.monotonic() - loop_started)))
    finally:
        client.close()
        nvmlShutdown()

    if rows:
        frame = pd.DataFrame(rows)
        frame.to_parquet(args.output_dir / "telemetry.parquet", index=False)
        sm_columns = [
            column for column in frame if column.endswith(".sm_util_percent")
        ]
        hbm_columns = [
            column for column in frame if column.endswith(".hbm_used_bytes")
        ]
        power_columns = [column for column in frame if column.endswith(".power_w")]
        elapsed = (
            float(frame["elapsed_s"].iloc[-1] - frame["elapsed_s"].iloc[0])
            if len(frame) > 1
            else 0.0
        )
        total_power = frame[power_columns].sum(axis=1) if power_columns else None
        summary = {
            "samples": len(frame),
            "elapsed_s": elapsed,
            "gpu_sm_util_mean_percent": None
            if not sm_columns
            else float(frame[sm_columns].mean(axis=1).mean()),
            "gpu_sm_util_peak_percent": None
            if not sm_columns
            else float(frame[sm_columns].max(axis=1).max()),
            "node_hbm_peak_bytes": None
            if not hbm_columns
            else float(frame[hbm_columns].sum(axis=1).max()),
            "node_power_mean_w": None
            if total_power is None
            else float(total_power.mean()),
            "node_energy_j": None
            if total_power is None
            else float(total_power.mean() * elapsed),
        }
        (args.output_dir / "telemetry-summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
    print(f"Telemetry samples: {len(rows)}")


if __name__ == "__main__":
    main()
