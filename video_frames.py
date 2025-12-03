import cv2
import os
from skimage.metrics import structural_similarity as ssim

# -------- SETTINGS --------
FOLDER = "Drone_Capture"
OUT_DIR = "frames"
FPS_EXTRACT = 4
BLUR_THRESH = 120
SSIM_THRESH = 0.95
EXPOSURE_LOW = 40
EXPOSURE_HIGH = 220
# --------------------------

os.makedirs(OUT_DIR, exist_ok=True)


def too_blurry(f):
    return cv2.Laplacian(f, cv2.CV_64F).var() < BLUR_THRESH


def bad_exposure(f):
    m = f.mean()
    return m < EXPOSURE_LOW or m > EXPOSURE_HIGH


def is_duplicate(a, b):
    g1 = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY)
    return ssim(g1, g2) > SSIM_THRESH


def process_video(path):
    cap = cv2.VideoCapture(path)
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(orig_fps // FPS_EXTRACT) if orig_fps > FPS_EXTRACT else 1

    count = 0
    saved = 0
    prev = None

    while True:
        ret = cap.grab()
        if not ret:
            break

        if count % interval == 0:
            _, frame = cap.retrieve()

            if too_blurry(frame):
                count += 1
                continue
            if bad_exposure(frame):
                count += 1
                continue
            if prev is not None and is_duplicate(prev, frame):
                count += 1
                continue

            name = f"{os.path.splitext(os.path.basename(path))[0]}_{saved:06d}.jpg"
            cv2.imwrite(os.path.join(OUT_DIR, name), frame)
            prev = frame
            saved += 1

        count += 1

    cap.release()


# run on all mp4 files
for file in os.listdir(FOLDER):
    if file.lower().endswith(".mp4"):
        process_video(os.path.join(FOLDER, file))
