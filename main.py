import os
import sys

if sys.platform == "win32":
    import msvcrt

    devnull = open(os.devnull, "wb")
    sys.stderr.flush()
    sys.stdout.flush()
    os.dup2(devnull.fileno(), 2)

from PyQt5.QtWidgets import QApplication
import tello
import threading
from tello_control_ui import TelloUI
from shelf_controller import ShelfController

# from gpt_drone_controller import GPTDroneController


def main():
    shelf = ShelfController()
    shelf.connect()

    app = QApplication(sys.argv)
    drone = tello.Tello("", 8889)
    vplayer = TelloUI(drone, "./img/", shelf)
    drone.on_connected = vplayer.sig_connected.emit
    drone.on_disconnected = vplayer.sig_disconnected.emit

    vplayer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
