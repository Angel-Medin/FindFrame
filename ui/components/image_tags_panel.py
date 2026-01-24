from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListWidget, 
                             QLineEdit, QPushButton, QCompleter)


class ImageTagsPanel(QWidget):
    """Panel lateral derecho para gestión de etiquetas."""
    
    # Señales para comunicarse con el viewer principal
    tag_added = pyqtSignal(list)  # lista de tags a agregar
    tag_removed = pyqtSignal(str)  # tag a eliminar
    open_external_requested = pyqtSignal()
    
    def __init__(self, tag_model: QStringListModel, setup_autocomplete_callback, parent=None):
        super().__init__(parent)
        self.tag_model = tag_model
        self.setup_autocomplete_callback = setup_autocomplete_callback
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del panel de etiquetas."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        self.tag_title = QLabel("Etiquetas de la imagen", alignment=Qt.AlignCenter)
        layout.addWidget(self.tag_title)
        
        # Lista de etiquetas
        self.tag_list = QListWidget()
        layout.addWidget(self.tag_list)
        
        # Input para nueva etiqueta
        self.new_tag_input = QLineEdit()
        self.setup_autocomplete_callback(self.new_tag_input)
        self.new_tag_input.setPlaceholderText("Nueva etiqueta")
        layout.addWidget(self.new_tag_input)
        
        # Botón agregar etiqueta
        self.btn_add_tag = QPushButton("Agregar Etiqueta")
        self.btn_add_tag.clicked.connect(self._on_add_tag_clicked)
        layout.addWidget(self.btn_add_tag)
        
        # Botón eliminar etiqueta
        self.btn_remove_tag = QPushButton("Eliminar Etiqueta")
        self.btn_remove_tag.clicked.connect(self._on_remove_tag_clicked)
        layout.addWidget(self.btn_remove_tag)
        
        # Botón abrir ubicación
        self.btn_open_external = QPushButton("Abrir Ubicación")
        self.btn_open_external.clicked.connect(self._on_open_external_clicked)
        layout.addWidget(self.btn_open_external)
    
    def _on_add_tag_clicked(self):
        """Emite señal cuando se hace clic en Agregar Etiqueta."""
        new_tags_raw = self.new_tag_input.text().strip()
        tags_to_add = [t.strip() for t in new_tags_raw.split(',') if t.strip()]
        
        if tags_to_add:
            self.tag_added.emit(tags_to_add)
            self.new_tag_input.clear()
    
    def _on_remove_tag_clicked(self):
        """Emite señal cuando se hace clic en Eliminar Etiqueta."""
        selected_items = self.tag_list.selectedItems()
        
        if selected_items:
            tag_to_remove = selected_items[0].text()
            self.tag_removed.emit(tag_to_remove)
    
    def _on_open_external_clicked(self):
        """Emite señal cuando se hace clic en Abrir Ubicación."""
        self.open_external_requested.emit()
    
    def update_tag_list(self, tags: list):
        """Actualiza la lista de etiquetas mostradas."""
        self.tag_list.clear()
        for tag in tags:
            self.tag_list.addItem(tag)
    
    def clear_tag_list(self):
        """Limpia la lista de etiquetas."""
        self.tag_list.clear()
