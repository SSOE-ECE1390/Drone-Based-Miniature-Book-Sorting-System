from ultralytics import YOLO

CORRECT_ORDER = [
    0,
    1,
    2,
    3,
    4,
    5,
]  # vertical_line, horizontal_line, circle, square, cross, x
MODEL_PATH = "best.pt"

model = YOLO(MODEL_PATH)


def detect_books(frame):
    results = model(frame, conf=0.5, verbose=False)[0]
    slots = [None] * 6
    frame_w = frame.shape[1]
    slot_w = frame_w / 6

    for box in results.boxes:
        cx = float(box.xywh[0][0])
        slot_idx = min(int(cx / slot_w), 5)
        slots[slot_idx] = int(box.cls[0])

    return slots


def get_swaps(detected):
    order = list(detected)
    swaps = []

    for i in range(len(order)):
        if order[i] == CORRECT_ORDER[i]:
            continue
        target = CORRECT_ORDER[i]
        try:
            j = order.index(target, i + 1)
            swaps.append((i + 1, j + 1))
            order[i], order[j] = order[j], order[i]
        except ValueError:
            print(f"[SORT] Book {target} not found in remaining slots")

    return swaps


def analyze_shelf(frame):
    detected = detect_books(frame)
    print(f"[SORT] Detected: {detected}")

    if detected == CORRECT_ORDER:
        print("[SORT] Shelf is in correct order")
        return []

    swaps = get_swaps(detected)
    for s in swaps:
        print(f"[SORT] Swap slot {s[0]} <-> slot {s[1]}")

    return swaps
