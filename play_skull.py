#!/usr/bin/env python3
"""Loop a pre-converted RGB565 animation on the TFT framebuffer.

Usage:  python3 play_skull.py [file.raw] [fps]
Example: python3 play_skull.py skull_rot_ccw.raw 12
"""
import os
import signal
import sys
import time

FB = "/dev/fb1"
RAW = sys.argv[1] if len(sys.argv) > 1 else "skull_rot_ccw.raw"
FPS = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
W, H = 480, 320
FRAME_BYTES = W * H * 2

with open(RAW, "rb") as f:
    data = f.read()
count = len(data) // FRAME_BYTES
if count == 0:
    sys.exit("No complete frames found in " + RAW)
view = memoryview(data)
frames = [view[i * FRAME_BYTES:(i + 1) * FRAME_BYTES] for i in range(count)]

fd = os.open(FB, os.O_WRONLY)
running = True

def stop(*_):
    global running
    running = False

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)

period = 1.0 / FPS
next_t = time.monotonic()
i = 0
while running:
    os.pwrite(fd, frames[i], 0)
    i = (i + 1) % count
    next_t += period
    delay = next_t - time.monotonic()
    if delay > 0:
        time.sleep(delay)
    else:
        next_t = time.monotonic()   # fell behind, so resync instead of rushing

os.pwrite(fd, bytes(FRAME_BYTES), 0)   # blank the screen on exit
os.close(fd)
