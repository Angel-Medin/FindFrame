from PyQt5.QtCore import QObject, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from pathlib import Path


class ImageLoadWorker(QObject):
    finished = pyqtSignal(Path, QSize, QPixmap)

    def load(self, path: Path, size: QSize):
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return

        scaled = pixmap.scaled(
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.finished.emit(path, size, scaled)
