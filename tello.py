import socket
import threading
import time
import numpy as np
import sys
import os
from ctypes import cdll, c_int

project_dir = os.path.dirname(os.path.abspath(__file__))
ffmpeg_dll_dir = os.path.join(project_dir, "ffmpeg_dlls")

if sys.platform == "win32":
    ffmpeg_dlls = [
        "avcodec-62.dll",
        "avformat-62.dll",
        "avutil-60.dll",
        "swscale-7.dll",
    ]
    for dll_name in ffmpeg_dlls:
        dll_path = os.path.join(ffmpeg_dll_dir, dll_name)
        if os.path.exists(dll_path):
            try:
                cdll.LoadLibrary(dll_path)
            except Exception as e:
                print(f"Warning: Could not preload {dll_name}: {e}")

    try:
        avutil = cdll.LoadLibrary(os.path.join(ffmpeg_dll_dir, "avutil-60.dll"))
        avutil.av_log_set_level(c_int(-8))
    except:
        pass

sys.path.insert(0, ffmpeg_dll_dir)

import libh264decoder


class Tello:
    COMMAND_TIMEOUT = 1.0
    MOVE_DELAY = 3.0

    def __init__(
        self,
        local_ip,
        local_port,
        imperial=False,
        tello_ip="192.168.10.1",
        tello_port=8889,
    ):
        self.abort_flag = False
        self.decoder = libh264decoder.H264Decoder()
        self.command_timeout = self.COMMAND_TIMEOUT
        self.imperial = imperial
        self.response = None
        self.frame = None
        self.is_freeze = False
        self.last_frame = None
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tello_address = (tello_ip, tello_port)
        self.local_video_port = 11111
        self.last_height = 0
        self.socket.bind((local_ip, local_port))

        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.socket.sendto(b"command", self.tello_address)
        self.socket.sendto(b"streamon", self.tello_address)

        self.socket_video.bind((local_ip, self.local_video_port))

        self.receive_video_thread = threading.Thread(target=self._receive_video_thread)
        self.receive_video_thread.daemon = True
        self.receive_video_thread.start()

    def __del__(self):
        self.socket.close()
        self.socket_video.close()

    def read(self):
        if self.is_freeze:
            return self.last_frame
        return self.frame

    def video_freeze(self, is_freeze=True):
        self.is_freeze = is_freeze
        if is_freeze:
            self.last_frame = self.frame

    def _receive_thread(self):
        while True:
            try:
                self.response, ip = self.socket.recvfrom(3000)
            except socket.error as exc:
                if self.connected:
                    print("Disconnected from Tello Drone")
                    self.connected = False

    def _receive_video_thread(self):
        packet_data = b""
        while True:
            try:
                res_string, ip = self.socket_video.recvfrom(2048)
                packet_data += res_string
                if len(res_string) != 1460:
                    for frame in self._h264_decode(packet_data):
                        self.frame = frame
                    packet_data = b""
            except socket.error as exc:
                if self.connected:
                    print("Disconnected from Tello Drone")
                    self.connected = False

    def _h264_decode(self, packet_data):
        res_frame_list = []
        frames = self.decoder.decode(packet_data)
        for framedata in frames:
            (frame, w, h, ls) = framedata
            if frame is not None:
                frame = np.frombuffer(frame, dtype=np.ubyte)
                frame = frame.reshape((h, ls // 3, 3))
                frame = frame[:, :w, :]
                res_frame_list.append(frame)
        return res_frame_list

    def send_command(self, command):
        self.abort_flag = False
        timer = threading.Timer(self.command_timeout, self.set_abort_flag)

        self.socket.sendto(command.encode("utf-8"), self.tello_address)

        timer.start()
        while self.response is None:
            if self.abort_flag:
                break
        timer.cancel()

        if self.response is None:
            response = "none_response"
        else:
            response = self.response.decode("utf-8", errors="ignore")
            print(f"[DRONE] Command '{command}' - Response: {response}")
            if not self.connected:
                self.connected = True
                print("Connected to Tello Drone")

        self.response = None
        return response

    def send_command_without_wait(self, command):
        self.socket.sendto(command.encode("utf-8"), self.tello_address)

    def set_abort_flag(self):
        self.abort_flag = True

    def takeoff(self):
        response = self.send_command("takeoff")
        time.sleep(3)
        return response

    def land(self):
        return self.send_command("land")

    def set_speed(self, speed):
        speed = float(speed)
        if self.imperial:
            speed = int(round(speed * 44.704))
        else:
            speed = int(round(speed * 27.7778))
        return self.send_command("speed %s" % speed)

    def rotate_cw(self, degrees):
        response = self.send_command("cw %s" % degrees)
        time.sleep(self.MOVE_DELAY)
        return response

    def rotate_ccw(self, degrees):
        response = self.send_command("ccw %s" % degrees)
        time.sleep(self.MOVE_DELAY)
        return response

    def flip(self, direction):
        response = self.send_command("flip %s" % direction)
        time.sleep(self.MOVE_DELAY)
        return response

    def get_response(self):
        return self.response

    def get_height(self):
        height = self.send_command("height?")
        height = str(height)
        height = "".join(filter(str.isdigit, height))
        try:
            height = int(height)
            self.last_height = height
        except:
            height = self.last_height
        return height

    def get_battery(self):
        battery = self.send_command("battery?")
        try:
            battery = int(battery)
        except:
            pass
        return battery

    def get_flight_time(self):
        flight_time = self.send_command("time?")
        try:
            flight_time = int(flight_time)
        except:
            pass
        return flight_time

    def get_speed(self):
        speed = self.send_command("speed?")
        try:
            speed = float(speed)
            if self.imperial:
                speed = round((speed / 44.704), 1)
            else:
                speed = round((speed / 27.7778), 1)
        except:
            pass
        return speed

    def move(self, direction, distance):
        distance = float(distance)
        if self.imperial:
            distance = int(round(distance * 30.48))
        else:
            distance = int(round(distance * 100))
        response = self.send_command("%s %s" % (direction, distance))
        time.sleep(self.MOVE_DELAY)
        return response

    def move_backward(self, distance):
        return self.move("back", distance)

    def move_down(self, distance):
        return self.move("down", distance)

    def move_forward(self, distance):
        return self.move("forward", distance)

    def move_left(self, distance):
        return self.move("left", distance)

    def move_right(self, distance):
        return self.move("right", distance)

    def move_up(self, distance):
        return self.move("up", distance)
