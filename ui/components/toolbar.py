from PyQt5.QtCore import QObject, pyqtSignal, QStringListModel
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCompleter


class Toolbar(QWidget):
    """Barra de tareas superior con botones de acción principal."""
    
    # Señales para comunicarse con el viewer principal
    load_folder_requested = pyqtSignal()
    update_folder_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la barra de tareas."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Botón para cargar carpeta
        self.btn_load = QPushButton("Cargar Carpeta")
        self.btn_load.clicked.connect(self._on_load_folder_clicked)
        layout.addWidget(self.btn_load)
        
        # Botón para actualizar carpeta
        self.btn_update_folder = QPushButton("Actualizar Carpeta")
        self.btn_update_folder.clicked.connect(self._on_update_folder_clicked)
        layout.addWidget(self.btn_update_folder)
        
        # Espaciador para empujar los botones a la izquierda
        layout.addStretch()
    
    def _on_load_folder_clicked(self):
        """Emite señal cuando se hace clic en Cargar Carpeta."""
        self.load_folder_requested.emit()
    
    def _on_update_folder_clicked(self):
        """Emite señal cuando se hace clic en Actualizar Carpeta."""
        self.update_folder_requested.emit()
