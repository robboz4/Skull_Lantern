#!/usr/bin/env python3
"""Convert a rendered PNG sequence into a raw RGB565 animation for the lantern's TFT.

The output is one file with the frames written back to back, ready for play_skull.py:
  - RGB565, little-endian (2 bytes per pixel)
  - 480 x 320 pixels per frame by default (the TFT framebuffer size)

The Blender scene renders portrait 320x480 frames, so by default each frame is
rotated 90 degrees to fit the landscape display, and every second frame is kept
(24 fps source -> 12 fps playback).

Requires: pip install pillow numpy

Examples:
  python3 convert_frames.py renders/ -o skull_rot_ccw.raw
  python3 convert_frames.py renders/ -o skull_rot_cw.raw --rotate cw
  python3 convert_frames.py renders/ -o skull_flipped.raw --vflip
"""
import argparse
import glob
import os
import sys

import numpy as np
from PIL import Image


def parse_size(text):
    try:
        w, h = text.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise argparse.ArgumentTypeError("size must look like 480x320")


def to_rgb565(img, swap_rb):
    """Return a 2D uint16 array of RGB565 values for a PIL image."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    q = np.rint(rgb * np.array([31, 63, 31], dtype=np.float32)).astype(np.uint16)
    r, g, b = q[:, :, 0], q[:, :, 1], q[:, :, 2]
    if swap_rb:
        r, b = b, r
    return (r << 11) | (g << 5) | b


def main():
    p = argparse.ArgumentParser(
        description="Convert a PNG sequence into a raw RGB565 animation for the TFT framebuffer."
    )
    p.add_argument("input_dir", help="folder containing the rendered PNG frames")
    p.add_argument("-o", "--output", default="skull.raw", help="output file (default: skull.raw)")
    p.add_argument("--pattern", default="*.png", help="frame filename pattern (default: *.png)")
    p.add_argument("--step", type=int, default=2,
                   help="keep every Nth frame (default 2: 24 fps source -> 12 fps playback)")
    p.add_argument("--rotate", choices=["ccw", "cw", "none"], default="ccw",
                   help="rotate each frame to fit the display (default: ccw)")
    p.add_argument("--hflip", action="store_true", help="mirror left-right after rotating")
    p.add_argument("--vflip", action="store_true", help="flip top-bottom after rotating")
    p.add_argument("--swap-rb", action="store_true",
                   help="swap red and blue, for displays that show a blue tint")
    p.add_argument("--size", type=parse_size, default=(480, 320),
                   help="expected frame size after rotating, WxH (default: 480x320)")
    args = p.parse_args()

    if args.step < 1:
        sys.exit("--step must be 1 or more")

    files = sorted(glob.glob(os.path.join(args.input_dir, args.pattern)))
    if not files:
        sys.exit("No files matching %r found in %s" % (args.pattern, args.input_dir))
    files = files[::args.step]

    out_w, out_h = args.size
    k = {"ccw": 1, "cw": -1, "none": 0}[args.rotate]

    written = 0
    with open(args.output, "wb") as out:
        for path in files:
            with Image.open(path) as img:
                px = to_rgb565(img, args.swap_rb)
            px = np.rot90(px, k)
            if args.hflip:
                px = px[:, ::-1]
            if args.vflip:
                px = px[::-1, :]
            h, w = px.shape
            if (w, h) != (out_w, out_h):
                out.close()
                os.remove(args.output)
                sys.exit(
                    "%s is %dx%d after rotating, but the display needs %dx%d. "
                    "Check --rotate, or pass --size if your display is different."
                    % (os.path.basename(path), w, h, out_w, out_h)
                )
            out.write(np.ascontiguousarray(px).astype("<u2").tobytes())
            written += 1

    size = os.path.getsize(args.output)
    print("Wrote %d frames (%dx%d, RGB565) to %s: %d bytes" % (written, out_w, out_h, args.output, size))


if __name__ == "__main__":
    main()
