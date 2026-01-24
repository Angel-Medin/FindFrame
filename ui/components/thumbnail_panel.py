from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QFrame
from PyQt5.QtGui import QPixmap
from services.thumbnail_service import ThumbnailWorker


class ThumbnailPanel(QWidget):
    """Panel lateral izquierdo con miniaturas de imágenes."""
    
    # Señal para notificar cuando se hace clic en una miniatura
    thumbnail_clicked = pyqtSignal(int)  # index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_labels = []
        self.thread = None
        self.worker = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del panel de miniaturas."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de scroll para las miniaturas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(320)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)
        
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
    
    def load_thumbnails_threaded(self, images):
        """Carga las miniaturas en un hilo separado."""
        # Detener el hilo anterior si todavía está en ejecución
        if self.thread is not None and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait()
        
        self.clear_thumbnails()
        
        self.thread = QThread()
        self.worker = ThumbnailWorker(images)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.process_thumbnails)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_thread_references)
        
        self.worker.thumbnail_ready.connect(self.add_thumbnail)
        self.thread.start()
    
    def _clear_thread_references(self):
        """Limpia las referencias al hilo y al worker una vez que han terminado."""
        self.worker = None
        self.thread = None
    
    def add_thumbnail(self, path, pixmap, index):
        """Añade una miniatura al grid."""
        thumb_label = QLabel()
        thumb_label.setFixedSize(100, 100)
        thumb_label.setPixmap(pixmap)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setFrameShape(QFrame.Box)
        
        thumb_label.setProperty("image_path", path)
        thumb_label.mousePressEvent = lambda event, idx=index: self._on_thumbnail_clicked(idx)
        
        row, col = divmod(len(self.thumbnail_labels), 3)
        self.scroll_layout.addWidget(thumb_label, row, col, Qt.AlignCenter)
        self.thumbnail_labels.append(thumb_label)
    
    def clear_thumbnails(self):
        """Limpia todas las miniaturas del layout."""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.thumbnail_labels = []
    
    def highlight_thumbnail(self, current_image_path):
        """Resalta la miniatura de la imagen actual."""
        if current_image_path is None:
            return
        
        for thumb_label in self.thumbnail_labels:
            if thumb_label.property("image_path") == current_image_path:
                thumb_label.setStyleSheet("border: 5px solid red;")
                self.scroll_area.ensureWidgetVisible(thumb_label)
            else:
                thumb_label.setStyleSheet("")
    
    def _on_thumbnail_clicked(self, index):
        """Emite señal cuando se hace clic en una miniatura."""
        self.thumbnail_clicked.emit(index)
