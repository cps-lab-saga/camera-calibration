import cv2 as cv


def get_cameras(max_no=100):
    cameras = []
    for index, _ in enumerate(reversed(range(max_no))):
        cap = cv.VideoCapture(index)
        if cap.isOpened():
            cameras.append(index)
            cap.release()
        else:
            cap.release()
            break
    return cameras
