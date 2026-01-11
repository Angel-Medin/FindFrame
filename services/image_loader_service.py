from pathlib import Path
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize
from collections import OrderedDict
from PyQt5.QtCore import QThread
from services.image_load_worker import ImageLoadWorker
from PyQt5.QtCore import pyqtSignal, QObject

class ImageLoaderService(QObject):
    """
    Servicio único para cargar imágenes:
    - Preview (escalado al visor)
    - Thumbnails (100x100)
    - Cache LRU para ambos
    """
    # ---------- Señales ----------
    preview_ready = pyqtSignal(Path, QPixmap)
    thumbnail_ready = pyqtSignal(Path, QPixmap, int)

    def __init__(self):
        super().__init__()

        # ---------- Cache ----------
        self._preview_cache: OrderedDict[tuple[Path, int, int],QPixmap] = OrderedDict()
        self._thumb_cache = OrderedDict()

        self._max_cache_items = 50
        self._max_thumb_items = 200
        self._thumb_size = QSize(100, 100)



        # Para mapear thumbnails async
        self._pending_thumb_indexes: dict[Path, int] = {}

        # ---------- Thread ----------
        self._thread = QThread()
        self._worker = ImageLoadWorker()
        self._worker.moveToThread(self._thread)

        self._worker.finished.connect(self._on_worker_finished) 
        self._thread.start()

    # ---------- API pública ----------

    def get_preview(self, path: Path, target_size) -> QPixmap | None:
        """
        Preview sincrónico (bloquea brevemente).
        Ideal para imagen actualmente visible.
        """
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


    def request_thumbnail_async(self, path: Path, index: int):
        if path in self._thumb_cache:
            self.thumbnail_ready.emit(path, self._thumb_cache[path], index)
            return

        # 👇 guardar el índice ANTES de mandar al worker
        self._pending_thumb_indexes[path] = index
        self._worker.load(path, self._thumb_size)



    def request_preview_async(self, path: Path, target_size):
        key = (path, target_size.width(), target_size.height())

        if key in self._preview_cache:
            self.preview_ready.emit(path, self._preview_cache[key])
            return

        self._worker.load(path, target_size)

    


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
        if size == self._thumb_size:
            index = self._pending_thumb_indexes.pop(path, None)
            if index is None:
                return  # request cancelado o inválido

            self._add_thumb_to_cache(path, pixmap)
            self.thumbnail_ready.emit(path, pixmap, index)
        else:
            key = (path, size.width(), size.height())
            self._add_to_cache(key, pixmap)
            self.preview_ready.emit(path, pixmap)




    def _add_thumb_to_cache(self, path: Path, pixmap: QPixmap):
        self._thumb_cache[path] = pixmap
        self._thumb_cache.move_to_end(path)

        if len(self._thumb_cache) > self._max_thumb_items:
            self._thumb_cache.popitem(last=False)


    def shutdown(self):
        """
        Apaga el worker y el thread de forma limpia.
        Debe llamarse al cerrar la aplicación.
        """
        if self._thread.isRunning():
            # Si el worker tiene stop(), lo llamamos
            if hasattr(self._worker, "stop"):
                self._worker.stop()

            self._thread.quit()
            self._thread.wait()

    