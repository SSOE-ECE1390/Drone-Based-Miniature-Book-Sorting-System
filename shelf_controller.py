from websockets.sync.client import connect
import time


class ShelfController:
    def __init__(self, ip="172.20.10.11", port=81):
        self.ip = ip
        self.port = port
        self.uri = f"ws://{ip}:{port}"
        self.sock = None
        self.connected = False
        self.status = [True] * 10

    def connect(self):
        while not self.connected:
            try:
                # Disable keepalive pings to prevent timeout errors with ESP32
                self.sock = connect(self.uri, ping_interval=None)
                self.connected = True
                print("Connected to ESP32")
            except Exception as e:
                print(f"Connection failed: {e}")
                time.sleep(1)

    def release(self, slot):
        if self.connected:
            self.sock.send(f"release {slot}")

    def hold(self, slot):
        if self.connected:
            self.sock.send(f"hold {slot}")

    def release_all(self):
        if self.connected:
            self.sock.send("release_all")

    def hold_all(self):
        if self.connected:
            self.sock.send("hold_all")

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.connected = False
