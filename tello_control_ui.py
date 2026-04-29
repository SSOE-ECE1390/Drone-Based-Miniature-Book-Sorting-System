from PIL import Image
from PIL import ImageTk
import tkinter as tki
from tkinter import Toplevel, Scale
import threading
import datetime
import cv2
import os
import time
import platform


class TelloUI:

    def __init__(self, tello, outputpath):
        self.tello = tello
        self.outputPath = outputpath
        self.frame = None
        self.thread = None
        self.stopEvent = None
        self.sending_command_thread = None
        self.is_streaming = False

        self.distance = 0.1
        self.degree = 30

        self.quit_waiting_flag = False

        self.root = tki.Tk()
        self.panel = None

        self.btn_start = tki.Button(
            self.root,
            text="START",
            command=self.startVideo,
            bg="green",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        self.btn_start.pack(side="left", fill="both", expand="yes", padx=10, pady=5)

        self.btn_stop = tki.Button(
            self.root,
            text="STOP",
            command=self.stopVideo,
            bg="red",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        self.btn_stop.pack(side="right", fill="both", expand="yes", padx=10, pady=5)

        self.stopEvent = threading.Event()

        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

    def videoLoop(self):
        try:
            time.sleep(0.5)
            # Start keepalive thread
            if self.sending_command_thread is None:
                self.sending_command_thread = threading.Thread(
                    target=self._sendingCommand
                )
                self.sending_command_thread.daemon = True
                self.sending_command_thread.start()

            while not self.stopEvent.is_set() and self.is_streaming:
                system = platform.system()

                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue

                image = Image.fromarray(self.frame)

                if system == "Windows" or system == "Linux":
                    self._updateGUIImage(image)
                else:
                    thread_tmp = threading.Thread(
                        target=self._updateGUIImage, args=(image,)
                    )
                    thread_tmp.start()
                    time.sleep(0.03)
        except RuntimeError as e:
            print("[INFO] caught a RuntimeError")

    def _updateGUIImage(self, image):
        image = ImageTk.PhotoImage(image)
        if self.panel is None:
            self.panel = tki.Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        else:
            self.panel.configure(image=image)
            self.panel.image = image

    def startVideo(self):
        """Start the video stream and takeoff"""
        if not self.is_streaming:
            print("[UI] Starting video stream...")
            self.is_streaming = True
            self.stopEvent.clear()
            self.thread = threading.Thread(target=self.videoLoop, args=())
            self.thread.start()
            print("[DRONE] Taking off...")
            self.tello.takeoff()

    def stopVideo(self):
        """Stop the video stream and land"""
        if self.is_streaming:
            print("[DRONE] Landing...")
            self.tello.land()
            print("[UI] Stopping video stream...")
            self.is_streaming = False
            self.stopEvent.set()
            if self.thread is not None:
                self.thread.join(timeout=2.0)

    def _sendingCommand(self):
        while self.is_streaming and not self.stopEvent.is_set():
            try:
                self.tello.send_command("command")
            except:
                pass
            time.sleep(5)

    def _setQuitWaitingFlag(self):
        self.quit_waiting_flag = True

    def openCmdWindow(self):
        panel = Toplevel(self.root)
        panel.wm_title("Command Panel")

        text0 = tki.Label(
            panel,
            text="This Controller map keyboard inputs to Tello control commands\n"
            "Adjust the trackbar to reset distance and degree parameter",
            font="Helvetica 10 bold",
        )
        text0.pack(side="top")

        text1 = tki.Label(
            panel,
            text="W - Move Tello Up\t\t\tArrow Up - Move Tello Forward\n"
            "S - Move Tello Down\t\t\tArrow Down - Move Tello Backward\n"
            "A - Rotate Tello Counter-Clockwise\tArrow Left - Move Tello Left\n"
            "D - Rotate Tello Clockwise\t\tArrow Right - Move Tello Right",
            justify="left",
        )
        text1.pack(side="top")

        self.btn_landing = tki.Button(
            panel, text="Land", relief="raised", command=self.telloLanding
        )
        self.btn_landing.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_takeoff = tki.Button(
            panel, text="Takeoff", relief="raised", command=self.telloTakeOff
        )
        self.btn_takeoff.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.tmp_f = tki.Frame(panel, width=100, height=2)
        self.tmp_f.bind("<KeyPress-w>", self.on_keypress_w)
        self.tmp_f.bind("<KeyPress-s>", self.on_keypress_s)
        self.tmp_f.bind("<KeyPress-a>", self.on_keypress_a)
        self.tmp_f.bind("<KeyPress-d>", self.on_keypress_d)
        self.tmp_f.bind("<KeyPress-Up>", self.on_keypress_up)
        self.tmp_f.bind("<KeyPress-Down>", self.on_keypress_down)
        self.tmp_f.bind("<KeyPress-Left>", self.on_keypress_left)
        self.tmp_f.bind("<KeyPress-Right>", self.on_keypress_right)
        self.tmp_f.pack(side="bottom")
        self.tmp_f.focus_set()

        self.btn_landing = tki.Button(
            panel, text="Flip", relief="raised", command=self.openFlipWindow
        )
        self.btn_landing.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.distance_bar = Scale(
            panel,
            from_=0.02,
            to=5,
            tickinterval=0.01,
            digits=3,
            label="Distance(m)",
            resolution=0.01,
        )
        self.distance_bar.set(0.2)
        self.distance_bar.pack(side="left")

        self.btn_distance = tki.Button(
            panel,
            text="Reset Distance",
            relief="raised",
            command=self.updateDistancebar,
        )
        self.btn_distance.pack(side="left", fill="both", expand="yes", padx=10, pady=5)

        self.degree_bar = Scale(panel, from_=1, to=360, tickinterval=10, label="Degree")
        self.degree_bar.set(30)
        self.degree_bar.pack(side="right")

        self.btn_distance = tki.Button(
            panel, text="Reset Degree", relief="raised", command=self.updateDegreebar
        )
        self.btn_distance.pack(side="right", fill="both", expand="yes", padx=10, pady=5)

    def openFlipWindow(self):
        panel = Toplevel(self.root)
        panel.wm_title("Gesture Recognition")

        self.btn_flipl = tki.Button(
            panel, text="Flip Left", relief="raised", command=self.telloFlip_l
        )
        self.btn_flipl.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_flipr = tki.Button(
            panel, text="Flip Right", relief="raised", command=self.telloFlip_r
        )
        self.btn_flipr.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_flipf = tki.Button(
            panel, text="Flip Forward", relief="raised", command=self.telloFlip_f
        )
        self.btn_flipf.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_flipb = tki.Button(
            panel, text="Flip Backward", relief="raised", command=self.telloFlip_b
        )
        self.btn_flipb.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

    def takeSnapshot(self):
        ts = datetime.datetime.now()
        filename = "{}.jpg".format(ts.strftime("%Y-%m-%d_%H-%M-%S"))
        p = os.path.sep.join((self.outputPath, filename))
        cv2.imwrite(p, cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR))
        print("[INFO] saved {}".format(filename))

    def pauseVideo(self):
        if self.btn_pause.config("relief")[-1] == "sunken":
            self.btn_pause.config(relief="raised")
            self.tello.video_freeze(False)
        else:
            self.btn_pause.config(relief="sunken")
            self.tello.video_freeze(True)

    def telloTakeOff(self):
        # Keep for compatibility but startVideo should be called instead
        return self.tello.takeoff()

    def telloLanding(self):
        # Keep for compatibility but stopVideo should be called instead
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

    def updateTrackBar(self):
        self.my_tello_hand.setThr(self.hand_thr_bar.get())

    def updateDistancebar(self):
        self.distance = self.distance_bar.get()
        print("reset distance to %.1f" % self.distance)

    def updateDegreebar(self):
        self.degree = self.degree_bar.get()
        print("reset distance to %d" % self.degree)

    def on_keypress_w(self, event):
        print("up %d m" % self.distance)
        self.telloUp(self.distance)

    def on_keypress_s(self, event):
        print("down %d m" % self.distance)
        self.telloDown(self.distance)

    def on_keypress_a(self, event):
        print("ccw %d degree" % self.degree)
        self.tello.rotate_ccw(self.degree)

    def on_keypress_d(self, event):
        print("cw %d m" % self.degree)
        self.tello.rotate_cw(self.degree)

    def on_keypress_up(self, event):
        print("forward %d m" % self.distance)
        self.telloMoveForward(self.distance)

    def on_keypress_down(self, event):
        print("backward %d m" % self.distance)
        self.telloMoveBackward(self.distance)

    def on_keypress_left(self, event):
        print("left %d m" % self.distance)
        self.telloMoveLeft(self.distance)

    def on_keypress_right(self, event):
        print("right %d m" % self.distance)
        self.telloMoveRight(self.distance)

    def on_keypress_enter(self, event):
        if self.frame is not None:
            self.registerFace()
        self.tmp_f.focus_set()

    def onClose(self):
        print("[INFO] closing...")
        self.stopEvent.set()
        del self.tello
        self.root.quit()
