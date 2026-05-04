import serial
import time


class ShelfController:
    def __init__(self, port="COM16", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False
        self.status = [True] * 10

    def connect(self):
        while not self.connected:
            try:
                self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
                time.sleep(2)  # Wait for ESP32 to initialize after serial connection
                self.connected = True
                print(f"Connected to ESP32 on {self.port}")
            except Exception as e:
                print(f"Connection failed: {e}")
                time.sleep(1)

    def release(self, slot):
        if self.connected:
            try:
                self.serial.write(f"release {slot}\n".encode())
            except Exception as e:
                print(f"Error sending command: {e}")

    def hold(self, slot):
        if self.connected:
            try:
                self.serial.write(f"hold {slot}\n".encode())
            except Exception as e:
                print(f"Error sending command: {e}")

    def release_all(self):
        if self.connected:
            try:
                self.serial.write("release_all\n".encode())
            except Exception as e:
                print(f"Error sending command: {e}")

    def hold_all(self):
        if self.connected:
            try:
                self.serial.write("hold_all\n".encode())
            except Exception as e:
                print(f"Error sending command: {e}")

    def disconnect(self):
        if self.serial:
            self.serial.close()
            self.connected = False
