import os
import sys

if sys.platform == "win32":
    import msvcrt

    devnull = open(os.devnull, "wb")
    sys.stderr.flush()
    sys.stdout.flush()
    os.dup2(devnull.fileno(), 2)

import tello
import threading
from tello_control_ui import TelloUI
from shelf_controller import ShelfController
from test_ui import TestUI
from gpt_drone_controller import GPTDroneController


def main():
    shelf = ShelfController()
    shelf.connect()

    drone = tello.Tello("", 8889)
    vplayer = TelloUI(drone, "./img/", shelf)

    test_ui = TestUI(shelf, vplayer.root)

    # gpt_controller = GPTDroneController(drone)
    # gpt_thread = threading.Thread(
    #    target=gpt_controller.run_autonomous_task, args=(120,)
    # )
    # gpt_thread.daemon = True
    # gpt_thread.start()

    vplayer.root.mainloop()

    shelf.disconnect()


if __name__ == "__main__":
    main()
