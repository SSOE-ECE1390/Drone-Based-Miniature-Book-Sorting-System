import cv2

PREVIEW  = 0  # Preview Mode
BLUR     = 1  # Blurring Filter
SOBEL_X  = 2  # SOBEL Edge Detector in X direction
SOBEL_Y  = 3  # SOBEL Edge Detector in Y direction
SOBEL_XY = 4  # SOBEL Edge Detector
CANNY    = 5  # Canny Edge Detector

image_filter = PREVIEW
alive = True

win_name = "Camera Filters"
cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
result = None
source = cv2.VideoCapture(1)

while alive:
    has_frame, frame = source.read()
    if not has_frame:
        break

 # Flip the horizontal of the video frame
    frame = cv2.flip(frame, 1)
    
    # Depending on what mode we are in, filter the data
    if image_filter == PREVIEW:
        result = frame
    elif image_filter == CANNY:
        result = cv2.Canny(frame, 80, 150)
    elif image_filter == SOBEL_X:
        result = cv2.Sobel(frame, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=5)
    elif image_filter == SOBEL_Y:
        result = cv2.Sobel(frame, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=5)
    elif image_filter == SOBEL_XY:
        result = cv2.Sobel(frame, ddepth=cv2.CV_64F, dx=1, dy=1, ksize=5)
    elif image_filter == BLUR:
        result = cv2.blur(frame, (45,45))
   
    cv2.imshow(win_name, result)

    # This catches any key strokes and updates the filter mode
    key = cv2.waitKey(1)
    if key == ord("Q") or key == ord("q") or key == 27:
        alive = False
    elif key == ord("C") or key == ord("c"):
        image_filter = CANNY
    elif key == ord("S") or key == ord("s"):
        image_filter = SOBEL_XY
    elif key == ord("X") or key == ord("x"):
        image_filter = SOBEL_X
    elif key == ord("Y") or key == ord("y"):
        image_filter = SOBEL_Y
    elif key == ord("B") or key == ord("b"):
        image_filter = BLUR
    elif key == ord("P") or key == ord("p"):
        image_filter = PREVIEW