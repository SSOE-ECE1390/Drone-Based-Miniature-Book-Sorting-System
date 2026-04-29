import os
import sys

# Suppress FFmpeg/H.264 decoder C-level messages by redirecting stderr
if sys.platform == "win32":
    # Redirect stderr file descriptor to NUL before importing anything
    import msvcrt

    devnull = open(os.devnull, "wb")
    # Flush existing output
    sys.stderr.flush()
    sys.stdout.flush()
    # Redirect OS-level stderr (fd 2) to NUL
    os.dup2(devnull.fileno(), 2)

import tello
from tello_control_ui import TelloUI
from shelf_controller import ShelfController
from Book_detector import BookDetector
from test_ui import TestUI


def main():
    shelf = ShelfController()
    shelf.connect()

    detector = BookDetector(shelf)

    drone = tello.Tello("", 8889)

    vplayer = TelloUI(drone, "./img/")

    # test_ui = TestUI(shelf)

    vplayer.root.mainloop()

    shelf.disconnect()


if __name__ == "__main__":
    main()
