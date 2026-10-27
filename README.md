# Gesture Control: Brightness, Screenshot & Sign Translator

A real-time hand-gesture app built with OpenCV and MediaPipe. It uses your webcam to track both hands and does three things:

1. **Brightness control** – pinch your thumb and index finger (right side of the frame) to set screen brightness.
2. **Screenshot** – swipe an open hand downward (left side of the frame) to capture the screen.
3. **Sign translator** – shows a text meaning for a few simple hand signs on the right hand.

## How It Works

The frame is mirrored and split into two halves. Which half a hand's wrist is in decides what that hand does.

| Hand position (in mirrored frame) | Function |
|---|---|
| Right half | Brightness control + sign recognition |
| Left half | Screenshot trigger |

### 1. Brightness Control (right half)
- Draws a line between the **thumb tip (landmark 4)** and **index fingertip (landmark 8)**.
- The pixel distance between them is mapped to brightness: **25 px → 0 %**, **250 px → 100 %**.
- Brightness is set with `screen_brightness_control`, and a bar on the left of the window shows the current level.
- Pinch closer to dim, spread apart to brighten.

### 2. Screenshot (left half)
- Hold your hand open (3 or more fingers extended, not counting the thumb) and move it **downward quickly** (wrist moves more than 3 % of frame height between frames).
- A full-screen screenshot is saved in the current folder as `screenshot_<timestamp>.png`.
- A 2-second cooldown prevents repeat captures, and a "SCREENSHOT TAKEN!" message flashes on the camera view.

### 3. Sign Meanings (right half)
Shown in the box at the top-right of the window.

| Fingers extended (Thumb, Index, Middle, Ring, Pinky) | Gesture | Meaning shown |
|---|---|---|
| 1 0 0 0 0 (thumb pointing up) | Thumbs up | YES / GOOD |
| 1 1 1 1 1 | Open palm | HELLO / STOP |
| 0 0 0 0 0 | Fist | READY / STRONG |
| 0 1 1 0 0 | Two fingers | PEACE / VICTORY |
| 0 1 0 0 0 | Index finger | ATTENTION |

When no sign matches, the box shows "Waiting for Sign...".

## Requirements

- Python 3.9+
- A webcam
- Windows or macOS recommended (brightness control and screenshots need a desktop display; brightness control also needs a monitor/laptop that supports software brightness changes)

### Python packages

```bash
pip install opencv-python mediapipe numpy screen-brightness-control pyautogui
```

## Setup & Running

1. Put `motion.py` in a folder.
2. Make sure `hand_landmarker.task` (the MediaPipe hand model) is in the same folder. If it is missing, the script downloads it automatically on first run from:
   `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`
3. Run:

```bash
python motion.py
```

4. Press **`q`** in the camera window to quit.

## Project Files

```
.
├── motion.py              # Main script
├── hand_landmarker.task   # MediaPipe hand landmark model
└── screenshot_*.png       # Generated screenshots
```

## Configuration

These values are set at the top of `motion.py` / in the main loop and can be tuned:

| Setting | Default | What it does |
|---|---|---|
| `num_hands` | `2` | Max number of hands tracked |
| `min_hand_detection_confidence` | `0.6` | Detection confidence threshold |
| `min_hand_presence_confidence` | `0.6` | Presence confidence threshold |
| Pinch range | `[25, 250]` px | Distance range mapped to 0–100 % brightness |
| Swipe threshold | `0.03` | Downward wrist movement needed for a screenshot |
| Screenshot cooldown | `2.0` s | Minimum time between screenshots |
| `cv2.VideoCapture(0)` | `0` | Camera index (change if you have multiple cameras) |

## Tips & Known Limitations

- Use good, even lighting and keep your hands clearly in view.
- Keep each hand on its own side of the frame. A hand crossing the center line switches function.
- The thumb check is based on the x-axis, so the sign detection is tuned for one hand orientation (palm facing the camera) and may misread the thumb in other poses.
- Brightness updates continuously whenever a hand is on the right side, so keep it away from the right half when you don't want to change brightness.
- If brightness control fails on your display, the error is silently ignored and the bar will still move.
- On Linux, `pyautogui` screenshots need an active X11 session.

## Tech Stack

- [OpenCV](https://opencv.org/) – camera capture and UI drawing
- [MediaPipe Tasks (Hand Landmarker)](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker) – hand landmark detection
- [NumPy](https://numpy.org/) – value mapping
- [screen-brightness-control](https://pypi.org/project/screen-brightness-control/) – brightness changes
- [PyAutoGUI](https://pyautogui.readthedocs.io/) – screenshots
