from pathlib import Path

from camera_calibration.defs import QtCore, QtWidgets, Signal
from camera_calibration.funcs import check_file_type


class DroppableWidget(QtWidgets.QWidget):
    item_dropped = Signal(object)

    def __init__(self, *args, filetypes=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filetypes = filetypes
        self.setAcceptDrops(True)

    def valid_paths(self, e):
        if e.mimeData().hasUrls():
            urls = e.mimeData().urls()
            if Path(urls[0].toLocalFile()).is_dir():
                paths = Path(urls[0].toLocalFile()).glob("*")
            else:
                paths = (Path(url.toLocalFile()) for url in e.mimeData().urls())
            if self.filetypes is None:
                return [p for p in paths if p.is_file()]
            else:
                return [p for p in paths if check_file_type(p, self.filetypes)]

    def valid_path(self, e):
        if e.mimeData().hasUrls():
            path = Path(e.mimeData().urls()[0].toLocalFile())
            if self.filetypes is None and path.is_file():
                return path
            if check_file_type(path, self.filetypes):
                return path

    def dragEnterEvent(self, e):
        if self.valid_paths(e):
            e.acceptProposedAction()
            e.setDropAction(QtCore.Qt.LinkAction)
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if self.valid_paths(e):
            e.acceptProposedAction()
            e.setDropAction(QtCore.Qt.LinkAction)
        else:
            super().dragMoveEvent(e)

    def dropEvent(self, e):
        if paths := self.valid_paths(e):
            for p in paths:
                self.item_dropped.emit(p)
            e.accept()
        else:
            super().dropEvent(e)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = DroppableWidget(filetypes=["image"])
    widget.show()

    app.exec()
