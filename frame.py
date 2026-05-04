import cv2
import os
import sys
from pathlib import Path

BLUR_THRESHOLD = 5
FRAME_INTERVAL = 15
OUTPUT_DIR = "extracted_frames"


def is_blurry(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() < BLUR_THRESHOLD


def extract(video_path):
    name = Path(video_path).stem
    out_dir = os.path.join(OUTPUT_DIR, name)

    if os.path.isdir(out_dir) and any(
        f.lower().endswith(".jpg") for f in os.listdir(out_dir)
    ):
        print(f"{name}: already extracted, skipping")
        return

    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Could not open {video_path}")
        return

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"{name}: {total} frames at {fps:.1f}fps")

    saved = 0
    dropped_blur = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % FRAME_INTERVAL == 0:
            if is_blurry(frame):
                dropped_blur += 1
            else:
                path = os.path.join(out_dir, f"{name}_{saved:04d}.jpg")
                cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                saved += 1
        frame_idx += 1

    cap.release()
    print(f"  saved: {saved}  dropped blurry: {dropped_blur}")


def main():
    video_dir = "videos"
    if not os.path.isdir(video_dir):
        print(f"Directory '{video_dir}' not found")
        return
    videos = sorted(
        [
            os.path.join(video_dir, f)
            for f in os.listdir(video_dir)
            if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
        ]
    )
    if not videos:
        print(f"No video files found in '{video_dir}'")
        return
    for v in videos:
        extract(v)
    print(f"\nDone. Frames saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
