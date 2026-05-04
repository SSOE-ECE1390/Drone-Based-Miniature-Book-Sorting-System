import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "ultralytics", "-q"])

from google.colab import drive
from ultralytics import YOLO
import zipfile
import shutil
import torch
import os

# ─── UPDATE THESE ────────────────────────────────────────────────────────────
DRIVE_DATASET_ZIP = "/content/drive/MyDrive/annotated_dataset.zip"
DRIVE_OUTPUT_DIR = "/content/drive/MyDrive/yolo_shelf_model"
DATASET_DIR = "/content/annotated_dataset"
DATA_YAML = f"{DATASET_DIR}/data.yaml"
MODEL = "yolov8n.pt"
EPOCHS = 50
IMG_SIZE = 640
PROJECT = "/content/runs"
RUN_NAME = "shelf_symbols"
# ─────────────────────────────────────────────────────────────────────────────


def mount_drive():
    drive.mount("/content/drive")
    print("Drive mounted")


def extract_dataset():
    with zipfile.ZipFile(DRIVE_DATASET_ZIP, "r") as z:
        z.extractall("/content")
    total = sum(len(f) for _, _, f in os.walk(DATASET_DIR))
    print(f"Dataset extracted to {DATASET_DIR} — {total} files")


def fix_yaml():
    yaml = f"""path: {DATASET_DIR}
train: images/train
val: images/val
nc: 6
names: ["I", "+", "X", "-", "[]", "O"]
"""
    with open(DATA_YAML, "w") as f:
        f.write(yaml)
    print("data.yaml updated with Colab paths")


def check_gpu():
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")


def train():
    model = YOLO(MODEL)
    model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        project=PROJECT,
        name=RUN_NAME,
        patience=15,
        batch=16,
        workers=2,
        verbose=True,
    )


def validate():
    best_weights = f"{PROJECT}/{RUN_NAME}/weights/best.pt"
    model = YOLO(best_weights)
    metrics = model.val(data=DATA_YAML)
    print(f"mAP50:    {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    return best_weights


def save_to_drive(best_weights):
    os.makedirs(DRIVE_OUTPUT_DIR, exist_ok=True)
    shutil.copy(best_weights, f"{DRIVE_OUTPUT_DIR}/best.pt")
    shutil.copy(f"{PROJECT}/{RUN_NAME}/results.png", f"{DRIVE_OUTPUT_DIR}/results.png")
    print(f"Model saved to {DRIVE_OUTPUT_DIR}")


def main():
    mount_drive()
    extract_dataset()
    fix_yaml()
    check_gpu()
    train()
    best_weights = validate()
    save_to_drive(best_weights)


if __name__ == "__main__":
    main()
