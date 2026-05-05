from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
import threading
import datetime
import cv2
import os
import time
import platform
from Book_Sorter import BookSorter
from Frame_converter import FrameToSymbols
from drone_controller import BookDetector, DroneController, DroneState

CORRECT_ORDER = ["I", "+", "X", "-", "[]", "O"]
SYMBOL_CORRECT_COLOR = QColor("#00e676")
SYMBOL_WRONG_COLOR = QColor("#ff1744")
SYMBOL_NEUTRAL_COLOR = QColor("#42a5f5")
SLOT_HELD_BG = QColor("#1a1a2e")
SLOT_RELEASED_BG = QColor("#0d0d0d")
TEMP_COLOR = QColor("#ff9800")
BG_COLOR = "#0a0a0a"
BORDER_COLOR = "#2a2a2a"
TEXT_COLOR = "#e0e0e0"
DIM_COLOR = "#555555"


class SymbolWidget(QWidget):
    def __init__(
        self, symbol=None, correct=None, held=True, is_temp=False, parent=None
    ):
        super().__init__(parent)
        self.symbol = symbol
        self.correct = correct
        self.held = held
        self.is_temp = is_temp
        self.setFixedSize(72, 72)

    def update_state(self, symbol, correct, held):
        self.symbol = symbol
        self.correct = correct
        self.held = held
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = SLOT_HELD_BG if self.held else SLOT_RELEASED_BG
        p.fillRect(self.rect(), bg)
        if self.is_temp:
            border_color = TEMP_COLOR
        elif self.correct is True:
            border_color = SYMBOL_CORRECT_COLOR
        elif self.correct is False:
            border_color = SYMBOL_WRONG_COLOR
        else:
            border_color = SYMBOL_NEUTRAL_COLOR
        p.setPen(QPen(border_color, 2))
        p.drawRect(1, 1, self.width() - 2, self.height() - 2)
        if self.symbol is None:
            p.end()
            return
        sym_pen = QPen(border_color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(sym_pen)
        cx, cy, r = self.width() // 2, self.height() // 2, 18
        if self.symbol == "I":
            p.drawLine(cx, cy - r, cx, cy + r)
            p.drawLine(cx - 8, cy - r, cx + 8, cy - r)
            p.drawLine(cx - 8, cy + r, cx + 8, cy + r)
        elif self.symbol == "+":
            p.drawLine(cx - r, cy, cx + r, cy)
            p.drawLine(cx, cy - r, cx, cy + r)
        elif self.symbol == "X":
            p.drawLine(cx - r, cy - r, cx + r, cy + r)
            p.drawLine(cx + r, cy - r, cx - r, cy + r)
        elif self.symbol == "-":
            p.drawLine(cx - r, cy, cx + r, cy)
        elif self.symbol == "[]":
            p.drawRect(cx - r, cy - r, r * 2, r * 2)
        elif self.symbol == "O":
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        p.end()


class ShelfWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slot_widgets = []
        self.temp_widget = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)
        shelf_label = QLabel("SHELF")
        shelf_label.setFont(QFont("Consolas", 8))
        shelf_label.setStyleSheet(f"color: {DIM_COLOR};")
        layout.addWidget(shelf_label)
        slots_row = QHBoxLayout()
        slots_row.setSpacing(6)
        for i in range(6):
            w = SymbolWidget()
            self.slot_widgets.append(w)
            slots_row.addWidget(w)
        layout.addLayout(slots_row)
        temp_row = QHBoxLayout()
        temp_label = QLabel("TEMP")
        temp_label.setFont(QFont("Consolas", 8))
        temp_label.setStyleSheet(f"color: {DIM_COLOR};")
        self.temp_widget = SymbolWidget(is_temp=True)
        temp_row.addWidget(temp_label)
        temp_row.addWidget(self.temp_widget)
        temp_row.addStretch()
        layout.addLayout(temp_row)

    def update_shelf(self, slot_map, hardware_slot_map):
        if slot_map is None:
            return
        for i, w in enumerate(self.slot_widgets):
            sym = next((s for s, slot in slot_map.items() if slot == i), None)
            correct = (sym == CORRECT_ORDER[i]) if sym is not None else None
            held = hardware_slot_map.get(i, "hold") == "hold"
            w.update_state(sym, correct, held)
        temp_sym = next((s for s, slot in slot_map.items() if slot == 8), None)
        held_temp = hardware_slot_map.get(8, "released") == "hold"
        self.temp_widget.update_state(temp_sym, None, held_temp)


class HardwareSlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slot_labels = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        hw_label = QLabel("HARDWARE SLOTS")
        hw_label.setFont(QFont("Consolas", 8))
        hw_label.setStyleSheet(f"color: {DIM_COLOR};")
        layout.addWidget(hw_label)

        slots_row = QHBoxLayout()
        slots_row.setSpacing(8)
        for i in range(9):
            col = QVBoxLayout()
            col.setSpacing(3)
            num_label = QLabel(str(i))
            num_label.setFont(QFont("Consolas", 9))
            num_label.setStyleSheet(f"color: {DIM_COLOR};")
            num_label.setAlignment(Qt.AlignCenter)
            default_held = i <= 5
            state_label = QLabel("HELD" if default_held else "RELEASED")
            state_label.setFont(QFont("Consolas", 9, QFont.Bold))
            state_label.setAlignment(Qt.AlignCenter)
            state_label.setFixedWidth(72)
            state_label.setStyleSheet(
                f"color: {SYMBOL_CORRECT_COLOR.name()};"
                if default_held
                else f"color: {SYMBOL_WRONG_COLOR.name()};"
            )
            self.slot_labels[i] = state_label
            col.addWidget(num_label)
            col.addWidget(state_label)
            slots_row.addLayout(col)
        layout.addLayout(slots_row)

    def update_hardware(self, hardware_slot_map):
        for slot, label in self.slot_labels.items():
            state = hardware_slot_map.get(slot, "released")
            if state == "hold":
                label.setText("HELD")
                label.setStyleSheet(f"color: {SYMBOL_CORRECT_COLOR.name()};")
            else:
                label.setText("RELEASED")
                label.setStyleSheet(f"color: {SYMBOL_WRONG_COLOR.name()};")


class TelemetryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self.setFixedHeight(120)

    def update_telemetry(self, data: dict):
        self._data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(BG_COLOR))
        W = self.width()

        # section label
        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor(DIM_COLOR))
        p.drawText(0, 0, W, 14, Qt.AlignLeft | Qt.AlignVCenter, "TELEMETRY")

        # battery bar
        bat = self._data.get("battery")
        bar_y, bar_h = 16, 18
        p.setPen(QColor(BORDER_COLOR))
        p.drawRect(0, bar_y, W - 1, bar_h)
        if bat is not None:
            fill_w = max(1, int((bat / 100.0) * (W - 3)))
            if bat > 50:
                bat_color = SYMBOL_CORRECT_COLOR
            elif bat > 20:
                bat_color = QColor("#ffeb3b")
            else:
                bat_color = SYMBOL_WRONG_COLOR
            p.fillRect(1, bar_y + 1, fill_w, bar_h - 2, bat_color)
            p.setFont(QFont("Consolas", 8, QFont.Bold))
            p.setPen(QColor("#000000"))
            p.drawText(1, bar_y + 1, fill_w, bar_h - 2, Qt.AlignCenter, f"BAT  {bat}%")
        else:
            p.setFont(QFont("Consolas", 8))
            p.setPen(QColor(DIM_COLOR))
            p.drawText(0, bar_y, W, bar_h, Qt.AlignCenter, "BAT  —")

        # metric boxes with clarified units
        # Height: convert cm to meters for display
        height_cm = self._data.get("height")
        height_m = None
        if height_cm is not None:
            try:
                height_m = float(height_cm) / 100.0
            except Exception:
                height_m = None
        # Time: show as seconds (s)
        flight_time = self._data.get("flight_time")
        # Speed: keep as cm/s
        speed = self._data.get("speed")

        metrics = [
            ("ALT", height_m, "m"),
            ("TIME", flight_time, "s"),
            ("SPEED", speed, "cm/s"),
        ]
        n = len(metrics)
        cell_w = (W - (n - 1) * 4) // n
        box_y = 40
        box_h = self.height() - box_y - 2
        for i, (label, val, unit) in enumerate(metrics):
            x = i * (cell_w + 4)
            p.setPen(QColor(BORDER_COLOR))
            p.drawRect(x, box_y, cell_w, box_h)
            p.setFont(QFont("Consolas", 7))
            p.setPen(QColor(DIM_COLOR))
            p.drawText(
                x + 2, box_y + 1, cell_w - 4, 12, Qt.AlignLeft | Qt.AlignVCenter, label
            )
            p.setFont(QFont("Consolas", 11, QFont.Bold))
            p.setPen(QColor(TEXT_COLOR))
            if val is None:
                val_str = "—"
            elif label == "ALT":
                val_str = f"{val:.2f}" if isinstance(val, float) else str(val)
            else:
                val_str = str(val)
            p.drawText(x, box_y + 14, cell_w, box_h - 28, Qt.AlignCenter, val_str)
            p.setFont(QFont("Consolas", 7))
            p.setPen(QColor(DIM_COLOR))
            p.drawText(
                x + 2,
                box_y + box_h - 14,
                cell_w - 4,
                12,
                Qt.AlignRight | Qt.AlignVCenter,
                unit,
            )
        p.end()


class TelloUI(QMainWindow):
    sig_connected = pyqtSignal()
    sig_disconnected = pyqtSignal()
    sig_frame = pyqtSignal(object)
    sig_shelf = pyqtSignal()
    sig_telemetry = pyqtSignal(dict)

    def __init__(self, tello, outputpath, shelf=None):
        super().__init__()
        self.tello = tello
        self.outputPath = outputpath
        self.frame = None
        self.thread = None
        self.stopEvent = None
        self.sending_command_thread = None
        self.telemetry_thread = None
        self.is_streaming = False
        self.is_paused = False
        self.degree = 30

        self.quit_waiting_flag = False
        self.last_sort_time = 0
        self.sort_in_progress = False
        self.book_sorter = (
            BookSorter(shelf, log_callback=self.set_log) if shelf else None
        )
        self.symbol_detector = FrameToSymbols()
        self.book_detector = BookDetector()
        self.drone_controller = DroneController(
            self.tello, on_target_reached=self.set_log
        )
        self.drone_controller.set_state(DroneState.HOVERING)

        self.stopEvent = threading.Event()

        self.sig_connected.connect(self._on_connected)
        self.sig_disconnected.connect(self._on_disconnected)
        self.sig_frame.connect(self._on_frame)
        self.sig_shelf.connect(self._refresh_shelf)
        self.sig_telemetry.connect(self._refresh_telemetry)

        self._build_ui()
        self._apply_styles()
        self.setWindowTitle("TELLO Controller")

    def _build_ui(self):
        self.setMinimumSize(1400, 750)
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setSpacing(12)
        root_layout.setContentsMargins(12, 12, 12, 12)

        left = QVBoxLayout()
        left.setSpacing(8)
        self.panel = QLabel()
        self.panel.setFixedSize(640, 480)
        self.panel.setAlignment(Qt.AlignCenter)
        self.panel.setStyleSheet(f"background: #000; border: 1px solid {BORDER_COLOR};")
        left.addWidget(self.panel)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("START")
        self.btn_stop = QPushButton("STOP")
        self.btn_start.setFixedHeight(44)
        self.btn_stop.setFixedHeight(44)
        self.btn_start.clicked.connect(self.startVideo)
        self.btn_stop.clicked.connect(self.stopVideo)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        self.btn_pause = QPushButton("PAUSE")
        self.btn_pause.setFixedHeight(44)
        self.btn_pause.clicked.connect(self.pauseVideo)
        btn_row.addWidget(self.btn_pause)
        left.addLayout(btn_row)

        flight_row = QHBoxLayout()
        self.btn_takeoff = QPushButton("TAKEOFF")
        self.btn_land = QPushButton("LAND")
        self.btn_takeoff.setFixedHeight(44)
        self.btn_land.setFixedHeight(44)
        self.btn_takeoff.setObjectName("btn_takeoff")
        self.btn_land.setObjectName("btn_land")
        self.btn_takeoff.clicked.connect(self.telloTakeOff)
        self.btn_land.clicked.connect(self.telloLanding)
        flight_row.addWidget(self.btn_takeoff)
        flight_row.addWidget(self.btn_land)
        left.addLayout(flight_row)

        root_layout.addLayout(left)

        right = QVBoxLayout()
        right.setSpacing(10)

        status_row = QHBoxLayout()
        self.conn_indicator = QLabel("●")
        self.conn_indicator.setFont(QFont("Consolas", 14))
        self.conn_indicator.setStyleSheet(f"color: {DIM_COLOR};")
        self.conn_label = QLabel("WAITING")
        self.conn_label.setFont(QFont("Consolas", 11))
        self.conn_label.setStyleSheet(f"color: {DIM_COLOR};")
        status_row.addWidget(self.conn_indicator)
        status_row.addWidget(self.conn_label)
        status_row.addStretch()
        right.addLayout(status_row)

        right.addWidget(self._divider())

        self.telemetry_widget = TelemetryWidget()
        right.addWidget(self.telemetry_widget)

        right.addWidget(self._divider())

        ref_label = QLabel("CORRECT ORDER")
        ref_label.setFont(QFont("Consolas", 8))
        ref_label.setStyleSheet(f"color: {DIM_COLOR};")
        right.addWidget(ref_label)

        ref_row = QHBoxLayout()
        ref_row.setSpacing(6)
        for sym in CORRECT_ORDER:
            w = SymbolWidget(symbol=sym, correct=True, held=True)
            w.setFixedSize(52, 52)
            ref_row.addWidget(w)
        ref_row.addStretch()
        right.addLayout(ref_row)

        right.addWidget(self._divider())

        self.shelf_widget = ShelfWidget()
        right.addWidget(self.shelf_widget)

        right.addWidget(self._divider())
        self.hw_slot_widget = HardwareSlotWidget()
        right.addWidget(self.hw_slot_widget)

        right.addWidget(self._divider())

        self.swap_label = QLabel("no active swap")
        self.swap_label.setFont(QFont("Consolas", 10))
        self.swap_label.setStyleSheet(f"color: {DIM_COLOR};")
        right.addWidget(self.swap_label)

        right.addWidget(self._divider())

        log_label = QLabel("LAST ACTION")
        log_label.setFont(QFont("Consolas", 8))
        log_label.setStyleSheet(f"color: {DIM_COLOR};")
        right.addWidget(log_label)

        self.log_display = QLabel("—")
        self.log_display.setFont(QFont("Consolas", 10))
        self.log_display.setStyleSheet(f"color: {TEXT_COLOR};")
        self.log_display.setWordWrap(True)
        right.addWidget(self.log_display)

        right.addStretch()
        root_layout.addLayout(right)

    def _divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {BORDER_COLOR};")
        return line

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {BG_COLOR};
                color: {TEXT_COLOR};
                font-family: Consolas;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: {TEXT_COLOR};
                border: 1px solid {BORDER_COLOR};
                font-family: Consolas;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background-color: #252525;
                border-color: #555;
            }}
            QPushButton#btn_start {{
                border-left: 3px solid {SYMBOL_CORRECT_COLOR.name()};
            }}
            QPushButton#btn_stop {{
                border-left: 3px solid {SYMBOL_WRONG_COLOR.name()};
            }}
            QPushButton#btn_takeoff {{
                border-left: 3px solid {SYMBOL_NEUTRAL_COLOR.name()};
            }}
            QPushButton#btn_land {{
                border-left: 3px solid {TEMP_COLOR.name()};
            }}
        """)
        self.btn_start.setObjectName("btn_start")
        self.btn_stop.setObjectName("btn_stop")

    def _on_connected(self):
        self.conn_indicator.setStyleSheet(f"color: {SYMBOL_CORRECT_COLOR.name()};")
        self.conn_label.setText("CONNECTED")
        self.conn_label.setStyleSheet(f"color: {SYMBOL_CORRECT_COLOR.name()};")

    def _on_disconnected(self):
        self.conn_indicator.setStyleSheet(f"color: {SYMBOL_WRONG_COLOR.name()};")
        self.conn_label.setText("RECONNECTING...")
        self.conn_label.setStyleSheet(f"color: #ffeb3b;")
        if self.is_streaming:
            self.stopVideo()

    def _on_frame(self, pixmap):
        self.panel.setPixmap(pixmap)

    def set_log(self, msg):
        self.log_display.setText(msg)

    def _refresh_shelf(self):
        if self.book_sorter is None:
            return
        self.shelf_widget.update_shelf(
            self.book_sorter.slot_map, self.book_sorter.hardware_slot_map
        )
        self.hw_slot_widget.update_hardware(self.book_sorter.hardware_slot_map)
        swap = self.book_sorter.hw_state.get("swap")
        if swap:
            self.swap_label.setStyleSheet(f"color: {TEMP_COLOR.name()};")
            self.swap_label.setText(
                f"⟳  slot {swap['a_slot']} ↔ slot {swap['b_slot']}  ({swap['a_sym']} ↔ {swap['b_sym']})"
            )
        else:
            self.swap_label.setStyleSheet(f"color: {DIM_COLOR};")
            self.swap_label.setText("no active swap")

    def _refresh_telemetry(self, data: dict):
        self.telemetry_widget.update_telemetry(data)

    def _telemetryLoop(self):
        while self.is_streaming and not self.stopEvent.is_set():
            data = {
                "battery": self.tello.battery,
                "height": self.tello.height,
                "flight_time": self.tello.flight_time,
                "speed": self.tello.speed,
            }
            self.sig_telemetry.emit(data)
            self.stopEvent.wait(2.0)

    def videoLoop(self):
        try:
            time.sleep(0.5)
            if self.sending_command_thread is None:
                self.sending_command_thread = threading.Thread(
                    target=self._sendingCommand
                )
                self.sending_command_thread.daemon = True
                self.sending_command_thread.start()

            while not self.stopEvent.is_set() and self.is_streaming:
                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue

                if not self.is_paused:
                    if (
                        time.time() - self.last_sort_time >= 1.0
                        and not self.sort_in_progress
                        and self.book_sorter
                    ):
                        self.last_sort_time = time.time()
                        self.sort_in_progress = True

                        def _detect_and_sort(frame):
                            try:
                                symbols = self.symbol_detector.detect(frame)
                                if symbols:
                                    self.book_sorter.process_frame(symbols)
                                    self.sig_shelf.emit()
                            finally:
                                self.sort_in_progress = False

                        t = threading.Thread(
                            target=_detect_and_sort,
                            args=(self.frame.copy(),),
                        )
                        t.daemon = True
                        t.start()

                    target_symbol = (
                        self.book_sorter.hw_state.get("swap", {})
                        if self.book_sorter
                        else {}
                    )
                    target = None
                    bbox = None
                    center = None
                    if target_symbol:
                        a_sym = target_symbol.get("a_sym")
                        if a_sym:
                            target = self.book_detector.detect_target(
                                self.tello.frame, a_sym
                            )
                            self.drone_controller.track_target(target, a_sym)
                            if target is not None:
                                bbox = target.get_bbox()
                                center = target.get_center()

                    frame_copy = self.frame.copy()

                    # Draw bounding box and center if target found
                    if bbox is not None and center is not None:
                        x1, y1, x2, y2 = bbox
                        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.circle(frame_copy, center, 8, (0, 0, 255), -1)
                        # Overlay last command in the top-left corner of the bounding box
                        cmd = (
                            self.drone_controller.last_cmd
                            if hasattr(self.drone_controller, "last_cmd")
                            else {"lr": 0, "fb": 0, "ud": 0}
                        )
                        cmd_text = (
                            f"LR:{cmd['lr']:+d}  FB:{cmd['fb']:+d}  UD:{cmd['ud']:+d}"
                        )
                        # Offset a bit inside the box
                        text_x = x1 + 4
                        text_y = y1 + 18
                        cv2.putText(
                            frame_copy,
                            cmd_text,
                            (text_x, text_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (255, 255, 0),
                            2,
                            cv2.LINE_AA,
                        )

                    # Overlay last command in bottom left (always)
                    cmd = (
                        self.drone_controller.last_cmd
                        if hasattr(self.drone_controller, "last_cmd")
                        else {"lr": 0, "fb": 0, "ud": 0}
                    )
                    cv2.putText(
                        frame_copy,
                        f"LR:{cmd['lr']:+d}  FB:{cmd['fb']:+d}  UD:{cmd['ud']:+d}",
                        (10, frame_copy.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        1,
                        cv2.LINE_AA,
                    )

                    h, w, ch = frame_copy.shape
                    qt_image = QImage(
                        frame_copy.data, w, h, ch * w, QImage.Format_RGB888
                    )
                    pixmap = QPixmap.fromImage(qt_image).scaled(
                        720, 540, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.sig_frame.emit(pixmap)

        except RuntimeError as e:
            print("[INFO] caught a RuntimeError")

    def startVideo(self):
        if not self.is_streaming:
            print("[UI] Starting video stream...")
            print("[DRONE] Connected to DJI Tello")
            self.tello.send_command_without_wait("streamon")
            self.is_streaming = True
            self.stopEvent.clear()
            self.thread = threading.Thread(target=self.videoLoop, args=())
            self.thread.start()
            self.telemetry_thread = threading.Thread(
                target=self._telemetryLoop, daemon=True
            )
            self.telemetry_thread.start()

    def stopVideo(self):
        if self.is_streaming:
            print("[UI] Stopping video stream...")
            self.is_streaming = False
            self.stopEvent.set()
            if self.thread is not None:
                self.thread.join(timeout=2.0)
                self.thread = None
            if self.sending_command_thread is not None:
                self.sending_command_thread.join(timeout=2.0)
                self.sending_command_thread = None
            if self.telemetry_thread is not None:
                self.telemetry_thread.join(timeout=2.0)
                self.telemetry_thread = None

    def pauseVideo(self):
        self.is_paused = not self.is_paused
        self.btn_pause.setText("RESUME" if self.is_paused else "PAUSE")

    def _sendingCommand(self):
        while self.is_streaming and not self.stopEvent.is_set():
            try:
                self.tello.send_command("command")
            except:
                pass
            try:
                self.tello.get_battery()
                self.tello.get_height()
                self.tello.get_flight_time()
                self.tello.get_speed()
            except:
                pass
            time.sleep(5)

    def _setQuitWaitingFlag(self):
        self.quit_waiting_flag = True

    def telloTakeOff(self):
        self.drone_controller.enable_tracking()
        return self.tello.takeoff()

    def telloLanding(self):
        self.drone_controller.disable_tracking()
        return self.tello.land()

    def telloFlip_l(self):
        return self.tello.flip("l")

    def telloFlip_r(self):
        return self.tello.flip("r")

    def telloFlip_f(self):
        return self.tello.flip("f")

    def telloFlip_b(self):
        return self.tello.flip("b")

    def telloCW(self, degree):
        return self.tello.rotate_cw(degree)

    def telloCCW(self, degree):
        return self.tello.rotate_ccw(degree)

    def telloMoveForward(self, distance):
        return self.tello.move_forward(distance)

    def telloMoveBackward(self, distance):
        return self.tello.move_backward(distance)

    def telloMoveLeft(self, distance):
        return self.tello.move_left(distance)

    def telloMoveRight(self, distance):
        return self.tello.move_right(distance)

    def telloUp(self, dist):
        return self.tello.move_up(dist)

    def telloDown(self, dist):
        return self.tello.move_down(dist)

    def onClose(self):
        print("[INFO] closing...")
        self.stopEvent.set()
        del self.tello
        self.close()
