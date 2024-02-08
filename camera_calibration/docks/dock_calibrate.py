import qtawesome as qta

from camera_calibration.custom_components.dock_base import BaseDock
from defs import QtCore, QtWidgets, Signal


class CalibrateDock(BaseDock):
    start_calibrate = Signal(bool)
    save_clicked = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Calibrate")

        self.camera_model_combobox = QtWidgets.QComboBox(self)
        self.camera_model_combobox.addItems(["Standard", "Fish Eye"])
        self.dock_layout.addWidget(self.camera_model_combobox)

        self.calibrate_button = QtWidgets.QPushButton(self)
        self.play_icon = qta.icon("mdi.play-circle")
        self.calibrate_button.setIcon(self.play_icon)
        self.calibrate_button.setText("Calibrate")
        self.calibrate_button.setToolTip("Calibrate.")
        self.calibrate_button.clicked.connect(self.calibrate_button_clicked)
        self.dock_layout.addWidget(self.calibrate_button)

        self.results_label = QtWidgets.QLabel(self)
        self.dock_layout.addWidget(self.results_label)

        self.dock_layout.addStretch()

        icon_size = 18
        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setIcon(qta.icon("mdi.content-save"))
        self.save_button.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.save_button.setText("Save")
        self.save_button.setToolTip("Save Calibration.")
        self.save_button.clicked.connect(self.save_clicked)
        self.dock_layout.addWidget(self.save_button)

    def calibrate_button_clicked(self):
        camera_model = self.camera_model_combobox.currentText().replace(" ", "").lower()
        self.start_calibrate.emit(camera_model == "fisheye")

    def set_results(
        self,
        rms_error,
        intrinsic_matrix,
        distortion_coeffs,
        rotation_vecs,
        translation_vecs,
        fisheye,
    ):
        fx = intrinsic_matrix[0, 0]
        fy = intrinsic_matrix[1, 1]
        cx = intrinsic_matrix[0, 2]
        cy = intrinsic_matrix[1, 2]
        s = intrinsic_matrix[0, 1]

        output_text = (
            f"RMS Error,\n"
            f"{rms_error}"
            f"\n\n"
            f"Focal Length (pixels),\n"
            f"fx = {fx:.0f}\n"
            f"fy = {fy:.0f}\n"
            f"\n"
            f"Optical Centres,\n"
            f"cx = {cx:.0f}\n"
            f"cy = {cy:.0f}\n"
            f"\n\n"
            f"Camera Matrix,\n"
            f"{intrinsic_matrix.astype(int)}\n"
            f"\n\n"
        )
        if fisheye:
            k1, k2, k3, k4 = distortion_coeffs[:, 0]
            output_text += (
                f"Distortion Coefficients,\n"
                f"k1 = {k1:.4f}\n"
                f"k2 = {k2:.4f}\n"
                f"k3 = {k3:.4f}\n"
                f"k4 = {k4:.4f}\n"
            )
        else:
            k1, k2, p1, p2, k3 = distortion_coeffs[0]
            output_text += (
                f"Distortion Coefficients,\n"
                f"k1 = {k1:.4f}\n"
                f"k2 = {k2:.4f}\n"
                f"p1 = {p1:.4f}\n"
                f"p2 = {p2:.4f}\n"
                f"k3 = {k3:.4f}\n"
            )
        self.results_label.setText(f"Results:\n\n{output_text}")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = CalibrateDock()
    widget.show()

    app.exec()
