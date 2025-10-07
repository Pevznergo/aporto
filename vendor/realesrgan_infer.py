#!/usr/bin/env python3
"""
Vendorized lightweight Real-ESRGAN inference for directory of images.
Compatible with 'realesr-general-x4v3' model. Supports optional GFPGAN face enhancement.

Usage example:
  python realesrgan_infer.py -i /path/to/frames -o /path/to/out -n realesr-general-x4v3 --outscale 4 \
    [--model_path models/realesr-general-x4v3.pth] [--face_enhance]
"""
from __future__ import annotations
import argparse
import os
import sys
import glob
import cv2

import torch
import warnings

# Reduce noisy warnings from dependencies; do not affect functionality
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning, module=r'torchvision')
warnings.filterwarnings('ignore', category=UserWarning, module=r'facexlib')
warnings.filterwarnings('ignore', category=UserWarning, module=r'gfpgan')

# Strict path for GFPGAN weights per project policy
REQUIRED_GFPGAN_WEIGHTS = 'models/GFPGANv1.4.pth'

def _require_gfpgan_weights() -> str:
    path = REQUIRED_GFPGAN_WEIGHTS
    if os.path.isfile(path):
        return path
    raise SystemExit(
        f"GFPGAN weights not found at required path: {path}. "
        f"Place GFPGANv1.4.pth in aporto/upscale/models and retry."
    )

try:
    from realesrgan.utils import RealESRGANer
except Exception as e:
    print(f"Failed to import RealESRGANer from realesrgan.utils: {e}")
    sys.exit(1)

try:
    from realesrgan.archs.srvgg_arch import SRVGGNetCompact
except Exception as e:
    print(f"Failed to import SRVGGNetCompact: {e}")
    sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Real-ESRGAN inference (vendor)")
    p.add_argument('-i', '--input', required=True, help='Input directory of images')
    p.add_argument('-o', '--output', required=True, help='Output directory for enhanced images')
    p.add_argument('-n', '--model_name', default='realesr-general-x4v3', help='Model name')
    p.add_argument('--model_path', default=None, help='Path to model weights (.pth)')
    p.add_argument('--outscale', type=int, default=4, help='Final upscaling factor for output saving')
    p.add_argument('--face_enhance', action='store_true', help='Enable GFPGAN face enhancement')
    return p


def main() -> int:
    args = build_parser().parse_args()

    in_dir = os.path.abspath(args.input)
    out_dir = os.path.abspath(args.output)
    os.makedirs(out_dir, exist_ok=True)

    # Discover input images
    exts = ('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp')
    files = []
    for e in exts:
        files.extend(sorted(glob.glob(os.path.join(in_dir, e))))
    if not files:
        print(f"No input images found in: {in_dir}")
        return 2

    model_name = (args.model_name or '').lower()
    if model_name not in ('realesr-general-x4v3',):
        print(f"Warning: unsupported model '{args.model_name}', defaulting to 'realesr-general-x4v3'.")
        model_name = 'realesr-general-x4v3'

    # Build network for general-x4v3
    netscale = 4
    net = SRVGGNetCompact(num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=netscale, act_type='prelu')

    # Device / half
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    half = device == 'cuda'

    # Create restorer using signature available in installed realesrgan.utils
    # Installed version selects device internally; do not pass device/gpu_id
    restorer = RealESRGANer(
        scale=netscale,
        model_path=args.model_path,
        model=net,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=half,
    )

    face_enhancer = None
    if args.face_enhance:
        # Enforce presence of GFPGAN weights at required path; fail fast if missing
        w = _require_gfpgan_weights()
        try:
            from gfpgan import GFPGANer
            face_enhancer = GFPGANer(model_path=w, upscale=1, arch='clean', channel_multiplier=2, bg_upsampler=restorer)
        except Exception as e:
            raise SystemExit(f"Failed to initialize GFPGAN with weights at {w}: {e}")

    # Process images
    count = 0
    for fp in files:
        img = cv2.imread(fp, cv2.IMREAD_COLOR)
        if img is None:
            print(f"Skipping unreadable image: {fp}")
            continue
        try:
            if face_enhancer is not None:
                try:
                    output, _ = face_enhancer.enhance(img, has_aligned=False, only_center_face=False, paste_back=True)
                    # Adjust final outscale if needed
                    if int(args.outscale) != netscale:
                        h0, w0 = img.shape[:2]
                        output = cv2.resize(output, (int(w0 * int(args.outscale)), int(h0 * int(args.outscale))), interpolation=cv2.INTER_LANCZOS4)
                except Exception as ge:
                    # Per-frame fallback: use RealESRGAN if GFPGAN fails on this image
                    print(f"GFPGAN failed for {fp}: {ge}; falling back to RealESRGAN for this frame")
                    output, _ = restorer.enhance(img, outscale=int(args.outscale))
            else:
                output, _ = restorer.enhance(img, outscale=int(args.outscale))
        except Exception as e:
            print(f"Enhance failed for {fp}: {e}")
            continue
        out_path = os.path.join(out_dir, os.path.basename(fp))
        ok = cv2.imwrite(out_path, output)
        if not ok:
            print(f"Failed to write output: {out_path}")
            continue
        count += 1

    if count == 0:
        print("No images were processed successfully.")
        return 1
    print(f"Enhanced {count} images to: {out_dir}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
