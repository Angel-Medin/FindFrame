from pathlib import Path
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from collections import OrderedDict
from PyQt5.QtCore import QThread
from services.image_load_worker import ImageLoadWorker
from PyQt5.QtCore import pyqtSignal, QObject

class ImageLoaderService(QObject):
    preview_ready = pyqtSignal(Path, QPixmap)

    def __init__(self):
        super().__init__()


        # Cache en memoria
        self._preview_cache: OrderedDict[tuple[Path, int, int],QPixmap] = OrderedDict()
        self._max_cache_items = 50


        self._thread = QThread()
        self._worker = ImageLoadWorker()
        self._worker.moveToThread(self._thread)
        self._thread.start()

        self._worker.finished.connect(self._on_worker_finished) 

    # ---------- API pública ----------

    def get_preview(self, path: Path, target_size) -> QPixmap | None:
        if target_size.width() <= 0 or target_size.height() <= 0:
            return None

        key = (path, target_size.width(), target_size.height())

        if key in self._preview_cache:
            self._preview_cache.move_to_end(key)
            return self._preview_cache[key]

        pixmap = self._load_pixmap(path)
        if pixmap is None:
            return None

        scaled = pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self._add_to_cache(key, scaled)
        return scaled



    def get_full(self, path: Path) -> QPixmap | None:
        """
        Devuelve la imagen original sin escalar.
        No usa cache.
        """
        return self._load_pixmap(path)

    def invalidate(self, path: Path):
        """Invalida cache de una imagen concreta."""
        keys_to_remove = [k for k in self._preview_cache if k[0] == path]
        for k in keys_to_remove:
            self._preview_cache.pop(k, None)

    def clear_cache(self):
        """Limpia todo el cache en memoria."""
        self._preview_cache.clear()

    # ---------- Interno ----------

    def _load_pixmap(self, path: Path) -> QPixmap | None:
        if not path.exists():
            return None

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None

        return pixmap


    def preload_preview(self, path: Path, target_size):
        if path is None:
            return

        key = (path, target_size.width(), target_size.height())
        if key in self._preview_cache:
            return

        pixmap = self._load_pixmap(path)
        if pixmap is None:
            return

        scaled = pixmap.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self._add_to_cache(key, scaled)




    def _add_to_cache(self, key, pixmap):
        self._preview_cache[key] = pixmap
        self._preview_cache.move_to_end(key)

        if len(self._preview_cache) > self._max_cache_items:
            self._preview_cache.popitem(last=False)


    def _on_worker_finished(self, path, size, pixmap):
        key = (path, size.width(), size.height())
        self._add_to_cache(key, pixmap)
        self.preview_ready.emit(path, pixmap)


    def request_preview_async(self, path: Path, target_size):
        key = (path, target_size.width(), target_size.height())

        if key in self._preview_cache:
            self.preview_ready.emit(path, self._preview_cache[key])
            return

        self._worker.load(path, target_size)
    