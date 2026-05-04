import cv2
import numpy as np
from ultralytics import YOLO
import os

VALID_SYMBOLS = ["I", "+", "X", "-", "[]", "O"]
CLASS_NAMES = ["I", "+", "X", "-", "[]", "O"]
MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "best.pt")
CONF_THRESHOLD = 0.5


class FrameToSymbols:
    def __init__(self, model_path=None):
        path = model_path or MODEL_PATH
        self.model = YOLO(path)

    def detect(self, frame):
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        results = self.model(bgr, verbose=False, conf=CONF_THRESHOLD)[0]

        if results.boxes is None or len(results.boxes) == 0:
            return None

        boxes = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            cx = (x1 + x2) / 2
            symbol = CLASS_NAMES[cls_id]
            boxes.append((cx, symbol, conf))

        boxes = sorted(boxes, key=lambda b: b[0])

        if len(boxes) != 6:
            return None

        symbols = [b[1] for b in boxes]

        for sym in symbols:
            if sym not in VALID_SYMBOLS:
                return None
        for sym in VALID_SYMBOLS:
            if symbols.count(sym) > 1:
                return None

        return symbols
