import cv2
import numpy as np
import os
import random
import shutil
from pathlib import Path

OUTPUT_DIR = "dataset"
IMAGES_PER_CLASS = 500
IMG_SIZE = 416
CLASSES = ["vertical_line", "horizontal_line", "circle", "square", "cross", "x"]
TRAIN_SPLIT = 0.8

random.seed(42)
np.random.seed(42)


def random_noise(img):
    noise = np.random.normal(0, random.uniform(0, 15), img.shape).astype(np.int16)
    return np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def random_brightness(img):
    factor = random.uniform(0.7, 1.3)
    return np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def augment(img):
    img = random_noise(img)
    img = random_brightness(img)
    if random.random() > 0.5:
        img = cv2.GaussianBlur(img, (3, 3), 0)
    return img


def draw_shape(class_id):
    bg = random.randint(200, 255)
    img = np.ones((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8) * bg

    color = (random.randint(0, 60), random.randint(0, 60), random.randint(0, 60))
    thickness = random.randint(4, 12)
    margin = 80
    cx = random.randint(margin, IMG_SIZE - margin)
    cy = random.randint(margin, IMG_SIZE - margin)
    size = random.randint(40, 120)

    if class_id == 0:  # vertical line
        x = cx
        y1 = max(10, cy - size)
        y2 = min(IMG_SIZE - 10, cy + size)
        cv2.line(img, (x, y1), (x, y2), color, thickness)
        bx, by, bw, bh = x, (y1 + y2) // 2, thickness, y2 - y1

    elif class_id == 1:  # horizontal line
        y = cy
        x1 = max(10, cx - size)
        x2 = min(IMG_SIZE - 10, cx + size)
        cv2.line(img, (x1, y), (x2, y), color, thickness)
        bx, by, bw, bh = (x1 + x2) // 2, y, x2 - x1, thickness

    elif class_id == 2:  # circle
        r = size
        cv2.circle(img, (cx, cy), r, color, thickness)
        bx, by, bw, bh = cx, cy, r * 2, r * 2

    elif class_id == 3:  # square
        half = size
        x1, y1 = cx - half, cy - half
        x2, y2 = cx + half, cy + half
        x1, y1 = max(10, x1), max(10, y1)
        x2, y2 = min(IMG_SIZE - 10, x2), min(IMG_SIZE - 10, y2)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        bx, by, bw, bh = (x1 + x2) // 2, (y1 + y2) // 2, x2 - x1, y2 - y1

    elif class_id == 4:  # cross
        cv2.line(
            img,
            (cx, max(10, cy - size)),
            (cx, min(IMG_SIZE - 10, cy + size)),
            color,
            thickness,
        )
        cv2.line(
            img,
            (max(10, cx - size), cy),
            (min(IMG_SIZE - 10, cx + size), cy),
            color,
            thickness,
        )
        bx, by, bw, bh = cx, cy, size * 2, size * 2

    elif class_id == 5:  # x
        offset = int(size * 0.707)
        cv2.line(
            img,
            (cx - offset, cy - offset),
            (cx + offset, cy + offset),
            color,
            thickness,
        )
        cv2.line(
            img,
            (cx + offset, cy - offset),
            (cx - offset, cy + offset),
            color,
            thickness,
        )
        bx, by, bw, bh = cx, cy, size * 2, size * 2

    # YOLO format: class cx cy w h (normalized)
    label = (
        f"{class_id} "
        f"{bx / IMG_SIZE:.6f} "
        f"{by / IMG_SIZE:.6f} "
        f"{bw / IMG_SIZE:.6f} "
        f"{bh / IMG_SIZE:.6f}"
    )

    return augment(img), label


def generate():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    for split in ["train", "val"]:
        os.makedirs(f"{OUTPUT_DIR}/images/{split}", exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/labels/{split}", exist_ok=True)

    idx = 0
    for class_id, class_name in enumerate(CLASSES):
        print(f"Generating {IMAGES_PER_CLASS} images for: {class_name}")
        for i in range(IMAGES_PER_CLASS):
            img, label = draw_shape(class_id)
            split = "train" if i < int(IMAGES_PER_CLASS * TRAIN_SPLIT) else "val"
            name = f"{class_name}_{i:04d}"
            cv2.imwrite(f"{OUTPUT_DIR}/images/{split}/{name}.jpg", img)
            with open(f"{OUTPUT_DIR}/labels/{split}/{name}.txt", "w") as f:
                f.write(label)
            idx += 1

    yaml = f"""path: {os.path.abspath(OUTPUT_DIR)}
train: images/train
val: images/val
nc: {len(CLASSES)}
names: {CLASSES}
"""
    with open(f"{OUTPUT_DIR}/data.yaml", "w") as f:
        f.write(yaml)

    print(f"\nDone. {idx} images generated.")
    print(f"YAML: {OUTPUT_DIR}/data.yaml")
    print(f"\nTrain with:")
    print(
        f"  yolo train model=yolov8n.pt data={OUTPUT_DIR}/data.yaml epochs=50 imgsz=416"
    )


if __name__ == "__main__":
    generate()
