import cv2
import numpy as np
import easyocr
from PIL import Image
from ultralytics import YOLO
from sorting_algorithm import sorting_algorithm


class ShelfReader:
    def __init__(self, yolo_model_path=None, debug=False):
        if yolo_model_path:
            self.detector = YOLO(yolo_model_path)
        else:
            self.detector = YOLO("yolov8n.pt")
            print(
                "WARNING: Using generic YOLO model. Load trained spine detector for better results."
            )

        self.reader = easyocr.Reader(["en"])
        self.sorting_algorithm = sorting_algorithm()
        self.shelf_inventory = []
        self.debug = debug

    def read_shelf(self, image):
        if isinstance(image, str):
            image = cv2.imread(image)
            if image is None:
                raise FileNotFoundError(f"Could not load image: {image}")

        self.shelf_inventory = []

        spines = self._detect_spines(image)
        print(f"Detected {len(spines)} book spines")

        for i, spine_bbox in enumerate(spines):
            book_info = self._process_spine(image, spine_bbox, book_index=i)
            self.shelf_inventory.append(book_info)

        self._validate_shelf_order()
        return self.shelf_inventory

    def _detect_spines(self, image):
        results = self.detector(image)

        spines = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()

                    if confidence > 0.5:
                        spines.append(
                            {
                                "bbox": (int(x1), int(y1), int(x2), int(y2)),
                                "confidence": float(confidence),
                            }
                        )

        spines.sort(key=lambda s: s["bbox"][0])
        return [s["bbox"] for s in spines]

    def _process_spine(self, image, bbox, book_index):
        x1, y1, x2, y2 = bbox

        # Stage 1: Full spine (no cropping)
        cropped = image[y1:y2, x1:x2]

        # Stage 2: Grayscale
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

        # Stage 3: Threshold for bright regions (white label)
        _, bright_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # Stage 4: Find contours
        contours, _ = cv2.findContours(
            bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        label_roi = gray
        bad_capture = False

        if contours:
            valid_contours = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = w / h if h > 0 else 0

                if area > 500 and 0.3 < aspect_ratio < 3:
                    valid_contours.append((cnt, area, x, y, w, h))

            if valid_contours:
                valid_contours.sort(key=lambda c: c[1], reverse=True)
                cnt, _, lx, ly, lw, lh = valid_contours[0]

                # TODO: Add bad capture detection here
                bad_capture = False

                # Stage 5: Crop to label
                padding = 5
                lx = max(0, lx - padding)
                ly = max(0, ly - padding)
                lw = min(gray.shape[1] - lx, lw + 2 * padding)
                lh = min(gray.shape[0] - ly, lh + 2 * padding)
                label_roi = gray[ly : ly + lh, lx : lx + lw]

        raw_text = self._extract_text(label_roi)
        call_number = self._parse_call_number(raw_text)

        if bad_capture:
            book_info = {
                "index": book_index,
                "bbox": bbox,
                "raw_text": raw_text,
                "call_number": None,
                "status": "BAD_CAPTURE",
                "order_error": None,
            }
            print(
                f"Book {book_index}: Bad capture - bounding box has too much variation, skipping"
            )
        else:
            book_info = {
                "index": book_index,
                "bbox": bbox,
                "raw_text": raw_text,
                "call_number": call_number,
                "status": "OK" if call_number else "CALL_NUMBER_NOT_DETECTED",
                "order_error": None,
            }

            if not call_number:
                print(f"Book {book_index}: Spine detected but call number not readable")
            else:
                print(f"Book {book_index}: {call_number}")

        return book_info

    def _extract_text(self, processed_spine):
        try:
            results = self.reader.readtext(processed_spine, paragraph=False)

            text_list = []
            for detection in results:
                text = detection[1]
                confidence = detection[2]

                if confidence > 0.3:
                    text_list.append(text.strip())

            return text_list

        except Exception as e:
            print(f"OCR error: {e}")
            return []

    def _parse_call_number(self, raw_text):
        if not raw_text:
            return None

        cleaned_text = []
        for text in raw_text:
            text = text.replace("|", "1").replace(" ", "").strip()
            if text:
                cleaned_text.append(text)

        if not cleaned_text:
            return None

        combined = "".join(cleaned_text)

        return combined if len(combined) >= 2 else None

    def _validate_shelf_order(self):
        valid_books = [b for b in self.shelf_inventory if b["call_number"]]

        if len(valid_books) < 2:
            return

        for i in range(1, len(valid_books)):
            prev_book = valid_books[i - 1]
            curr_book = valid_books[i]

            try:
                comparison = self.sorting_algorithm.compare(
                    prev_book["call_number"], curr_book["call_number"]
                )

                if comparison > 0:
                    curr_book["order_error"] = (
                        f"Should come before {prev_book['call_number']}"
                    )
                    curr_book["status"] = "OUT_OF_ORDER"
                    print(
                        f"ORDER ERROR: Book {curr_book['index']} "
                        f"({curr_book['call_number']}) is out of order"
                    )

            except Exception as e:
                print(f"Could not compare books {i-1} and {i}: {e}")

    def get_shelf_report(self):
        total_books = len(self.shelf_inventory)
        detected = sum(1 for b in self.shelf_inventory if b["call_number"])
        unreadable = sum(
            1 for b in self.shelf_inventory if b["status"] == "CALL_NUMBER_NOT_DETECTED"
        )
        out_of_order = sum(
            1 for b in self.shelf_inventory if b["status"] == "OUT_OF_ORDER"
        )

        report = {
            "total_spines_detected": total_books,
            "call_numbers_read": detected,
            "unreadable_spines": unreadable,
            "out_of_order": out_of_order,
            "books": self.shelf_inventory,
            "call_number_sequence": [
                b["call_number"] for b in self.shelf_inventory if b["call_number"]
            ],
        }

        return report

    def visualize_results(self, image_input):
        # Accept either file path or numpy array
        if isinstance(image_input, str):
            image = cv2.imread(image_input)
        else:
            image = image_input.copy()

        for book in self.shelf_inventory:
            x1, y1, x2, y2 = book["bbox"]

            if book["status"] == "OK":
                color = (0, 255, 0)
            elif book["status"] == "OUT_OF_ORDER":
                color = (0, 0, 255)
            elif book["status"] == "BAD_CAPTURE":
                color = (255, 0, 255)
            else:
                color = (0, 165, 255)

            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

            label = book["call_number"] if book["call_number"] else "???"
            cv2.putText(
                image, label, (x1 + 5, y2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
            )

        return image


if __name__ == "__main__":
    reader = ShelfReader(yolo_model_path="best.pt", debug=False)

    results = reader.read_shelf("Drone Image.jpg")

    report = reader.get_shelf_report()

    print("\n" + "=" * 50)
    print("SHELF READING REPORT")
    print("=" * 50)
    print(f"Total spines detected: {report['total_spines_detected']}")
    print(f"Call numbers read: {report['call_numbers_read']}")
    print(f"Unreadable spines: {report['unreadable_spines']}")
    print(f"Out of order: {report['out_of_order']}")
    print(f"\nCall number sequence: {report['call_number_sequence']}")

    reader.visualize_results("Drone Image.jpg")
