import tkinter as tk
from tkinter import ttk


class TestUI:
    def __init__(self, shelf_controller, master=None):
        self.shelf = shelf_controller
        self.root = tk.Toplevel(master) if master else tk.Tk()
        self.root.title("Shelf Test")
        self.root.geometry("500x350")
        self.slot_state = {}  # True = held, False = released
        self.slot_buttons = {}
        self.setup_ui()

    def _toggle_slot(self, slot):
        if self.slot_state.get(slot, True):
            self.shelf.release(slot)
            self.slot_state[slot] = False
            self.slot_buttons[slot].config(text=f"Slot {slot}\n[released]")
        else:
            self.shelf.hold(slot)
            self.slot_state[slot] = True
            self.slot_buttons[slot].config(text=f"Slot {slot}\n[held]")

    def setup_ui(self):
        ttk.Label(self.root, text="Shelf Controller", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=5, pady=10
        )

        for i in range(10):
            slot_num = i + 7
            self.slot_state[i] = True
            btn = ttk.Button(
                self.root,
                text=f"Slot {slot_num}\n[held]",
                command=lambda s=i: self._toggle_slot(s),
            )
            btn.grid(row=i // 5 + 1, column=i % 5, padx=5, pady=5, sticky="ew")
            self.slot_buttons[i] = btn

        ttk.Button(
            self.root,
            text="Hold All",
            command=lambda: self.shelf.hold_all(),
        ).grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="ew")
        ttk.Button(
            self.root,
            text="Release All",
            command=lambda: self.shelf.release_all(),
        ).grid(row=3, column=2, columnspan=2, padx=5, pady=10, sticky="ew")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    from shelf_controller import ShelfController

    shelf = ShelfController()
    shelf.connect()
    ui = TestUI(shelf)
    ui.run()
