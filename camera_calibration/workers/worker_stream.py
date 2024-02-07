import cv2 as cv

from defs import QtCore, Signal


class StreamWorker(QtCore.QObject):
    new_frame = Signal(object)
    finished = Signal()

    def __init__(
        self,
        camera_no,
    ):
        super().__init__()

        self.camera_no = camera_no
        self.stop_flag = False
        self.cap = None
        self.frame = None

    def stream(self):
        self.stop_flag = False
        self.cap = cv.VideoCapture(self.camera_no)

        while not self.stop_flag:
            ret, frame = self.cap.read()
            if ret:
                self.new_frame.emit(frame)
        self.cap.release()
        self.finished.emit()
        self.stop_flag = False
        self.deleteLater()

    def stop_stream(self):
        self.stop_flag = True


if __name__ == "__main__":
    s = StreamWorker(1)
