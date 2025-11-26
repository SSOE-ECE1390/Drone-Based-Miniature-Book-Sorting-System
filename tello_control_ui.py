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
        self.shelf_reader = None
        self.shelf_reading_active = False

        self.distance = 0.1
        self.degree = 30

        self.quit_waiting_flag = False

        self.root = tki.Tk()
        self.panel = None

        self.btn_snapshot = tki.Button(
            self.root, text="Snapshot!", command=self.takeSnapshot
        )
        self.btn_snapshot.pack(
            side="bottom", fill="both", expand="yes", padx=10, pady=5
        )

        self.btn_shelf_read = tki.Button(
            self.root,
            text="Start Shelf Reading",
            relief="raised",
            command=self.toggleShelfReading,
        )
        self.btn_shelf_read.pack(
            side="bottom", fill="both", expand="yes", padx=10, pady=5
        )

        self.btn_pause = tki.Button(
            self.root, text="Pause", relief="raised", command=self.pauseVideo
        )
        self.btn_pause.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.btn_landing = tki.Button(
            self.root,
            text="Open Command Panel",
            relief="raised",
            command=self.openCmdWindow,
        )
        self.btn_landing.pack(side="bottom", fill="both", expand="yes", padx=10, pady=5)

        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.videoLoop, args=())
        self.thread.start()

        self.root.wm_title("TELLO Controller")
        self.root.wm_protocol("WM_DELETE_WINDOW", self.onClose)

        self.sending_command_thread = threading.Thread(target=self._sendingCommand)

    def videoLoop(self):
        try:
            time.sleep(0.5)
            self.sending_command_thread.start()
            last_process_time = 0

            while not self.stopEvent.is_set():
                system = platform.system()

                self.frame = self.tello.read()
                if self.frame is None or self.frame.size == 0:
                    continue

                current_time = time.time()

                # Check if shelf reading is active
                if (
                    self.shelf_reading_active
                    and hasattr(self, "shelf_reader")
                    and self.shelf_reader is not None
                ):

                    # Process every 5 seconds
                    if (current_time - last_process_time) > 5.0:
                        print(f"\n[PROCESSING FRAME]")
                        self.shelf_reader.read_shelf(self.frame)
                        processed_frame = self.shelf_reader.visualize_results(
                            self.frame
                        )

                        # Save processed frame
                        import datetime

                        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        cv2.imwrite(
                            f"processed_{ts}.jpg",
                            cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR),
                        )
                        print(f"[SAVED] processed_{ts}.jpg")

                        self.frame = processed_frame
                        last_process_time = current_time

                        # Move right after processing
                        self.telloMoveRight(self.distance)

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

    def toggleShelfReading(self):
        if self.shelf_reading_active:
            self.shelf_reading_active = False
            self.btn_shelf_read.config(text="Start Shelf Reading", relief="raised")
            print("[INFO] Shelf reading stopped")
            if hasattr(self, "shelf_reader") and self.shelf_reader is not None:
                report = self.shelf_reader.get_shelf_report()
                print(f"Total books found: {report['call_numbers_read']}")
                print(f"Call numbers: {report['call_number_sequence']}")
        else:
            self.shelf_reading_active = True
            self.shelf_reading_start_time = time.time()
            self.btn_shelf_read.config(text="Stop Shelf Reading", relief="sunken")
            print("[INFO] Shelf reading started - stabilizing for 5 seconds...")

    def _updateGUIImage(self, image):
        image = ImageTk.PhotoImage(image)
        if self.panel is None:
            self.panel = tki.Label(image=image)
            self.panel.image = image
            self.panel.pack(side="left", padx=10, pady=10)
        else:
            self.panel.configure(image=image)
            self.panel.image = image

    def _sendingCommand(self):
        while True:
            self.tello.send_command("command")
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
        return self.tello.takeoff()

    def telloLanding(self):
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
