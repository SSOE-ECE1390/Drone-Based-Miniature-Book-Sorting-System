# test_booksorter.py

from Book_Sorter import BookSorter, CORRECT_ORDER


class FakeShelf:
    def release(self, slot):
        print(f"[ESP32] RELEASE {slot}")

    def hold(self, slot):
        print(f"[ESP32] HOLD {slot}")


def run_test(name, frames):
    print(f"\n===== {name} =====")

    sorter = BookSorter(FakeShelf())

    for i, frame in enumerate(frames):
        print(f"\n[FRAME {i}] {frame}")
        sorter.process_frame(frame)

    print(f"\n===== END {name} =====\n")


# -------------------------
# TEST 1: simple swap
# -------------------------
test1 = [
    ["X", "+", "I", "-", "[]", "O"],
    ["+", "I", "-", "[]", "O", "X"],
    ["I", "+", "-", "[]", "O", "X"],
    CORRECT_ORDER,
]


# -------------------------
# TEST 2: repeated frames (no change spam)
# -------------------------
test2 = [
    ["X", "+", "I", "-", "[]", "O"],
    ["X", "+", "I", "-", "[]", "O"],
    ["X", "+", "I", "-", "[]", "O"],
    ["I", "+", "X", "-", "[]", "O"],
]


# -------------------------
# TEST 3: moderately disorganized (multiple swaps)
# -------------------------
test3 = [
    ["X", "O", "I", "-", "[]", "+"],
    ["I", "O", "X", "-", "[]", "+"],
    ["I", "+", "X", "-", "[]", "O"],
    ["I", "+", "X", "-", "[]", "O"],
    CORRECT_ORDER,
]


# -------------------------
# TEST 4: repeated frames + delayed movement
# -------------------------
test4 = [
    ["X", "+", "I", "-", "[]", "O"],
    ["X", "+", "I", "-", "[]", "O"],
    ["X", "+", "I", "-", "[]", "O"],
    ["I", "+", "X", "-", "[]", "O"],
    ["I", "+", "X", "-", "[]", "O"],
]


# -------------------------
# TEST 5: heavy disorder (multi-pass sorting)
# -------------------------
test5 = [
    ["O", "X", "-", "+", "[]", "I"],
    ["I", "X", "-", "+", "[]", "O"],
    ["I", "+", "-", "X", "[]", "O"],
    ["I", "+", "X", "-", "[]", "O"],
    ["I", "+", "X", "-", "O", "[]"],
    CORRECT_ORDER,
]


# -------------------------
# TEST 6: desync / chaotic reorder (many swaps needed)
# -------------------------
test6 = [
    ["+", "O", "X", "[]", "-", "I"],
    ["I", "O", "X", "[]", "-", "+"],
    ["I", "+", "X", "[]", "-", "O"],
    ["I", "+", "X", "-", "[]", "O"],
    ["I", "+", "X", "-", "O", "[]"],
    ["I", "+", "X", "-", "[]", "O"],
    CORRECT_ORDER,
]


if __name__ == "__main__":
    run_test("TEST 1 - SIMPLE SWAP", test1)
    run_test("TEST 2 - REPEATED FRAMES", test2)
    run_test("TEST 3 - MULTI SWAP", test3)
    run_test("TEST 4 - DELAYED CHANGE", test4)
    run_test("TEST 5 - HEAVY DISORDER", test5)
    run_test("TEST 6 - CHAOTIC DESYNC", test6)
