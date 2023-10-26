import json
import logging
import sys
from functools import partial
from pathlib import Path

import cv2 as cv
import numpy as np
import qtawesome as qta
from PySide6 import QtGui

from camera_calibration.custom_components import DroppableWidget, FlowLayout
from camera_calibration.display_widgets import ImageDisplay
from camera_calibration.docks import PatternDock, CalibrateDock
from defs import QtCore, QtWidgets, log_file, settings_file, resource_dir


class MainWidget(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calibrate Camera")
        self.setWindowIcon(QtGui.QIcon(str(resource_dir() / "calibration.svg")))
        self.resize(500, 800)

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
            "Calibrate": CalibrateDock(),
        }
        for dock in self.docks.values():
            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.docks["Calibrate"].calibrate_clicked.connect(self.calibrate)
        self.docks["Calibrate"].save_clicked.connect(self.save_calibration)

        self.image_display_items = []
        self.image_width = 100

        self.rms_error = None
        self.intrinsic_matrix = None
        self.distortion_coeffs = None
        self.rotation_vecs = None
        self.translation_vecs = None

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
            pattern_settings["rows"],
            pattern_settings["cols"],
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

    def calibrate(self):
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
        save_path = Path(save_url.toLocalFile())

        if save_path.suffix == ".json":
            with open(save_path, "w") as f:
                json.dump(
                    dict(
                        K=self.intrinsic_matrix.tolist(),
                        D=self.distortion_coeffs.tolist(),
                    ),
                    f,
                    sort_keys=False,
                    indent=4,
                )

        elif save_path.suffix == ".npz":
            np.savez(save_path, K=self.intrinsic_matrix, D=self.distortion_coeffs)

    def clear_results(self):
        self.rms_error = None
        self.intrinsic_matrix = None
        self.distortion_coeffs = None
        self.rotation_vecs = None
        self.translation_vecs = None
        self.docks["Calibrate"].results_label.setText("")

    def output_results(self):
        self.docks["Calibrate"].set_results(
            self.rms_error,
            self.intrinsic_matrix,
            self.distortion_coeffs,
            self.rotation_vecs,
            self.translation_vecs,
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
