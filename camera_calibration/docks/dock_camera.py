import re

import qtawesome as qta

from camera_calibration.custom_components.dock_base import BaseDock
from camera_calibration.defs import QtWidgets, Signal
from camera_calibration.funcs.opencv_camera import get_cameras


class CameraDock(BaseDock):
    connect_camera_clicked = Signal(int)
    settings_button_clicked = Signal()

    def __init__(self, backend=""):
        super().__init__()

        self.setWindowTitle("Camera")

        self.cameras = []
        self.camera_no = 0

        devices_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(devices_layout)

        self.devices_combobox = QtWidgets.QComboBox(self)
        self.devices_combobox.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum
        )
        devices_layout.addWidget(self.devices_combobox)
        self.refresh_devices()

        self.refresh_button = QtWidgets.QPushButton(self)
        self.refresh_button.setIcon(qta.icon("mdi.refresh"))
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.refresh_button.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Maximum
        )
        devices_layout.addWidget(self.refresh_button)

        self.connect_button = QtWidgets.QPushButton(self)
        self.connect_button.setIcon(qta.icon("mdi.link"))
        self.connect_button.setText("Connect")
        self.connect_button.clicked.connect(self.connect_button_clicked)
        self.dock_layout.addWidget(self.connect_button)

        if backend == "DSHOW":
            self.settings_button = QtWidgets.QPushButton(self)
            self.settings_button.setIcon(qta.icon("ri.settings-3-fill"))
            self.settings_button.setText("Settings")
            self.settings_button.clicked.connect(self.settings_button_clicked.emit)
            self.dock_layout.addWidget(self.settings_button)

    def refresh_devices(self):
        self.devices_combobox.clear()
        self.cameras = get_cameras(10)
        self.devices_combobox.addItems([f"Camera {i}" for i in self.cameras])
        if self.camera_no and self.camera_no in self.cameras:
            self.devices_combobox.setCurrentText(f"Camera {self.camera_no}")

    def connect_button_clicked(self):
        camera = self.devices_combobox.currentText()
        self.connect_button.setDisabled(True)
        self.refresh_button.setDisabled(True)
        self.connect_camera_clicked.emit(int(re.findall(r"\d+", camera)[0]))

    def camera_closed(self):
        self.connect_button.setDisabled(False)
        self.refresh_button.setDisabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = CameraDock()
    widget.show()

    app.exec()
