import os
import platform
import shutil
import subprocess
from pathlib import Path

import psutil


def _disk_path() -> str:
    if os.name == "nt":
        return Path.cwd().anchor or "C:\\"
    return "/"


def _mb(value: int) -> float:
    return round(value / 1024 / 1024, 1)


def _gpu_devices() -> list[dict]:
    binary = shutil.which("nvidia-smi")
    if not binary:
        return []
    try:
        output = subprocess.run(
            [
                binary,
                "--query-gpu=name,utilization.gpu,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return []
    devices: list[dict] = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            devices.append(
                {
                    "name": parts[0],
                    "utilization_percent": int(float(parts[1])),
                    "memory_total_mb": int(float(parts[2])),
                    "memory_used_mb": int(float(parts[3])),
                }
            )
    return devices


def get_system_status() -> dict:
    process = psutil.Process(os.getpid())
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(_disk_path())
    gpus = _gpu_devices()
    return {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory": {
            "total_mb": _mb(memory.total),
            "used_mb": _mb(memory.used),
            "percent": memory.percent,
        },
        "disk": {
            "path": _disk_path(),
            "total_gb": round(disk.total / 1024**3, 2),
            "used_gb": round(disk.used / 1024**3, 2),
            "percent": disk.percent,
        },
        "process": {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(interval=None),
            "memory_mb": _mb(process.memory_info().rss),
            "threads": process.num_threads(),
        },
        "gpu": {
            "available": len(gpus) > 0,
            "devices": gpus,
        },
    }
