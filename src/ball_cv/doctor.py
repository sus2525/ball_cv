from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import ultralytics

from ball_cv.config import Settings


def _command_version(command: str, *args: str) -> str:
    executable = shutil.which(command)
    if executable is None:
        return "NOT FOUND"

    try:
        result = subprocess.run(
            [executable, *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return f"ERROR ({exc})"
    if result.returncode:
        return f"ERROR (exit={result.returncode})"
    output = (result.stdout or result.stderr).splitlines()
    return output[0] if output else "ERROR (no version output)"


def _check_runtime_directories(paths: tuple[Path, ...]) -> list[str]:
    problems = []
    for path in paths:
        if not path.is_dir():
            problems.append(f"{path}: directory is missing")
        elif not os.access(path, os.W_OK):
            problems.append(f"{path}: directory is not writable")
    return problems


def run_doctor() -> int:
    settings = Settings()

    print("ball_cv environment")
    print(f"python={sys.version.split()[0]}")
    print(f"numpy={np.__version__}")
    print(f"opencv={cv2.__version__}")
    print(f"torch={torch.__version__}")
    print(f"ultralytics={ultralytics.__version__}")
    print(f"torch_cuda_available={torch.cuda.is_available()}")
    print(f"configured_device={settings.device}")
    ffmpeg = _command_version("ffmpeg", "-version")
    print(f"ffmpeg={ffmpeg}")
    print(f"data_dir={settings.data_dir}")
    print(f"models_dir={settings.models_dir}")
    print(f"artifacts_dir={settings.artifacts_dir}")
    print(f"model_path={settings.model_path}")

    problems = _check_runtime_directories(
        (settings.data_dir, settings.models_dir, settings.artifacts_dir)
    )
    if ffmpeg.startswith(("NOT FOUND", "ERROR")):
        problems.append("ffmpeg is unavailable")
    for problem in problems:
        print(f"error={problem}")
    return int(bool(problems))
