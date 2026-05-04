import time

CORRECT_ORDER = ["I", "+", "X", "-", "[]", "O"]
SHELF_SLOTS = [0, 1, 2, 3, 4, 5]
TEMP_SLOT = 8


class BookSorter:
    def __init__(self, shelf_controller, log_callback=None):
        self.shelf = shelf_controller
        self.log_callback = log_callback

        self.slot_map = None
        self.hardware_slot_map = {
            0: "hold",
            1: "hold",
            2: "hold",
            3: "hold",
            4: "hold",
            5: "hold",
            6: "released",
            7: "released",
            8: "released",
        }

        for s in SHELF_SLOTS:
            self.shelf.hold(s)
            time.sleep(0.05)
        self.shelf.release(6)
        time.sleep(0.05)
        self.shelf.release(7)
        time.sleep(0.05)
        self.shelf.release(8)

        self.last_frame = None
        self.expected_frame = None
        self.hw_state = {"swap": None}
        self.last_print = None

    def _log(self, msg):
        if msg != self.last_print:
            self.last_print = msg
            if self.log_callback:
                self.log_callback(msg)

    # ------------------------------------------------------------------ #
    # FRAME ENTRY
    # ------------------------------------------------------------------ #
    def process_frame(self, frame):
        if not frame or len(frame) != 6:
            return
        if frame == self.last_frame:
            return

        if self.expected_frame is not None and frame != self.expected_frame:
            self._log(f"DEVIATION: expected {self.expected_frame}, got {frame}")
            return
        self.expected_frame = None

        self.last_frame = frame
        self._update_slot_map(frame)

        if self.hw_state["swap"] is None:
            self._check_and_start_swap()
        else:
            self._continue_swap()

    # ------------------------------------------------------------------ #
    # FRAME TO SLOT MAP
    # ------------------------------------------------------------------ #
    def _update_slot_map(self, frame):
        held_shelf_slots = [
            s for s in SHELF_SLOTS if self.hardware_slot_map[s] == "hold"
        ]
        new_map = {}
        for sym, slot in zip(frame, held_shelf_slots):
            new_map[sym] = slot
        leftover = frame[len(held_shelf_slots) :]
        if leftover and self.hardware_slot_map[TEMP_SLOT] == "hold":
            new_map[leftover[0]] = TEMP_SLOT
        self.slot_map = new_map

    # ------------------------------------------------------------------ #
    # HARDWARE COMMANDS
    # ------------------------------------------------------------------ #
    def _release(self, slot):
        self._log(f"ESP32: release slot {slot}")
        self.shelf.release(slot)
        self.hardware_slot_map[slot] = "released"

    def _hold(self, slot):
        self._log(f"ESP32: hold slot {slot}")
        self.shelf.hold(slot)
        self.hardware_slot_map[slot] = "hold"

    def _reset_hardware_state(self):
        for s in SHELF_SLOTS:
            if self.hardware_slot_map[s] != "hold":
                self._hold(s)
        if self.hardware_slot_map[TEMP_SLOT] != "released":
            self._release(TEMP_SLOT)

    # ------------------------------------------------------------------ #
    # CHECK CORRECTNESS
    # ------------------------------------------------------------------ #
    def _check_and_start_swap(self):
        if all(self.slot_map.get(sym) == i for i, sym in enumerate(CORRECT_ORDER)):
            self._log("SHELF OK")
            return

        a_sym, b_sym, a_slot, b_slot = self._find_first_mismatch()
        if a_slot is None:
            return

        self.hw_state["swap"] = {
            "a_sym": a_sym,
            "b_sym": b_sym,
            "a_slot": a_slot,
            "b_slot": b_slot,
            "step": 1,
        }
        self._log(f"MISMATCH: swapping {a_sym} and {b_sym}")
        self._step_1()

    # ------------------------------------------------------------------ #
    # FIND MISMATCH
    # ------------------------------------------------------------------ #
    def _find_first_mismatch(self):
        for i, correct_sym in enumerate(CORRECT_ORDER):
            current_sym = next(
                (s for s, slot in self.slot_map.items() if slot == i), None
            )
            if current_sym != correct_sym:
                wrong_slot = self.slot_map.get(correct_sym)
                return current_sym, correct_sym, i, wrong_slot
        return None, None, None, None

    # ------------------------------------------------------------------ #
    # CONTINUE SWAP
    # ------------------------------------------------------------------ #
    def _continue_swap(self):
        step = self.hw_state["swap"]["step"]
        self._log(f"SWAP step {step}")
        if step == 1:
            self._step_1()
        elif step == 2:
            self._step_2()
        elif step == 3:
            self._step_3()
        elif step == 4:
            self._step_4()

    # ------------------------------------------------------------------ #
    # STEP 1: A_SLOT contents to TEMP
    # ------------------------------------------------------------------ #
    def _step_1(self):
        a_slot = self.hw_state["swap"]["a_slot"]
        a_sym = self.hw_state["swap"]["a_sym"]

        held_after = [
            s
            for s in SHELF_SLOTS
            if self.hardware_slot_map[s] == "hold" and s != a_slot
        ]
        remaining_syms = sorted(
            [sym for sym, slot in self.slot_map.items() if slot in held_after],
            key=lambda s: self.slot_map[s],
        )
        self.expected_frame = remaining_syms + [a_sym]
        self._log(f"EXPECTED FRAME: {self.expected_frame}")

        self._release(a_slot)
        self._hold(TEMP_SLOT)

        self.hw_state["swap"]["step"] = 2
        self._log(f"MOVE {a_sym} to TEMP")

    # ------------------------------------------------------------------ #
    # STEP 2: B_SLOT contents to A_SLOT
    # ------------------------------------------------------------------ #
    def _step_2(self):
        a_slot = self.hw_state["swap"]["a_slot"]
        b_slot = self.hw_state["swap"]["b_slot"]
        a_sym = self.hw_state["swap"]["a_sym"]
        b_sym = self.hw_state["swap"]["b_sym"]

        post = dict(self.slot_map)
        post[b_sym] = a_slot

        held_after = [
            s
            for s in SHELF_SLOTS
            if self.hardware_slot_map[s] == "hold" and s != b_slot
        ]
        held_after.append(a_slot)
        held_after = sorted(set(held_after))

        shelf_syms = sorted(
            [sym for sym, slot in post.items() if slot in held_after],
            key=lambda s: post[s],
        )
        self.expected_frame = shelf_syms + [a_sym]
        self._log(f"EXPECTED FRAME: {self.expected_frame}")

        self._release(b_slot)
        self._hold(a_slot)

        self.hw_state["swap"]["step"] = 3
        self._log(f"MOVE {b_sym} to slot {a_slot}")

    # ------------------------------------------------------------------ #
    # STEP 3: TEMP contents to B_SLOT
    # ------------------------------------------------------------------ #
    def _step_3(self):
        a_sym = self.hw_state["swap"]["a_sym"]
        b_slot = self.hw_state["swap"]["b_slot"]

        post = dict(self.slot_map)
        post[a_sym] = b_slot

        held_after = [s for s in SHELF_SLOTS if self.hardware_slot_map[s] == "hold"]
        held_after.append(b_slot)
        held_after = sorted(set(held_after))

        shelf_syms = sorted(
            [sym for sym, slot in post.items() if slot in held_after],
            key=lambda s: post[s],
        )
        self.expected_frame = shelf_syms
        self._log(f"EXPECTED FRAME: {self.expected_frame}")

        self._release(TEMP_SLOT)
        self._hold(b_slot)

        self.hw_state["swap"]["step"] = 4
        self._log(f"MOVE {a_sym} to slot {b_slot} — awaiting confirmation")

    # ------------------------------------------------------------------ #
    # STEP 4: CONFIRMATION — camera must see the final frame
    # ------------------------------------------------------------------ #
    def _step_4(self):
        a_sym = self.hw_state["swap"]["a_sym"]
        b_slot = self.hw_state["swap"]["b_slot"]
        self._log(f"SWAP COMPLETE: {a_sym} confirmed in slot {b_slot}")
        self.hw_state["swap"] = None
        self.last_frame = None
