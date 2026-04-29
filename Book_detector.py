import cv2
import cv2.aruco as aruco


class BookDetector:
    def __init__(self, shelf_controller):
        self.shelf = shelf_controller
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
        self.aruco_params = aruco.DetectorParameters()
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        self.correct_order = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    def detect_markers(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        if ids is None:
            return []

        markers = []
        for i, marker_id in enumerate(ids.flatten()):
            center_x = corners[i][0][:, 0].mean()
            markers.append((center_x, int(marker_id)))

        markers.sort(key=lambda m: m[0])
        detected_order = [m[1] for m in markers]

        return detected_order

    def find_out_of_order(self, detected_order):
        out_of_order = []

        for slot, book_id in enumerate(detected_order):
            if slot < len(self.correct_order) and book_id != self.correct_order[slot]:
                out_of_order.append((slot, book_id))

        return out_of_order

    async def process_frame(self, frame):
        detected_order = self.detect_markers(frame)

        if not detected_order:
            return None

        out_of_order = self.find_out_of_order(detected_order)

        return {"detected_order": detected_order, "out_of_order": out_of_order}

    async def release_book(self, slot):
        await self.shelf.release(slot)

    async def hold_book(self, slot):
        await self.shelf.hold(slot)
