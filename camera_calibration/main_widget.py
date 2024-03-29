import json
import logging
import sys
from functools import partial
from pathlib import Path

import cv2 as cv
import numpy as np
import qtawesome as qta

from camera_calibration.custom_components import DroppableWidget, FlowLayout
from camera_calibration.defs import (
    QtCore,
    QtGui,
    QtWidgets,
    log_file,
    settings_file,
    resource_dir,
)
from camera_calibration.display_widgets import ImageDisplay
from camera_calibration.display_widgets.camera_display import CameraDisplay
from camera_calibration.docks import PatternDock, CameraDock, CalibrateDock
from camera_calibration.menu_bar import MenuBar


class MainWidget(QtWidgets.QMainWindow):
    calibration_saved = QtCore.Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("Calibrate Camera")
        self.setWindowIcon(QtGui.QIcon(str(resource_dir() / "calibration.svg")))
        self.resize(800, 600)

        self.menu_bar = MenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menu_bar.open_image_file.connect(self.item_dropped)

        self.main_widget = DroppableWidget(filetypes=["image"], parent=self)
        self.main_widget.setToolTip("Drop images here.")
        self.main_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.main_widget.customContextMenuRequested.connect(
            self.main_widget_context_menu_requested
        )
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        self.scroll_area = QtWidgets.QScrollArea(self.main_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QtWidgets.QWidget(self)
        self.scroll_area.setWidget(self.scroll_area_contents)
        self.scroll_area_layout = FlowLayout(self.scroll_area_contents)
        self.main_layout.addWidget(self.scroll_area)

        self.context_menu = QtWidgets.QMenu(self.scroll_area_contents)
        clear_all_action = self.context_menu.addAction("Clear All")
        clear_all_action.setIcon(qta.icon("mdi6.delete", color="red"))
        clear_all_action.triggered.connect(self.clear_scroll_area)

        self.docks = {
            "Pattern": PatternDock(),
            "Camera": CameraDock(),
            "Calibrate": CalibrateDock(),
        }
        for dock in self.docks.values():
            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.docks["Camera"].connect_camera_clicked.connect(self.open_camera)
        self.docks["Calibrate"].start_calibrate.connect(self.calibrate)
        self.docks["Calibrate"].save_clicked.connect(self.save_calibration)

        self.image_display_items = []
        self.image_width = 100

        self.camera_display = None
        self.fisheye = None
        self.rms_error = None
        self.intrinsic_matrix = None
        self.distortion_coeffs = None
        self.rotation_vecs = None
        self.translation_vecs = None
        self.save_path = None

        self.pool = QtCore.QThreadPool.globalInstance()

        # load settings from previous session
        self.settings_file = settings_file()
        if self.settings_file.is_file():
            settings = QtCore.QSettings(
                str(self.settings_file), QtCore.QSettings.IniFormat
            )
            self.gui_restore(settings)

        self.main_widget.item_dropped.connect(self.item_dropped)

    def main_widget_context_menu_requested(self, _):
        self.context_menu.exec(QtGui.QCursor.pos())

    def item_dropped(self, path):
        img = cv.imread(str(path))
        if img is None:
            self.error_dialog(f"Could not read {path}")
            return
        self.add_image(img, path.name)

    def add_image(self, img, text):
        image_display = ImageDisplay()
        image_display.set_image(img, text)
        image_display.scale_image_to_width(self.image_width)
        image_display.close_clicked.connect(partial(self.remove_image, image_display))

        pattern_settings = self.docks["Pattern"].get_settings()
        image_display.find_points(
            pattern_settings["rows"] - 1,
            pattern_settings["cols"] - 1,
            pattern_settings["pattern"],
        )

        self.image_display_items.append(image_display)
        self.scroll_area_layout.addWidget(image_display)
        QtWidgets.QApplication.processEvents()

    def remove_image(self, image_display):
        self.scroll_area_layout.removeWidget(image_display)
        self.image_display_items.remove(image_display)
        image_display.deleteLater()

    def clear_scroll_area(self):
        for image_display in self.image_display_items:
            self.scroll_area_layout.removeWidget(image_display)
            image_display.deleteLater()
        self.image_display_items.clear()

    def open_camera(self, camera_no):
        self.camera_display = CameraDisplay(camera_no, self)
        self.camera_display.add_image.connect(self.add_image)
        self.camera_display.closed.connect(self.docks["Camera"].camera_closed())
        self.camera_display.show()

    def calibrate(self, fisheye):
        self.fisheye = fisheye
        imgshapes = []
        objpoints = []
        imgpoints = []
        for image_display in self.image_display_items:
            if (
                image_display.objpoints is not None
                and image_display.imgpoints is not None
            ):
                objpoints.append(image_display.objpoints)
                imgpoints.append(image_display.imgpoints)
                imgshapes.append(image_display.shape)

        if len(objpoints) == 0 or len(imgpoints) == 0:
            self.error_dialog("No calibration data available!")
            self.clear_results()
            return

        if len(set(imgshapes)) > 1:
            self.error_dialog("Image with different shape was used!")
            self.clear_results()
            return
        if fisheye:
            objpoints = np.expand_dims(
                np.asarray(objpoints), -2
            )  # https://github.com/opencv/opencv/issues/5534
            (
                self.rms_error,
                self.intrinsic_matrix,
                self.distortion_coeffs,
                self.rotation_vecs,
                self.translation_vecs,
            ) = cv.fisheye.calibrate(objpoints, imgpoints, imgshapes[0], None, None)

        else:
            (
                self.rms_error,
                self.intrinsic_matrix,
                self.distortion_coeffs,
                self.rotation_vecs,
                self.translation_vecs,
            ) = cv.calibrateCamera(objpoints, imgpoints, imgshapes[0], None, None)

        self.output_results()

    def save_calibration(self):
        if any(
            (
                self.fisheye is None,
                self.rms_error is None,
                self.intrinsic_matrix is None,
                self.distortion_coeffs is None,
                self.rotation_vecs is None,
                self.translation_vecs is None,
            )
        ):
            self.error_dialog("No calibration available!")
            return

        save_url, _ = QtWidgets.QFileDialog.getSaveFileUrl(
            self, caption="Save as", filter="JSON (*.json);; Numpy Binary (*.npz)"
        )
        self.save_path = Path(save_url.toLocalFile())

        if self.save_path.suffix == ".json":
            with open(self.save_path, "w") as f:
                json.dump(
                    dict(
                        K=self.intrinsic_matrix.tolist(),
                        D=self.distortion_coeffs.tolist(),
                        fisheye=self.fisheye,
                    ),
                    f,
                    sort_keys=False,
                    indent=4,
                )

        elif self.save_path.suffix == ".npz":
            np.savez(
                self.save_path,
                K=self.intrinsic_matrix,
                D=self.distortion_coeffs,
                fisheye=self.fisheye,
            )
        self.calibration_saved.emit(self.save_path)

    def clear_results(self):
        self.rms_error = None
        self.intrinsic_matrix = None
        self.distortion_coeffs = None
        self.rotation_vecs = None
        self.translation_vecs = None
        self.fisheye = None
        self.save_path = None
        self.docks["Calibrate"].results_label.setText("")

    def output_results(self):
        self.docks["Calibrate"].set_results(
            self.rms_error,
            self.intrinsic_matrix,
            self.distortion_coeffs,
            self.rotation_vecs,
            self.translation_vecs,
            self.fisheye,
        )

    def wheelEvent(self, evt):
        if evt.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            self.image_width += evt.angleDelta().y() / 12
            if self.image_width < 0:
                self.image_width = 0

            for image_display in self.image_display_items:
                image_display.scale_image_to_width(self.image_width)

    def gui_save(self, settings):
        for dock in self.docks.values():
            dock.gui_save(settings)
        settings.setValue("Window/geometry", self.saveGeometry())
        settings.setValue("Window/state", self.saveState())

    def gui_restore(self, settings):
        try:
            if geometry := settings.value("Window/geometry"):
                self.restoreGeometry(geometry)
            if state := settings.value("Window/state"):
                self.restoreState(state)
            for dock in self.docks.values():
                dock.gui_restore(settings)

        except Exception as e:
            self.error_dialog(f"{self.settings_file} is corrupted!\n{str(e)}")

    def closeEvent(self, event):
        """save before closing"""
        settings = QtCore.QSettings(str(self.settings_file), QtCore.QSettings.IniFormat)
        self.gui_save(settings)
        event.accept()

    def error_dialog(self, error):
        QtWidgets.QMessageBox.critical(self, "Error", error)

    @staticmethod
    def setup_logger():
        formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

        log_handler_stdout = logging.StreamHandler(sys.stdout)
        log_handler_stdout.setFormatter(formatter)

        log_handler_file = logging.FileHandler(log_file())
        log_handler_file.setFormatter(formatter)

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        log.addHandler(log_handler_stdout)
        log.addHandler(log_handler_file)


def main():
    app = QtWidgets.QApplication([])
    win = MainWidget()
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
