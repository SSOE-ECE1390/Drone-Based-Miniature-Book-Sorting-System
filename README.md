# Drone-Based Miniature Book Sorting System

Current code status: May 2026

This repository contains the control software for a DJI Tello based miniature book-sorting system with an ESP32-controlled shelf. The active runtime path has changed from the earlier YOLO-based design notes: the current code uses GPT vision to convert camera frames into symbol sequences, then drives a shelf-swap state machine that tells the ESP32 which slots to hold or release.

## What The Code Does Now

The current software is focused on shelf validation and shelf-side sorting logic.

When `main.py` runs:

1. `ShelfController` connects to the ESP32 over serial.
2. A `Tello` object is created for the drone connection.
3. `TelloUI` opens the main video/control window.
4. `TestUI` opens as a second window attached to the main UI so shelf outputs can be tested manually.
5. The Tello UI video loop samples frames from the drone.
6. Every 2 seconds, one frame is sent through `FrameToSymbols`.
7. `FrameToSymbols` calls the OpenAI vision API and returns the six spine symbols from left to right.
8. `BookSorter` compares that detected order against the required order `['I', '+', 'X', '-', '[]', 'O']`.
9. If a mismatch is found, `BookSorter` issues shelf hold/release commands to execute one swap at a time using a temporary slot.

The autonomous GPT drone pickup controller still exists in the repo, but it is not started by default in `main.py` right now.

## Active Runtime Files

### Core entrypoint

- `main.py`
   Starts the ESP32 shelf connection, creates the Tello UI, and opens the shelf test window.

### Shelf sorting pipeline

- `tello_control_ui.py`
   Main Tkinter UI for the Tello feed. It reads frames from the drone, displays the live image, and triggers the symbol-detection/sorting pipeline on a timer.

- `Frame_converter.py`
   Defines `FrameToSymbols`. This class sends a camera frame to the OpenAI API, asks for the six spine symbols in left-to-right order, and parses the response into a Python list.

- `Book_Sorter.py`
   Defines `BookSorter`, the current sorting state machine. It tracks expected shelf state, detects the first mismatch, and performs a three-step swap using a temporary slot.

- `shelf_controller.py`
   Serial interface to the ESP32. Sends `hold`, `release`, `hold_all`, and `release_all` commands.

### Manual testing tools

- `test_ui.py`
   Opens a second Tkinter window for manual shelf testing. This lets you trigger slot holds and global hold/release commands while the main UI is running.

- `Book_Sorter_Test.py`
   Pure Python test harness for the sorting algorithm. Uses a fake shelf object and scripted symbol sequences to test simple swaps, repeated frames, deviations, already-correct shelves, and heavy disorder cases.

### Drone control support

- `tello.py`
   Tello communication wrapper.

- `gpt_drone_controller.py`
   Separate GPT-driven drone task controller for the bottle/magnet pickup experiment. Present in the repository, but currently commented out in `main.py`.

## Current Sorting Logic

The live sorting pipeline is now:

`Drone frame -> FrameToSymbols.detect(frame) -> symbol list -> BookSorter.process_frame(symbols) -> ShelfController serial commands`

This is different from the older README description that referred to a YOLO book detector in the active runtime path.

### Symbol detection

`FrameToSymbols` expects exactly six book spine symbols chosen from:

- `I`
- `+`
- `X`
- `-`
- `[]`
- `O`

It sends a JPEG-encoded frame to the OpenAI API and expects a comma-separated response such as:

`I,+,X,-,[],O`

If the API response is malformed, incomplete, or contains an unknown symbol, the frame is ignored.

### BookSorter state machine

`BookSorter` uses:

- Shelf slots `0` through `5` as the main six shelf positions.
- Temporary slot `8` as a holding position during swaps.
- `CORRECT_ORDER = ['I', '+', 'X', '-', '[]', 'O']`

For each new detected symbol list:

1. Repeated identical frames are ignored.
2. The sorter maps the visible symbols onto whichever shelf slots are currently marked as held.
3. If the shelf already matches `CORRECT_ORDER`, it prints `SHELF OK`.
4. Otherwise it finds the first incorrect symbol and starts a three-step swap.

Swap sequence:

1. Move the wrong book from slot `a` to the temporary slot.
2. Move the correct book from slot `b` into slot `a`.
3. Move the temporary-slot book into slot `b`.

The sorter also tracks the expected next frame after each step.

If the observed next frame does not match the expected state, the code treats it as a deviation, prints a deviation message, clears the active swap, and resets hardware state so the shelf can recover cleanly.

## Current UI Behavior

### Main window

`TelloUI` currently:

- Opens a Tkinter window with `START` and `STOP` buttons.
- Starts the drone video stream loop.
- Sends a periodic `command` keepalive to the Tello while streaming.
- Displays the live camera image.
- Runs the symbol-detection/sorting pipeline every 2 seconds when a shelf controller is attached.

### Shelf test window

`TestUI` opens as a separate top-level window attached to the main UI root. It provides:

- Ten individual slot buttons.
- `Hold All`
- `Release All`

This window is useful after rewiring or reordering shelf outputs because it gives a direct manual way to test the ESP32 slot mapping while the main program is running.

## Important Code-Level Notes

- `Book_detector.py` is no longer part of the active startup path.
- `main.py` no longer constructs a `BookDetector` object.
- `tello_control_ui.py` now uses `FrameToSymbols` instead of passing raw frames directly into `BookSorter`.
- `BookSorter` now expects symbol lists, not image frames.
- The GPT autonomous drone task controller is present but currently disabled in `main.py`.
- In `startVideo()`, takeoff is still commented out, so starting the UI does not automatically launch the drone.

## Running The Project

### Main application

```bash
python main.py
```

This requires:

- A reachable ESP32 on the configured serial port.
- A working Tello connection.
- An OpenAI API key available in the environment because `FrameToSymbols` uses the OpenAI client.

### Sorter-only tests

```bash
python Book_Sorter_Test.py
```

This runs the shelf sorting logic without the drone, camera, or ESP32 hardware.

## Repository Map

### Active files

- `main.py`
- `tello_control_ui.py`
- `Frame_converter.py`
- `Book_Sorter.py`
- `Book_Sorter_Test.py`
- `test_ui.py`
- `shelf_controller.py`
- `tello.py`
- `gpt_drone_controller.py`

### Legacy or experimental files still present

- `Book_detector.py`
- `Dataset_generator.py`
- `best.pt`
- `dataset/`
- `book_detection/`

These files may still be useful for older experiments, training work, or archived approaches, but they do not describe the current main execution path as it exists in the code today.

## Known Gaps

- The README you had before described a broader final-report vision for autonomous pickup and placement; the current codebase is more narrowly centered on shelf detection, symbol interpretation, and swap control.
- `FrameToSymbols` depends on an online API call, so the sorting loop now depends on network access and API credentials.
- The test UI labels shelf buttons as slots `7` through `16`, while the shelf controller calls currently send indices `0` through `9`. That mapping should be treated carefully during wiring validation.

## Recommended Next Documentation Updates

If you want the README to go even further, the next useful additions would be:

1. A wiring table that maps physical relay outputs to the slot numbers used in `ShelfController` and `TestUI`.
2. A short state diagram for the `BookSorter` three-step swap process.
3. A section that explicitly separates active code from archived prototype code.
