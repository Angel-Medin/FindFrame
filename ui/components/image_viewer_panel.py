from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QScrollArea
from PyQt5.QtGui import QPixmap
from pathlib import Path


from ui.components.zoomable_image_label import ZoomableImageLabel

class ImageViewerPanel(QWidget):
    """Panel central con el visor de imagen y controles de navegación."""
    
    # Señales para comunicarse con el viewer principal
    next_requested = pyqtSignal()
    previous_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del panel central."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de scroll para la imagen con zoom
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False) # Importante para permitir que el label crezca
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #f0f0f0;") # Fondo gris claro
        
        # Label principal para mostrar la imagen (ahora Zoomable)
        self.image_label = ZoomableImageLabel()
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setMinimumSize(100, 100)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # Label para el nombre del archivo
        self.filename_label = QLabel("", alignment=Qt.AlignCenter)
        self.filename_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.filename_label.setMaximumHeight(40)
        layout.addWidget(self.filename_label)
        
        # Botones de navegación
        nav_layout = QHBoxLayout()
        
        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.clicked.connect(self._on_previous_clicked)
        self.btn_prev.setEnabled(False)
        nav_layout.addWidget(self.btn_prev)
        
        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.clicked.connect(self._on_next_clicked)
        self.btn_next.setEnabled(False)
        nav_layout.addWidget(self.btn_next)
        
        layout.addLayout(nav_layout)
    
    def _on_next_clicked(self):
        """Emite señal cuando se hace clic en Siguiente."""
        self.next_requested.emit()
    
    def _on_previous_clicked(self):
        """Emite señal cuando se hace clic en Anterior."""
        self.previous_requested.emit()
    
    def set_image(self, pixmap: QPixmap):
        """Establece la imagen a mostrar."""
        self.image_label.setPixmap(pixmap)
    
    def set_loading_text(self, text: str = "Cargando imagen..."):
        """Muestra un texto de carga."""
        self.image_label.setText(text)
    
    def set_filename(self, filename: str, current_index: int, total: int):
        """Establece el nombre del archivo y el contador."""
        self.filename_label.setText(f"{filename} ({current_index + 1}/{total})")
    
    def set_navigation_enabled(self, can_previous: bool, can_next: bool):
        """Habilita o deshabilita los botones de navegación."""
        self.btn_prev.setEnabled(can_previous)
        self.btn_next.setEnabled(can_next)
    
    def get_image_label_size(self):
        """Retorna el tamaño disponible en el viewport para la carga asíncrona."""
        # Solicitamos una imagen del tamaño del área visible, no del label (que puede ser pequeño)
        if self.scroll_area.viewport().size().isEmpty():
             return self.size() # Fallback si el área no está lista
        return self.scroll_area.viewport().size()
