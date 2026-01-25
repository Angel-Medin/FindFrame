from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QFrame
from PyQt5.QtGui import QPixmap
from pathlib import Path


class ThumbnailPanel(QWidget):
    """Panel lateral izquierdo con miniaturas de imágenes con lazy loading."""
    
    thumbnail_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_labels = []
        self.image_paths = []
        self.loaded_indices = set()  # Índices ya cargados
        
        # Configuración de lazy loading
        self.buffer_size = 15  # Cantidad de thumbnails a precargar fuera del viewport
        self.thumbnails_per_row = 3
        self.thumbnail_size = 100
        
        self._setup_ui()
        
        # Timer para evitar cargas excesivas durante scroll rápido
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._load_visible_thumbnails)
        
    def _setup_ui(self):
        """Configura la interfaz del panel de miniaturas."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de scroll para las miniaturas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(320)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        
        # Conectar evento de scroll
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)
        
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
    
    def set_images(self, images):
        """
        Establece la lista de imágenes y crea placeholders.
        No carga las miniaturas inmediatamente.
        """
        self.clear_thumbnails()
        self.image_paths = images
        self.loaded_indices.clear()
        
        # Crear placeholders para todas las imágenes
        for index in range(len(images)):
            self._create_placeholder(index)
        
        # Cargar las primeras miniaturas visibles
        QTimer.singleShot(100, self._load_visible_thumbnails)
    
    def _create_placeholder(self, index):
        """Crea un placeholder vacío para una miniatura."""
        thumb_label = QLabel()
        thumb_label.setFixedSize(self.thumbnail_size, self.thumbnail_size)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setFrameShape(QFrame.Box)
        thumb_label.setStyleSheet("background-color: #e0e0e0;")
        thumb_label.setText("...")
        
        thumb_label.setProperty("image_index", index)
        thumb_label.setProperty("image_path", self.image_paths[index])
        thumb_label.mousePressEvent = lambda event, idx=index: self._on_thumbnail_clicked(idx)
        
        row, col = divmod(index, self.thumbnails_per_row)
        self.scroll_layout.addWidget(thumb_label, row, col, Qt.AlignCenter)
        self.thumbnail_labels.append(thumb_label)
    
    def _on_scroll(self):
        """Maneja el evento de scroll con debounce."""
        # Reiniciar el timer cada vez que hay scroll
        self.scroll_timer.start(150)  # 150ms de debounce
    
    def _load_visible_thumbnails(self):
        """Carga las miniaturas visibles + buffer."""
        if not self.image_paths:
            return
        
        # Calcular rango visible
        viewport_rect = self.scroll_area.viewport().rect()
        visible_indices = self._get_visible_indices(viewport_rect)
        
        if not visible_indices:
            return
        
        # Añadir buffer (thumbnails arriba y abajo del viewport)
        start_index = max(0, min(visible_indices) - self.buffer_size)
        end_index = min(len(self.image_paths), max(visible_indices) + self.buffer_size + 1)
        
        # Debug (opcional, puedes comentar después)
        # print(f"Visible: {min(visible_indices)}-{max(visible_indices)}, Loading: {start_index}-{end_index}")
        
        # Cargar solo las que no están cargadas
        for index in range(start_index, end_index):
            if index not in self.loaded_indices:
                self._load_thumbnail(index)
    
    def _get_visible_indices(self, viewport_rect):
        """Determina qué índices de thumbnails están visibles."""
        visible_indices = []
        
        # Obtener la posición del scroll
        scroll_y = self.scroll_area.verticalScrollBar().value()
        viewport_top = scroll_y
        viewport_bottom = scroll_y + viewport_rect.height()
        
        for index, thumb_label in enumerate(self.thumbnail_labels):
            # Obtener la posición global del widget en el scroll_widget
            widget_global_pos = thumb_label.pos()
            widget_top = widget_global_pos.y()
            widget_bottom = widget_top + thumb_label.height()
            
            # Verificar si el widget está dentro del viewport
            if widget_bottom >= viewport_top and widget_top <= viewport_bottom:
                visible_indices.append(index)
        
        return visible_indices if visible_indices else [0]
    
    def _load_thumbnail(self, index):
        """Carga una miniatura específica de forma síncrona."""
        if index >= len(self.image_paths) or index in self.loaded_indices:
            return
        
        path = self.image_paths[index]
        
        # Intentar cargar desde cache
        thumb_folder = path.parent / ".thumbnails"
        thumb_path = thumb_folder / path.name
        
        thumbnail = None
        if thumb_path.exists():
            thumbnail = QPixmap(str(thumb_path))
            if thumbnail.isNull():
                thumbnail = None
        
        # Si no hay cache, generar thumbnail
        if thumbnail is None:
            original_pixmap = QPixmap(str(path))
            if original_pixmap.isNull():
                return
            
            thumbnail = original_pixmap.scaled(
                self.thumbnail_size, 
                self.thumbnail_size, 
                Qt.KeepAspectRatio, 
                Qt.FastTransformation
            )
            
            # Guardar en cache
            thumb_folder.mkdir(parents=True, exist_ok=True)
            thumbnail.save(str(thumb_path))
        
        # Actualizar el label
        if index < len(self.thumbnail_labels):
            thumb_label = self.thumbnail_labels[index]
            thumb_label.setPixmap(thumbnail)
            thumb_label.setText("")
            thumb_label.setStyleSheet("")
            self.loaded_indices.add(index)
    
    def clear_thumbnails(self):
        """Limpia todas las miniaturas del layout."""
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.thumbnail_labels = []
        self.image_paths = []
        self.loaded_indices.clear()
    
    def highlight_thumbnail(self, current_image_path):
        """Resalta la miniatura de la imagen actual."""
        if current_image_path is None:
            return
        
        for thumb_label in self.thumbnail_labels:
            if thumb_label.property("image_path") == current_image_path:
                thumb_label.setStyleSheet("border: 5px solid red;")
                self.scroll_area.ensureWidgetVisible(thumb_label)
                
                # Asegurar que la miniatura actual esté cargada
                index = thumb_label.property("image_index")
                if index not in self.loaded_indices:
                    self._load_thumbnail(index)
            else:
                # Solo resetear estilo si ya está cargado
                index = thumb_label.property("image_index")
                if index in self.loaded_indices:
                    thumb_label.setStyleSheet("")
    
    def _on_thumbnail_clicked(self, index):
        """Emite señal cuando se hace clic en una miniatura."""
        self.thumbnail_clicked.emit(index)
    
    def preload_around_index(self, index):
        """Precarga thumbnails alrededor de un índice específico."""
        start = max(0, index - self.buffer_size)
        end = min(len(self.image_paths), index + self.buffer_size + 1)
        
        for i in range(start, end):
            if i not in self.loaded_indices:
                self._load_thumbnail(i)