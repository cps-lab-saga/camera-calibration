from pathlib import Path

import qtawesome as qta

from camera_calibration.defs import QtWidgets, Signal
from camera_calibration.funcs import get_extensions_for_type


class MenuBar(QtWidgets.QMenuBar):
    open_image_file = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.file_menu = self.addMenu("File")

        self.open_image_file_action = self.file_menu.addAction(
            qta.icon("mdi6.file-image"), "Open Image File..."
        )
        self.open_image_file_action.triggered.connect(self.add_file)

        self.open_image_folder_action = self.file_menu.addAction(
            qta.icon("mdi6.folder-open"), "Open Image Folder..."
        )
        self.open_image_folder_action.triggered.connect(self.add_folder)

    def add_file(self):
        extensions = [f"*{x}" for x, _ in get_extensions_for_type("image")]
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Open Image File",
            None,
            f"Image Files ({' '.join(extensions)})",
        )
        if file_names:
            for file_path in file_names:
                self.open_image_file.emit(Path(file_path))

    def add_folder(self):
        folder_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open Image Folder",
        )
        if folder_name:
            for file_path in Path(folder_name).glob("*"):
                self.open_image_file.emit(file_path)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    main_window = QtWidgets.QMainWindow()
    main_menu = MenuBar(main_window)
    main_window.setMenuBar(main_menu)
    main_window.show()

    app.exec()
