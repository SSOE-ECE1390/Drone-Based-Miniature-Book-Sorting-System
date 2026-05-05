import os
import numpy as np
import time
import cv2
from enum import Enum
from typing import Optional, Tuple

from Frame_converter import FrameToSymbols, CLASS_NAMES


def log_track(msg: str):
    print(msg)
    try:
        with open(
            os.path.join(os.path.dirname(__file__), "tracking_log.txt"), "a"
        ) as f:
            f.write(msg + "\n")
    except Exception:
        pass


# ─── CONSTANTS ───────────────────────────────────────────────────────────────



FRAME_WIDTH = 960
FRAME_HEIGHT = 720
SAFETY_LIMIT = 12

# Lateral correction scale (higher = less aggressive)
KV_SCALE = 10
KH_SCALE = 4
DIST_SCALE = 3

# Area setpoint for stopping (closer to book)
AREA_SETPOINT = 3200
ARRIVAL_THRESHOLD = 3500


# ─── KALMAN FILTER ───────────────────────────────────────────────────────────


class clKalman:
    def __init__(self):
        self.kalman = cv2.KalmanFilter(4, 2)
        self.kalman.measurementMatrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0]], np.float32
        )
        self.kalman.transitionMatrix = np.array(
            [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32
        )
        self.kalman.processNoiseCov = (
            np.array(
                [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], np.float32
            )
            * 0.01
        )
        self.last_measurement = np.array((2, 1), np.float32)
        self.current_measurement = np.array((2, 1), np.float32)
        self.last_prediction = np.zeros((2, 1), np.float32)
        self.current_prediction = np.zeros((2, 1), np.float32)
        self.xi = 0
        self.yi = 0

    def init(self, x, y):
        self.xi = x
        self.yi = y

    def predictAndUpdate(self, x, y, correct=True):
        self.last_prediction = self.current_prediction
        self.last_measurement = self.current_measurement
        self.current_measurement = np.array(
            [[np.float32(x - self.xi)], [np.float32(y - self.yi)]]
        )
        if correct:
            self.kalman.correct(self.current_measurement)
        self.current_prediction = self.kalman.predict()
        self.current_prediction = [
            self.current_prediction[0] + self.xi,
            self.current_prediction[1] + self.yi,
        ]
        return self.last_prediction, self.current_prediction


# ─── HELPERS ─────────────────────────────────────────────────────────────────


def get_bbox_center(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) // 2, (y1 + y2) // 2)


def get_bbox_area(bbox: Tuple[int, int, int, int]) -> float:
    x1, y1, x2, y2 = bbox
    return float((x2 - x1) * (y2 - y1))


def safety_limiter(lr, fb, ud, yaw, limit=SAFETY_LIMIT):
    val = np.array([lr, fb, ud, yaw], dtype=float)
    val[val >= limit] = limit
    val[val <= -limit] = -limit
    return int(val[0]), int(val[1]), int(val[2]), int(val[3])


# ─── TRACKED OBJECT ──────────────────────────────────────────────────────────


class TrackedObject:
    def __init__(
        self, bbox: Tuple[int, int, int, int], center: Tuple[int, int], area: float
    ):
        self.bbox = bbox
        self.center = center
        self.area = area
        self.disappeared = 0

    def get_bbox(self) -> Tuple[int, int, int, int]:
        return self.bbox

    def get_center(self) -> Tuple[int, int]:
        return self.center

    def get_area(self) -> float:
        return self.area

    def mark_disappeared(self) -> None:
        self.disappeared += 1

    def reset_disappeared(self) -> None:
        self.disappeared = 0


# ─── BOOK DETECTOR ───────────────────────────────────────────────────────────


class BookDetector:
    def __init__(self, model_path: str = "best.pt"):
        self.converter = FrameToSymbols(model_path)

    def detect_target(self, frame, target_symbol: str) -> Optional[TrackedObject]:
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        results = self.converter.model(bgr, verbose=False, conf=0.5)[0]

        if results.boxes is None or len(results.boxes) == 0:
            log_track(
                f"[DETECTOR] target {target_symbol} not found in frame (no boxes)"
            )
            return None

        for box in results.boxes:
            cls_id = int(box.cls[0].item())
            symbol = CLASS_NAMES[cls_id]
            if symbol == target_symbol:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                bbox = (x1, y1, x2, y2)
                center = get_bbox_center(bbox)
                area = get_bbox_area(bbox)
                log_track(
                    f"[DETECTOR] target acquired: {target_symbol} at {center} area={area:.0f}"
                )
                return TrackedObject(bbox, center, area)

        log_track(
            f"[DETECTOR] target {target_symbol} not found in frame (boxes present)"
        )
        return None


# ─── DRONE STATE ─────────────────────────────────────────────────────────────


class DroneState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    HOVERING = "hovering"
    TRACKING = "tracking"
    LANDING = "landing"
    EMERGENCY = "emergency"


# ─── DRONE CONTROLLER ────────────────────────────────────────────────────────


class DroneController:
    def __init__(self, tello, on_target_reached=None):
        self.tello = tello
        self.state = DroneState.CONNECTED
        self.tracking_enabled = False
        self.last_command_time = time.time()
        self.command_interval = 0.1

        self.kf = clKalman()
        self.kfarea = clKalman()
        self.initialized = False

        self.cx = FRAME_WIDTH // 2
        self.cy = FRAME_HEIGHT // 2

        self.on_target_reached = on_target_reached

        # Store last command for UI overlay
        self.last_cmd = {"lr": 0, "fb": 0, "ud": 0}

    def enable_tracking(self) -> None:
        if self.state == DroneState.HOVERING:
            print("[TRACKING] enabled")
            self.tracking_enabled = True
            self.initialized = False
            self.state = DroneState.TRACKING

    def disable_tracking(self) -> None:
        print("[TRACKING] disabled")
        self.tracking_enabled = False
        self.initialized = False
        if self.state == DroneState.TRACKING:
            self.state = DroneState.HOVERING
            self.send_rc_control(0, 0, 0, 0)

    def track_target(
        self, target: Optional[TrackedObject], target_symbol: str = ""
    ) -> None:
        if not self.tracking_enabled or self.state != DroneState.TRACKING:
            return

        if target is None or target.disappeared > 0:
            log_track("[TRACK] no target — hovering")
            self.send_rc_control(0, 0, 0, 0)
            return

        cx, cy = target.get_center()
        area = target.get_area()

        if area >= ARRIVAL_THRESHOLD:
            self.send_rc_control(0, 0, 0, 0)
            self.disable_tracking()
            self.last_cmd = {"lr": 0, "fb": 0, "ud": 0}
            if self.on_target_reached and target_symbol:
                self.on_target_reached(
                    f"TARGET REACHED — {target_symbol} located for pickup"
                )
            return

        if not self.initialized:
            self.kf.init(self.cx, self.cy)
            self.kfarea.init(1, area)
            self.initialized = True

        _, cp = self.kf.predictAndUpdate(self.cx, self.cy, True)
        mvx = -int((cp[0].item() - cx) // KV_SCALE)
        mvy = int((cp[1].item() - cy) // KH_SCALE)

        _, ocp = self.kfarea.predictAndUpdate(1, area, True)
        dist = int((ocp[1].item() - AREA_SETPOINT) // DIST_SCALE)

        lr, fb, ud, yaw = safety_limiter(mvx, -dist, mvy, 0)
        self.last_cmd = {"lr": lr, "fb": fb, "ud": ud}

        log_track(
            f"[TRACK] center=({cx},{cy}) area={area:.0f} "
            f"mvx={mvx} mvy={mvy} dist={dist} "
            f"cmd_lr={lr} cmd_fb={fb} cmd_ud={ud}"
        )

        self.send_rc_control(lr, fb, ud, yaw)

    def send_rc_control(self, lr: int, fb: int, ud: int, yaw: int) -> None:
        current_time = time.time()
        if current_time - self.last_command_time < self.command_interval:
            return
        lr = int(np.clip(lr, -100, 100))
        fb = int(np.clip(fb, -100, 100))
        ud = int(np.clip(ud, -100, 100))
        yaw = int(np.clip(yaw, -100, 100))
        self.tello.send_rc_control(lr, fb, ud, yaw)
        self.last_command_time = current_time

    def get_telemetry(self) -> dict:
        try:
            return {
                "battery": self.tello.get_battery(),
                "height": self.tello.get_height(),
                "flight_time": self.tello.get_flight_time(),
                "speed": self.tello.get_speed(),
            }
        except Exception:
            log_track("[TELEMETRY] fetch failed")
            return {}

    def emergency_stop(self) -> None:
        print("[EMERGENCY] stop triggered")
        self.state = DroneState.EMERGENCY
        self.send_rc_control(0, 0, 0, 0)

    def is_flying(self) -> bool:
        return self.state in [DroneState.HOVERING, DroneState.TRACKING]

    def set_state(self, s) -> None:
        self.state = s

    def get_state(self) -> DroneState:
        return self.state

    def is_tracking(self) -> bool:
        return self.tracking_enabled and self.state == DroneState.TRACKING
