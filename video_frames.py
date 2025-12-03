import cv2
import os
from skimage.metrics import structural_similarity as ssim
import numpy as np

# -------- SETTINGS --------
VIDEO_PATH = "input.mp4"
OUT_DIR = "frames"
FPS_EXTRACT = 4  # 2–5 recommended
BLUR_THRESH = 120  # Laplacian variance cutoff
SSIM_THRESH = 0.95  # duplicate cutoff
EXPOSURE_LOW = 40  # too dark
EXPOSURE_HIGH = 220  # too bright
# --------------------------

os.makedirs(OUT_DIR, exist_ok=True)


def too_blurry(frame):
    return cv2.Laplacian(frame, cv2.CV_64F).var() < BLUR_THRESH


def bad_exposure(frame):
    mean = frame.mean()
    return mean < EXPOSURE_LOW or mean > EXPOSURE_HIGH


def is_duplicate(prev, curr):
    g1 = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(curr, cv2.COLOR_BGR2GRAY)
    return ssim(g1, g2) > SSIM_THRESH


cap = cv2.VideoCapture(VIDEO_PATH)
orig_fps = cap.get(cv2.CAP_PROP_FPS)
interval = int(orig_fps // FPS_EXTRACT) if orig_fps > FPS_EXTRACT else 1

count = 0
saved = 0
prev_frame = None

while True:
    ret = cap.grab()
    if not ret:
        break

    # Only decode selected frames
    if count % interval == 0:
        _, frame = cap.retrieve()

        if too_blurry(frame):
            count += 1
            continue

        if bad_exposure(frame):
            count += 1
            continue

        if prev_frame is not None and is_duplicate(prev_frame, frame):
            count += 1
            continue

        out_path = f"{OUT_DIR}/{saved:06d}.jpg"
        cv2.imwrite(out_path, frame)
        prev_frame = frame
        saved += 1

    count += 1

cap.release()
print(f"Saved {saved} frames.")
