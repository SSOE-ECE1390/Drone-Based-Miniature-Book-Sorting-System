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
# TEST 1: simple swap (I and X, a=0, b=2)
# initial: X is at slot 0, I is at slot 2 — swap them
# -------------------------
test1 = [
    ["X", "+", "I", "-", "[]", "O"],  # initial
    ["+", "I", "-", "[]", "O", "X"],  # step 1: slot 0 released, X in TEMP
    ["I", "+", "-", "[]", "O", "X"],  # step 2: slot 2 released, slot 0 holds I
    ["I", "+", "X", "-", "[]", "O"],  # step 3: TEMP released, slot 2 holds X = CORRECT
]


# -------------------------
# TEST 2: repeated frames during simple swap (no-spam check)
# user takes a while between each physical move
# -------------------------
test2 = [
    ["X", "+", "I", "-", "[]", "O"],  # initial — start swap, step 1 issued
    ["X", "+", "I", "-", "[]", "O"],  # repeat — should be ignored
    ["X", "+", "I", "-", "[]", "O"],  # repeat — should be ignored
    ["+", "I", "-", "[]", "O", "X"],  # user finally executed step 1
    ["+", "I", "-", "[]", "O", "X"],  # repeat — ignored
    ["I", "+", "-", "[]", "O", "X"],  # step 2
    ["I", "+", "X", "-", "[]", "O"],  # step 3 = CORRECT
]


# -------------------------
# TEST 3: two swaps (no edge cases — all step 2 frames differ from step 3)
# initial: [I, X, [], -, +, O]
#   swap 1: X@1 ↔ +@4
#   swap 2: []@2 ↔ X@4
# -------------------------
test3 = [
    ["I", "X", "[]", "-", "+", "O"],  # initial
    ["I", "[]", "-", "+", "O", "X"],  # swap1 step 1: slot 1 released, X in TEMP
    ["I", "+", "[]", "-", "O", "X"],  # swap1 step 2: slot 4 released, slot 1 holds +
    ["I", "+", "[]", "-", "X", "O"],  # swap1 step 3: TEMP released, slot 4 holds X
    ["I", "+", "-", "X", "O", "[]"],  # swap2 step 1: slot 2 released, [] in TEMP
    ["I", "+", "X", "-", "O", "[]"],  # swap2 step 2: slot 4 released, slot 2 holds X
    ["I", "+", "X", "-", "[]", "O"],  # swap2 step 3 = CORRECT
]


# -------------------------
# TEST 4: deviation — user makes the wrong move
# algorithm commands X→TEMP, expects [+, I, -, [], O, X]
# user instead moves O — frame doesn't match expectation
# -------------------------
test4 = [
    ["X", "+", "I", "-", "[]", "O"],  # initial — algorithm starts swap, step 1
    ["+", "I", "-", "[]", "X", "O"],  # WRONG — should trigger DEVIATION print
]


# -------------------------
# TEST 5: shelf already correct
# -------------------------
test5 = [
    ["I", "+", "X", "-", "[]", "O"],  # CORRECT_ORDER → SHELF OK
]


# -------------------------
# TEST 6: heavy disorder (3 swaps, no edge cases)
# initial: [+, X, [], -, I, O]
#   swap 1: +@0 ↔ I@4
#   swap 2: X@1 ↔ +@4
#   swap 3: []@2 ↔ X@4
# -------------------------
test6 = [
    ["+", "X", "[]", "-", "I", "O"],  # initial
    ["X", "[]", "-", "I", "O", "+"],  # swap1 step 1
    ["I", "X", "[]", "-", "O", "+"],  # swap1 step 2
    ["I", "X", "[]", "-", "+", "O"],  # swap1 step 3
    ["I", "[]", "-", "+", "O", "X"],  # swap2 step 1
    ["I", "+", "[]", "-", "O", "X"],  # swap2 step 2
    ["I", "+", "[]", "-", "X", "O"],  # swap2 step 3
    ["I", "+", "-", "X", "O", "[]"],  # swap3 step 1
    ["I", "+", "X", "-", "O", "[]"],  # swap3 step 2
    ["I", "+", "X", "-", "[]", "O"],  # swap3 step 3 = CORRECT
]


if __name__ == "__main__":
    run_test("TEST 1 - SIMPLE SWAP", test1)
    run_test("TEST 2 - REPEATED FRAMES (DELAYED USER)", test2)
    run_test("TEST 3 - TWO SWAPS", test3)
    run_test("TEST 4 - DEVIATION (WRONG MOVE)", test4)
    run_test("TEST 5 - ALREADY CORRECT", test5)
    run_test("TEST 6 - HEAVY DISORDER (3 SWAPS)", test6)
