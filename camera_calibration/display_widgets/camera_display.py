import qtawesome as qta

from camera_calibration.funcs import cvImg_to_qImg
from camera_calibration.workers.worker_stream import StreamWorker
from defs import QtCore, QtWidgets, QtGui, Signal


class CameraDisplay(QtWidgets.QWidget):
    add_image = Signal(object, str)
    closed = Signal()

    def __init__(self, camera_no, parent=None):
        super().__init__(parent=parent)

        self.setWindowFlags(QtCore.Qt.WindowType.Window)

        self.camera_no = camera_no
        self.resize(640, 480)

        layout = QtWidgets.QVBoxLayout(self)

        self.pixmap_label = QtWidgets.QLabel(self)
        self.pixmap_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.pixmap_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored,
        )
        layout.addWidget(self.pixmap_label)

        self.camera_button = QtWidgets.QPushButton(self)
        self.camera_button.setIcon(qta.icon("mdi6.camera"))
        self.camera_button.clicked.connect(self.camera_button_clicked)
        layout.addWidget(self.camera_button)

        self.stream_thread = QtCore.QThread()
        self.stream_worker = StreamWorker(self.camera_no)
        self.stream_worker.moveToThread(self.stream_thread)
        self.stream_thread.started.connect(self.stream_worker.stream)
        self.stream_worker.new_frame.connect(self.set_image)
        self.stream_worker.finished.connect(self.stream_finished)
        self.stream_thread.start()

        self.image = None
        self.pixmap = None
        self.count = 1

    def set_image(self, image):
        qt_img = cvImg_to_qImg(image)
        self.pixmap = QtGui.QPixmap(qt_img)
        self.pixmap_label.setPixmap(
            self.pixmap.scaledToWidth(self.pixmap_label.width())
        )
        self.image = image

    def camera_button_clicked(self):
        self.add_image.emit(self.image, f"camera_{self.count}")
        self.count += 1

    def stream_finished(self):
        self.stream_thread.exit()
        self.stream_worker = None
        self.close()

    def closeEvent(self, event):
        if self.stream_worker is not None:
            self.stream_worker.stop_stream()
            event.ignore()
        else:
            event.accept()
            self.closed.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = CameraDisplay(1)
    widget.show()

    app.exec()
