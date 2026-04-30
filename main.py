import os
import sys

if sys.platform == "win32":
    import msvcrt

    devnull = open(os.devnull, "wb")
    sys.stderr.flush()
    sys.stdout.flush()
    os.dup2(devnull.fileno(), 2)

import tello
from tello_control_ui import TelloUI
from shelf_controller import ShelfController
from Book_detector import BookDetector


def main():
    shelf = ShelfController()
    shelf.connect()

    detector = BookDetector(shelf)
    drone = tello.Tello("", 8889)
    vplayer = TelloUI(drone, "./img/")

    vplayer.root.mainloop()

    shelf.disconnect()


if __name__ == "__main__":
    main()
