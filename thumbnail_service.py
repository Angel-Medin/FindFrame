from PyQt5.QtCore import QObject, Qt, pyqtSignal
from pathlib import Path
from PyQt5.QtGui import QPixmap


class ThumbnailWorker(QObject):
    # Señales para comunicarse con el hilo principal de la GUI
    thumbnail_ready = pyqtSignal(Path, QPixmap, int)  # Envía la ruta, el pixmap y el índice de la miniatura
    finished = pyqtSignal()                         # Indica que ha terminado el proceso

    def __init__(self, image_paths, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.is_running = True

    # El método principal que se ejecutará en el hilo secundario
    def process_thumbnails(self):
        """
        Procesa cada ruta de imagen, genera/carga la miniatura y emite una señal.
        """
        errores_log = Path.cwd() / "errores.txt"
        
        for index, path in enumerate(self.image_paths):
            if not self.is_running:
                break # Permite detener el proceso si se carga una nueva carpeta

            if not path.exists():
                with open(errores_log, "a", encoding="utf-8") as f:
                    f.write(f"No existe: {path}\n")
                continue

            thumb_folder = path.parent / ".thumbnails"
            thumb_folder.mkdir(parents=True, exist_ok=True)
            thumb_path = thumb_folder / path.name

            thumbnail = None
            if thumb_path.exists():
                thumbnail = QPixmap(str(thumb_path))
                if thumbnail.isNull(): # Cache corrupta
                    thumbnail = None

            if thumbnail is None:
                original_pixmap = QPixmap(str(path))
                if original_pixmap.isNull():
                    with open(errores_log, "a", encoding="utf-8") as f:
                        f.write(f"No pudo cargarse: {path}\n")
                    continue
                thumbnail = original_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.FastTransformation)
                thumbnail.save(str(thumb_path))
            
            # Emite la señal con los datos listos para que la GUI los use
            self.thumbnail_ready.emit(path, thumbnail, index)
            
        self.finished.emit()

    def stop(self):
        self.is_running = False
