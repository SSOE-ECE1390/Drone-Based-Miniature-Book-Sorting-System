import cv2
import numpy as np
import os

# ─── UPDATE THESE AS YOU ADD MORE VIDEOS ────────────────────────────────────
VIDEO_LABELS = {
    "frame_set_1": ["+", "[]", "O", "-", "I", "X"],
    "frame_set_2": ["[]", "I", "O", "-", "+", "X"],
    "frame_set_3": ["[]", "I", "X", "-", "+", "O"],
    "frame_set_4": ["[]", "I", "X", "-", "+", "O"],
    "frame_set_5": ["[]", "I", "X", "+", "-", "O"],
    "frame_set_6": ["[]", "I", "X", "O", "+", "-"],
}

CLASSES = ["I", "+", "X", "-", "[]", "O"]

INPUT_DIR = "extracted_frames"
OUTPUT_DIR = "annotated_dataset"
TARGET_W = 1280
TARGET_H = 720

# White detection thresholds
WHITE_MIN = 200
MIN_BOX_AREA = 2000
MAX_BOX_AREA = 80000
ASPECT_RATIO_TOLERANCE = 0.6
# ─────────────────────────────────────────────────────────────────────────────


def resize_to_720p(img):
    return cv2.resize(img, (TARGET_W, TARGET_H), interpolation=cv2.INTER_AREA)


def detect_white_boxes(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, WHITE_MIN, 255, cv2.THRESH_BINARY)

    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < MIN_BOX_AREA or area > MAX_BOX_AREA:
            continue
        aspect = min(w, h) / max(w, h)
        if aspect < ASPECT_RATIO_TOLERANCE:
            continue
        boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: b[0])
    return boxes


def to_yolo(x, y, w, h, img_w, img_h):
    cx = (x + w / 2) / img_w
    cy = (y + h / 2) / img_h
    nw = w / img_w
    nh = h / img_h
    return cx, cy, nw, nh


def process_video_set(set_name, labels):
    in_dir = os.path.join(INPUT_DIR, set_name)
    img_out = os.path.join(OUTPUT_DIR, "images", "train", set_name)
    lbl_out = os.path.join(OUTPUT_DIR, "labels", "train", set_name)

    if os.path.isdir(img_out) and any(f.endswith(".jpg") for f in os.listdir(img_out)):
        print(f"{set_name}: already annotated, skipping")
        return

    os.makedirs(img_out, exist_ok=True)
    os.makedirs(lbl_out, exist_ok=True)

    frames = sorted([f for f in os.listdir(in_dir) if f.endswith(".jpg")])
    saved = 0
    skipped = 0

    for fname in frames:
        img = cv2.imread(os.path.join(in_dir, fname))
        if img is None:
            continue

        img = resize_to_720p(img)
        boxes = detect_white_boxes(img)

        if len(boxes) != len(labels):
            skipped += 1
            continue

        out_name = f"{set_name}_{fname}"
        annotation_lines = []

        for i, (x, y, w, h) in enumerate(boxes):
            symbol = labels[i]
            class_id = CLASSES.index(symbol)
            cx, cy, nw, nh = to_yolo(x, y, w, h, TARGET_W, TARGET_H)
            annotation_lines.append(f"{class_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                img, symbol, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )

        cv2.imwrite(os.path.join(img_out, out_name), img)
        lbl_name = out_name.replace(".jpg", ".txt")
        with open(os.path.join(lbl_out, lbl_name), "w") as f:
            f.write("\n".join(annotation_lines))

        saved += 1

    print(f"{set_name}: saved {saved}  skipped {skipped} (wrong box count)")


def write_yaml():
    yaml = f"""path: {os.path.abspath(OUTPUT_DIR)}
train: images/train
val: images/val
nc: {len(CLASSES)}
names: {CLASSES}
"""
    with open(os.path.join(OUTPUT_DIR, "data.yaml"), "w") as f:
        f.write(yaml)


def main():
    os.makedirs(os.path.join(OUTPUT_DIR, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "labels", "val"), exist_ok=True)

    for set_name, labels in VIDEO_LABELS.items():
        if os.path.exists(os.path.join(INPUT_DIR, set_name)):
            process_video_set(set_name, labels)
        else:
            print(f"Skipping {set_name} — folder not found")

    write_yaml()
    print(f"\nDone. Dataset saved to {OUTPUT_DIR}/")
    print("Train with:")
    print(
        f"  yolo train model=yolov8n.pt data={OUTPUT_DIR}/data.yaml epochs=50 imgsz=640"
    )


if __name__ == "__main__":
    main()
