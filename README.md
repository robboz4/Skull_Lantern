# Skull Lantern

A DIY Pepper's Ghost Halloween lantern: a glowing skull that floats, sways and nods inside a tube. A Raspberry Pi drives a small TFT screen in the base, and an angled acrylic reflector inside the tube bounces the image up so the skull appears to hover in mid-air.

**Preview:** [final_skull.mov](final_skull.mov)

## How it works

1. **The animation is built in Blender.** A detailed skull model ([`models/skull.stl`](models/skull.stl)) sways side to side, floats up and down, nods forward and back, and slowly shrinks and grows. It has a subtle procedural grain texture and sits on a pure black background. Black vanishes in the reflection, so only the skull is visible.
2. **Frames are rendered at 320x480, 24 fps**, as a seamless 5-second loop (120 frames).
3. **Frames are converted ahead of time** to raw RGB565 pixel data at the display's native 480x320 size. Every second frame is kept (60 frames, 12 fps), rotated to match the screen.
4. **The Pi only copies bytes.** A tiny Python player writes each pre-converted frame straight into the display's framebuffer (`/dev/fb1`) on a timer. There is no image decoding at runtime, which is what lets this run on an original Raspberry Pi Model A+.
5. **A 45-degree acrylic reflector** in the tube turns the screen image into a floating skull.

## Hardware

- Raspberry Pi Model A+ (BCM2835, single-core ARMv6) running Raspbian 13 (trixie)
- 3.5" TFT display, 480x320, HX8357D controller (`pitft35-resistive` overlay)
- 4.0 in outside-diameter tube, cut at 45 degrees
- 3 mm (1/8 in) clear cast acrylic reflector, sandwiched between the two 45-degree cut faces of the tube and cut from [`reflector_template_v3_sandwich.svg`](reflector_template_v3_sandwich.svg)
  - The pane is an ellipse of 142.7 x 100.6 mm. The tube's cut-face ellipse is 101.6 x 143.7 mm, and the pane is about 0.5 mm smaller all round so it doesn't overhang.
  - The template is 150 x 110 mm, with a red hairline marking the vector cut.

## Repository contents

| File | What it is |
| --- | --- |
| `play_skull.py` | Loops a raw animation file on the TFT framebuffer |
| `install_skull_service.sh` | Installs the player as a systemd service so it starts at boot |
| `convert_frames.py` | Converts a rendered PNG sequence into a raw animation file |
| `skull_rot_ccw.raw` | The animation, rotated counter-clockwise (60 frames, 18.4 MB) |
| `skull_rot_cw.raw` | The same animation, rotated clockwise (60 frames, 18.4 MB) |
| `skull_ghost_lantern.blend` | The Blender 5.2 scene (model, lighting, animation, render settings) |
| `models/skull.stl` | The skull model used in the scene |
| `reflector_template_v3_sandwich.svg` | Cutting template for the acrylic reflector |
| `final_skull.mov` | Preview video of the finished animation |

## Raspberry Pi setup

### 1. Enable the display

Add these lines to `/boot/firmware/config.txt`:

```
dtparam=spi=on
dtoverlay=pitft35-resistive,rotate=90,speed=62000000,fps=30
```

Reboot, then check the display driver loaded:

```bash
cat /sys/class/graphics/fb1/name    # should print: fb_hx8357d
```

The TFT is `/dev/fb1`. (`/dev/fb0` is the HDMI output.)

### 2. Try it

Copy this folder to the Pi, then:

```bash
python3 play_skull.py skull_rot_ccw.raw 12
```

The second argument is the playback frame rate. Press Ctrl+C to stop; the screen is blanked on exit. If you get a permission error on `/dev/fb1`, run it with `sudo`.

### 3. Pick the right rotation

Which `.raw` file looks right depends on how the display is mounted in your lantern. If the skull is sideways or upside-down, try the other file (`skull_rot_cw.raw`). Judge it by the **reflection** in the angled reflector, not by the raw screen.

### 4. Start automatically at boot

From the folder containing the files:

```bash
sudo bash install_skull_service.sh skull_rot_ccw.raw 12
```

This copies the player and animation to `/opt/skull-lantern/`, adds a launcher that waits for the display to appear at boot, and enables a systemd service called `skull-lantern` that restarts itself if it ever stops. Run the script again with a different file or frame rate to change them.

```bash
sudo systemctl status skull-lantern          # is it running?
sudo journalctl -u skull-lantern -n 20       # recent errors
sudo systemctl stop skull-lantern            # stop temporarily
sudo systemctl disable --now skull-lantern   # stop and disable auto-start
```

## Animation file format

| Property | Value |
| --- | --- |
| Frame size | 480 x 320 pixels |
| Pixel format | RGB565, little-endian (2 bytes per pixel) |
| Bytes per frame | 307,200 |
| Frames per file | 60 (18,432,000 bytes) |
| Source frame rate | 24 fps, every second frame kept |
| Playback | 12 fps plays the 5-second loop in real time |

The two files differ only in which way the 320x480 portrait render was rotated to fit the landscape framebuffer.

## Changing or re-rendering the animation

1. Open `skull_ghost_lantern.blend` in Blender 5.2. The scene is already set to 320x480, frames 1 to 120 at 24 fps, with an orthographic camera, three area lights and a black background. The skull object is `SkullSTL` with the `SkullBoneGrain` material.
2. Set an output folder and use **Render > Render Animation** to produce a PNG sequence.
3. Convert the frames with [`convert_frames.py`](convert_frames.py) (needs `pip install pillow numpy`):

   ```bash
   python3 convert_frames.py path/to/frames -o skull_rot_ccw.raw              # counter-clockwise
   python3 convert_frames.py path/to/frames -o skull_rot_cw.raw --rotate cw   # clockwise
   ```

   By default it keeps every second frame (24 fps to 12 fps), rotates each frame to fit the 480x320 display, and writes RGB565 in the format above. Other options: `--swap-rb` (display shows a blue tint), `--hflip` / `--vflip` (correct the orientation of the reflection), `--step 1` (keep every frame) and `--pattern` (frame filename pattern). Run it with `--help` for the full list.

## Troubleshooting

- **No `/dev/fb1`**: the display overlay isn't loaded. Check `config.txt` and reboot.
- **Skull is sideways or upside-down**: use the other `.raw` file.
- **Colours look wrong (blue tint instead of warm bone)**: red and blue are swapped on your display, so regenerate the frames with `convert_frames.py --swap-rb`.
- **Playback is choppy**: lower the frame rate argument (for example `10`).
- **Boot text or a blinking cursor shows on the TFT**: the console is mapped to the same framebuffer as the animation.

## Credits

- Skull model (`models/skull.stl`): https://www.thingiverse.com/thing:443779 licensed under the Creative Commons - Attribution - Share Alike license.
- Skull pick holderRemixed:  https://www.thingiverse.com/thing:4645648 licensed under the Creative Commons - Attribution license.)

