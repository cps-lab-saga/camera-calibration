from defs import QtCore, QtWidgets


class MyScrollArea(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setWidgetResizable(True)

        self.contents = QtWidgets.QWidget(self)
        self.setWidget(self.contents)
        self.layout = QtWidgets.QVBoxLayout(self.contents)

    def resizeEvent(self, event):
        self.contents.setMaximumWidth(self.width() - self.verticalScrollBar().width())

        super().resizeEvent(event)
