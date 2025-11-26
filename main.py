import os
import sys
import tello
from tello_control_ui import TelloUI
from callnumber_detection import ShelfReader


def main():
    drone = tello.Tello("", 8889)

    # Initialize shelf reader
    reader = ShelfReader(yolo_model_path="best.pt", debug=False)

    vplayer = TelloUI(drone, "./img/")

    # Attach shelf reader to the UI so videoLoop can use it
    vplayer.shelf_reader = reader

    # Start the Tkinter mainloop
    vplayer.root.mainloop()


if __name__ == "__main__":
    main()
