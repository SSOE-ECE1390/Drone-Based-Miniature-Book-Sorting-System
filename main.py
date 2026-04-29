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

    test_ui = TestUI(shelf)

    vplayer.root.mainloop()

    shelf.disconnect()


if __name__ == "__main__":
    main()
