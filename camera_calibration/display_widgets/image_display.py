import cv2 as cv
import qtawesome as qta

from camera_calibration.custom_components import tab10_gbr, tab10_rgb
from camera_calibration.funcs import cvImg_to_qImg, find_points
from defs import QtCore, QtWidgets, QtGui, Signal


class ImageDisplay(QtWidgets.QFrame):
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        layout = QtWidgets.QGridLayout(self)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.item_label = QtWidgets.QLabel(self)
        self.item_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout.addWidget(self.item_label, 0, 0)

        self.delete_button = QtWidgets.QPushButton(self)
        self.delete_button.setIcon(qta.icon("mdi6.close"))
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.delete_button, 0, 1)

        self.pixmap_label = QtWidgets.QLabel(self)
        self.pixmap_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.pixmap_label, 1, 0, 1, 2)

        self.raw_image = None
        self.image = None
        self.label = None
        self.pixmap = None
        self.image_width = 200

        self.objpoints = None
        self.imgpoints = None
        self.shape = None
        layout.rowStretch(-1)

    def set_image(self, image, label=None, processed=False):
        qt_img = cvImg_to_qImg(image)
        self.pixmap = QtGui.QPixmap(qt_img)
        self.pixmap_label.setPixmap(self.pixmap.scaledToWidth(self.image_width))
        self.image = image
        if not processed:
            self.raw_image = image
            self.shape = self.raw_image.shape[:2][::-1]

        if label is not None:
            self.label = label
            self.item_label.setText(label)

    def scale_image_to_width(self, width):
        self.image_width = width
        self.pixmap_label.setPixmap(self.pixmap.scaledToWidth(self.image_width))

    def find_points(self, nx, ny, pattern):
        pool = QtCore.QThreadPool.globalInstance()
        runnable = FindPointsRunnable(self.raw_image, nx, ny, pattern)
        runnable.setAutoDelete(True)
        runnable.find_points_signal.points_found.connect(self.points_found)
        pool.start(runnable)

    def points_found(self, results):
        nx, ny, img, ret, objpoints, imgpoints = results
        if ret:
            self.objpoints = objpoints
            self.imgpoints = imgpoints
            self.image = self.draw_ok(self.image, (nx, ny), imgpoints, ret)
        else:
            self.objpoints = None
            self.imgpoints = None
            self.image = self.draw_error(self.image)
        self.set_image(self.image, processed=True)

    @staticmethod
    def draw_ok(image, pattern_size, imgpoints, ret):
        image_h, image_w, _ = image.shape

        image = image.copy()
        cv.drawChessboardCorners(image, pattern_size, imgpoints, ret)

        border_size = round(image_w / 20)
        image = cv.copyMakeBorder(
            image,
            top=border_size,
            bottom=border_size,
            left=border_size,
            right=border_size,
            borderType=cv.BORDER_CONSTANT,
            value=tab10_rgb["green"],
        )
        return image

    @staticmethod
    def draw_error(image):
        image = image.copy()
        image_h, image_w, _ = image.shape
        font = cv.FONT_HERSHEY_SIMPLEX
        rectangle_w = image_w * 2 / 4
        rectangle_h = image_h * 2 / 4

        text_scale = 0.15  # 0 to 1
        font_scale = round(rectangle_w / (25 / text_scale))
        thickness = round(rectangle_w / 50)

        cv.rectangle(
            image,
            (
                round(image_w / 2 - rectangle_w / 2),
                round(image_h / 2 + rectangle_h / 2),
            ),
            (
                round(image_w / 2 + rectangle_w / 2),
                round(image_h / 2 - rectangle_h / 2),
            ),
            tab10_gbr["red"],
            -1,
        )

        text = "Points\nNot\nFound!"
        rows = text.count("\n") + 1
        line_spacing_y = rectangle_h / (rows + 1)
        y0 = image_h / 2 - (rows / 2 - 0.5) * line_spacing_y
        x0 = image_w / 2
        for i, line in enumerate(text.split("\n")):
            text_size, _ = cv.getTextSize(line, font, font_scale, thickness)
            y = round(y0 + i * line_spacing_y + text_size[1] / 2)
            x = round(x0 - text_size[0] / 2)
            cv.putText(
                image,
                line,
                (x, y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv.LINE_AA,
            )

        border_size = round(image_w / 20)
        image = cv.copyMakeBorder(
            image,
            top=border_size,
            bottom=border_size,
            left=border_size,
            right=border_size,
            borderType=cv.BORDER_CONSTANT,
            value=tab10_gbr["red"],
        )
        return image


class FindPointsSignals(QtCore.QObject):
    points_found = Signal(object)


class FindPointsRunnable(QtCore.QRunnable):
    def __init__(self, img, nx, ny, pattern):
        super().__init__()

        self.img = img
        self.nx = nx
        self.ny = ny
        self.pattern = pattern
        self.find_points_signal = FindPointsSignals()

    def run(self):
        img, ret, objpoints, imgpoints = find_points(
            self.img, self.nx, self.ny, self.pattern
        )
        self.find_points_signal.points_found.emit(
            (self.nx, self.ny, img, ret, objpoints, imgpoints)
        )


if __name__ == "__main__":
    import numpy as np

    black_img = np.zeros([100, 100, 3], dtype=np.uint8)

    app = QtWidgets.QApplication([])
    widget = ImageDisplay()
    widget.set_image(black_img, "test")
    widget.show()

    app.exec()
