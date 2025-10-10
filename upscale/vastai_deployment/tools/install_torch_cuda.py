#!/usr/bin/env python3
"""
install_torch_cuda.py

Detect CUDA version via nvidia-smi and install matching CUDA-enabled PyTorch wheels.

Usage:
  python3 upscale/vastai_deployment/tools/install_torch_cuda.py [--dry-run]

Env overrides:
  TORCH_INDEX_URL   - explicit index URL (e.g. https://download.pytorch.org/whl/cu118)
  TORCH_VERSION     - e.g. 2.4.1
  TORCHVISION_VERSION - e.g. 0.19.1
  TORCHAUDIO_VERSION  - optional

Defaults map CUDA >=12 -> cu121, CUDA 11.x -> cu118.
"""
import os
import re
import shlex
import subprocess
import sys


def run(cmd, check=True):
    print("+", " ".join(shlex.quote(c) for c in cmd))
    return subprocess.run(cmd, check=check)


def detect_cuda_version() -> str:
    try:
        r = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        if r.returncode == 0:
            m = re.search(r"CUDA Version:\s*([0-9]+\.[0-9]+)", r.stdout)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def pick_index(cuda_ver: str) -> str:
    env = os.getenv("TORCH_INDEX_URL")
    if env:
        return env
    # Fallback mapping
    try:
        major = int(cuda_ver.split(".")[0])
    except Exception:
        major = 12
    if major >= 12:
        return "https://download.pytorch.org/whl/cu121"
    return "https://download.pytorch.org/whl/cu118"


def main():
    dry_run = "--dry-run" in sys.argv
    cuda_ver = detect_cuda_version()
    idx = pick_index(cuda_ver)
    torch_v = os.getenv("TORCH_VERSION", "2.4.1")
    tv_v = os.getenv("TORCHVISION_VERSION", "0.19.1")
    ta_v = os.getenv("TORCHAUDIO_VERSION", "")

    print(f"Detected CUDA: {cuda_ver or '<unknown>'}")
    print(f"Using index: {idx}")
    print(f"torch=={torch_v} torchvision=={tv_v} torchaudio=={ta_v or '<skip>'}")

    cmds = [
        [sys.executable, "-m", "pip", "uninstall", "-y", "torch", "torchvision", "torchaudio"],
        [sys.executable, "-m", "pip", "cache", "purge"],
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", "--index-url", idx,
         f"torch=={torch_v}", f"torchvision=={tv_v}"] + ([f"torchaudio=={ta_v}"] if ta_v else []),
    ]
    if dry_run:
        print("DRY-RUN; would execute:")
        for c in cmds:
            print(" ", " ".join(shlex.quote(x) for x in c))
        return 0
    for c in cmds:
        run(c)
    # Final check
    code = subprocess.run([sys.executable, "-c", "import torch; import sys; print('cuda:', torch.cuda.is_available())"])
    return code.returncode


if __name__ == "__main__":
    sys.exit(main())
