import qtawesome as qta

from camera_calibration.custom_components.dock_base import BaseDock
from camera_calibration.funcs import make_pattern_pixmap
from defs import QtCore, QtWidgets, Signal


class PatternDock(BaseDock):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pattern")
        self.screens = QtWidgets.QApplication.instance().screens()

        self.display = None

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_pattern_combobox = QtWidgets.QComboBox(self)
        self.show_pattern_combobox.addItems(
            ["Checkerboard", "Circles", "Asymmetric Circles"]
        )
        self.show_pattern_combobox.currentIndexChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_pattern_combobox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_col_spinbox = QtWidgets.QSpinBox(self)
        self.show_col_spinbox.setSuffix(" Columns")
        self.show_col_spinbox.setRange(1, 100)
        self.show_col_spinbox.setValue(10)
        self.show_col_spinbox.valueChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_col_spinbox)

        self.show_row_spinbox = QtWidgets.QSpinBox(self)
        self.show_row_spinbox.setSuffix(" Rows")
        self.show_row_spinbox.setRange(1, 100)
        self.show_row_spinbox.setValue(10)
        self.show_row_spinbox.valueChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_row_spinbox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_size_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.show_size_spinbox.setPrefix("Size/Spacing ")
        self.show_size_spinbox.setSuffix(" mm")
        self.show_size_spinbox.setRange(1, 100)
        self.show_size_spinbox.setDecimals(1)
        self.show_size_spinbox.setSingleStep(0.5)
        self.show_size_spinbox.setValue(25)
        self.show_size_spinbox.valueChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_size_spinbox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_radius_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.show_radius_spinbox.setPrefix("Radius ratio ")
        self.show_radius_spinbox.setRange(1, 100)
        self.show_radius_spinbox.setDecimals(1)
        self.show_radius_spinbox.setSingleStep(0.5)
        self.show_radius_spinbox.setValue(5)
        self.show_radius_spinbox.valueChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_radius_spinbox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.screen_combobox = QtWidgets.QComboBox(self)
        for i in range(len(self.screens)):
            self.screen_combobox.addItem("Screen {}".format(i + 1))
        self.screen_combobox.currentIndexChanged.connect(self.show_button_toggled)
        row_layout.addWidget(self.screen_combobox)

        icon_size = 18
        self.show_button = QtWidgets.QPushButton(self)
        self.show_icon = qta.icon("mdi.checkerboard")
        self.show_button.setIcon(self.show_icon)
        self.show_button.setCheckable(True)
        self.show_button.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.show_button.setText("Show Pattern")
        self.show_button.setToolTip("Show calibration pattern.")
        self.show_button.toggled.connect(self.show_button_toggled)
        row_layout.addWidget(self.show_button)

        self.dock_layout.addStretch()

    def show_button_toggled(self):
        if self.show_button.isChecked():
            self.show_pattern()
        else:
            self.display = None

    def get_settings(self):
        return dict(
            pattern=self.show_pattern_combobox.currentText(),
            screen=self.screens[int(self.screen_combobox.currentText()[-1]) - 1],
            rows=self.show_row_spinbox.value(),
            cols=self.show_col_spinbox.value(),
            size=self.show_size_spinbox.value(),
            radius_rate=self.show_radius_spinbox.value(),
        )

    def show_pattern(self):
        settings = self.get_settings()

        self.display = MyPatternDisplay()
        self.display.closed.connect(self.show_button.toggle)
        pixmap = make_pattern_pixmap(
            settings["screen"],
            settings["cols"],
            settings["rows"],
            settings["size"],
            settings["radius_rate"],
            settings["pattern"],
        )
        self.display.setPixmap(pixmap)

        self.display.show()
        self.display.windowHandle().setScreen(settings["screen"])
        self.display.showFullScreen()

    def gui_save(self, settings):
        self.display = None
        super().gui_save(settings)


class MyPatternDisplay(QtWidgets.QLabel):
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key_Escape:
            self.closed.emit()
            self.deleteLater()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = PatternDock()
    widget.show()

    app.exec()
