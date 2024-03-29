from camera_calibration.custom_components.gui_save_base import BaseGuiSave

from camera_calibration.defs import QtCore, QtWidgets


class BaseDock(QtWidgets.QDockWidget, BaseGuiSave):
    def __init__(self):
        super().__init__()

        self.setObjectName(self.__class__.__name__)
        self.save_heading = self.__class__.__name__

        self.dock_contents = QtWidgets.QFrame(parent=self)
        self.setWidget(self.dock_contents)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setFeatures(
            self.DockWidgetFeature.DockWidgetFloatable
            | self.DockWidgetFeature.DockWidgetMovable
            | self.DockWidgetFeature.DockWidgetClosable
        )

        self.dock_layout = QtWidgets.QBoxLayout(
            QtWidgets.QBoxLayout.TopToBottom, self.dock_contents
        )

        # self.dockLocationChanged.connect(self.change_layout_based_on_dock_area)

    def change_layout_based_on_dock_area(self, area):
        if area in [QtCore.Qt.LeftDockWidgetArea, QtCore.Qt.RightDockWidgetArea]:
            self.dock_layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
        else:
            self.dock_layout.setDirection(QtWidgets.QBoxLayout.LeftToRight)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = BaseDock()
    widget.show()

    app.exec()
