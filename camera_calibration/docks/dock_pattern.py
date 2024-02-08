from pathlib import Path

import qtawesome as qta

from camera_calibration.custom_components.dock_base import BaseDock
from camera_calibration.defs import QtCore, QtWidgets, Signal
from camera_calibration.funcs import make_pattern_pixmap


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
        self.show_pattern_combobox.currentIndexChanged.connect(self.update_pattern)
        row_layout.addWidget(self.show_pattern_combobox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_col_spinbox = QtWidgets.QSpinBox(self)
        self.show_col_spinbox.setSuffix(" Columns")
        self.show_col_spinbox.setRange(1, 100)
        self.show_col_spinbox.setValue(10)
        self.show_col_spinbox.valueChanged.connect(self.update_pattern)
        row_layout.addWidget(self.show_col_spinbox)

        self.show_row_spinbox = QtWidgets.QSpinBox(self)
        self.show_row_spinbox.setSuffix(" Rows")
        self.show_row_spinbox.setRange(1, 100)
        self.show_row_spinbox.setValue(10)
        self.show_row_spinbox.valueChanged.connect(self.update_pattern)
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
        self.show_size_spinbox.valueChanged.connect(self.update_pattern)
        row_layout.addWidget(self.show_size_spinbox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        self.show_radius_spinbox = QtWidgets.QDoubleSpinBox(self)
        self.show_radius_spinbox.setPrefix("Radius ratio ")
        self.show_radius_spinbox.setRange(1, 100)
        self.show_radius_spinbox.setDecimals(1)
        self.show_radius_spinbox.setSingleStep(0.5)
        self.show_radius_spinbox.setValue(5)
        self.show_radius_spinbox.valueChanged.connect(self.update_pattern)
        row_layout.addWidget(self.show_radius_spinbox)

        row_layout = QtWidgets.QHBoxLayout()
        self.dock_layout.addLayout(row_layout)

        # self.screen_combobox = QtWidgets.QComboBox(self)
        # for i in range(len(self.screens)):
        #     self.screen_combobox.addItem("Screen {}".format(i + 1))
        # self.screen_combobox.currentIndexChanged.connect(self.show_button_toggled)
        # row_layout.addWidget(self.screen_combobox)

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
            rows=self.show_row_spinbox.value(),
            cols=self.show_col_spinbox.value(),
            size=self.show_size_spinbox.value(),
            radius_rate=self.show_radius_spinbox.value(),
        )

    def show_pattern(self):
        settings = self.get_settings()

        self.display = MyPatternDisplay(settings)
        self.display.closed.connect(self.show_button.toggle)
        self.display.show()

    def update_pattern(self):
        if self.display is not None:
            settings = self.get_settings()
            self.display.update_settings(settings)

    def gui_save(self, settings):
        self.display = None
        super().gui_save(settings)


class MyPatternDisplay(QtWidgets.QLabel):
    closed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent=parent)

        self.pixmap = None
        self.settings = settings
        self.resize(600, 600)

        self.setWindowTitle("Pattern (F11 to toggle Full Screen)")

        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Ignored,
        )
        self.context_menu = QtWidgets.QMenu(self)
        export_action = self.context_menu.addAction("Export")
        export_action.setIcon(qta.icon("mdi6.export"))
        export_action.triggered.connect(self.export_pattern)

    def set_pattern(self):
        page_width, page_height = self.width(), self.height()

        self.pixmap = make_pattern_pixmap(
            self.windowHandle().screen(),
            self.settings["cols"],
            self.settings["rows"],
            self.settings["size"],
            page_width,
            page_height,
            radius_rate=self.settings["radius_rate"],
            pattern=self.settings["pattern"],
        )
        self.setPixmap(self.pixmap)

    def update_settings(self, settings):
        self.settings = settings
        self.set_pattern()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.set_pattern()

    def export_pattern(self):
        save_url, _ = QtWidgets.QFileDialog.getSaveFileUrl(
            self,
            caption="Save as",
            filter="Portable Network Graphics (*.png);; JPEG (*.jpg)",
        )
        save_path = Path(save_url.toLocalFile())
        self.pixmap.save(str(save_path))

    def contextMenuEvent(self, event):
        self.context_menu.exec(event.globalPos())

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)

    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif evt.key() == QtCore.Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = PatternDock()
    widget.show()

    app.exec()
