from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLineEdit, 
                             QSpinBox, QLabel, QComboBox, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class Toolbar(QWidget):
    """Barra de tareas superior con botones de acción principal."""
    
    # Señales para comunicarse con el viewer principal
    load_folder_requested = pyqtSignal()
    update_folder_requested = pyqtSignal()
    toggle_guides_requested = pyqtSignal(bool)
    lock_guides_requested = pyqtSignal(bool)
    guide_mode_changed = pyqtSignal(str)
    clear_guides_requested = pyqtSignal()
    toggle_grid_requested = pyqtSignal(bool)
    grid_spacing_changed = pyqtSignal(int)
    grid_color_changed = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._grid_color = QColor(100, 100, 255, 150)
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
        
        # Separador visual
        layout.addWidget(QLabel("|"))
        
        # Botón para activar/desactivar guías
        self.btn_toggle_guides = QPushButton("Activar Guías")
        self.btn_toggle_guides.setCheckable(True)
        self.btn_toggle_guides.clicked.connect(self._on_toggle_guides)
        layout.addWidget(self.btn_toggle_guides)
        
        # Selector de tipo de guía
        layout.addWidget(QLabel("Tipo:"))
        self.combo_guide_mode = QComboBox()
        self.combo_guide_mode.addItems(["Vertical", "Horizontal"])
        self.combo_guide_mode.currentTextChanged.connect(self._on_guide_mode_changed)
        layout.addWidget(self.combo_guide_mode)
        
        # Botón para bloquear/desbloquear guías
        self.btn_lock_guides = QPushButton("🔓 Desbloqueado")
        self.btn_lock_guides.setCheckable(True)
        self.btn_lock_guides.setChecked(False)
        self.btn_lock_guides.clicked.connect(self._on_lock_guides)
        self.btn_lock_guides.setToolTip("Bloquear guías para permitir zoom y pan")
        layout.addWidget(self.btn_lock_guides)
        
        # Botón para limpiar guías
        self.btn_clear_guides = QPushButton("Limpiar Guías")
        self.btn_clear_guides.clicked.connect(self._on_clear_guides)
        layout.addWidget(self.btn_clear_guides)
        
        # Separador visual
        layout.addWidget(QLabel("|"))
        
        # Botón para activar/desactivar grilla
        self.btn_toggle_grid = QPushButton("Activar Grilla")
        self.btn_toggle_grid.setCheckable(True)
        self.btn_toggle_grid.clicked.connect(self._on_toggle_grid)
        layout.addWidget(self.btn_toggle_grid)
        
        # Control para espaciado de grilla
        layout.addWidget(QLabel("Espaciado:"))
        self.spin_grid_spacing = QSpinBox()
        self.spin_grid_spacing.setMinimum(10)
        self.spin_grid_spacing.setMaximum(500)
        self.spin_grid_spacing.setValue(50)
        self.spin_grid_spacing.setSuffix(" px")
        self.spin_grid_spacing.valueChanged.connect(self._on_grid_spacing_changed)
        layout.addWidget(self.spin_grid_spacing)
        
        # Botón para elegir color de grilla
        self.btn_grid_color = QPushButton("Color Grilla")
        self.btn_grid_color.clicked.connect(self._on_choose_grid_color)
        self._update_grid_color_button()
        layout.addWidget(self.btn_grid_color)
        
        # Espaciador para empujar los botones a la izquierda
        layout.addStretch()
    
    def _on_load_folder_clicked(self):
        """Emite señal cuando se hace clic en Cargar Carpeta."""
        self.load_folder_requested.emit()
    
    def _on_update_folder_clicked(self):
        """Emite señal cuando se hace clic en Actualizar Carpeta."""
        self.update_folder_requested.emit()
    
    def _on_toggle_guides(self, checked):
        """Emite señal cuando se activan/desactivan las guías."""
        self.btn_toggle_guides.setText("Desactivar Guías" if checked else "Activar Guías")
        self.toggle_guides_requested.emit(checked)
    
    def _on_lock_guides(self, checked):
        """Emite señal cuando se bloquean/desbloquean las guías."""
        self.btn_lock_guides.setText("🔒 Bloqueado" if checked else "🔓 Desbloqueado")
        self.lock_guides_requested.emit(checked)
    
    def _on_guide_mode_changed(self, text):
        """Emite señal cuando cambia el modo de guía."""
        mode = 'vertical' if text == 'Vertical' else 'horizontal'
        self.guide_mode_changed.emit(mode)
    
    def _on_clear_guides(self):
        """Emite señal para limpiar todas las guías."""
        self.clear_guides_requested.emit()
    
    def _on_toggle_grid(self, checked):
        """Emite señal cuando se activa/desactiva la grilla."""
        self.btn_toggle_grid.setText("Desactivar Grilla" if checked else "Activar Grilla")
        self.toggle_grid_requested.emit(checked)
    
    def _on_grid_spacing_changed(self, value):
        """Emite señal cuando cambia el espaciado de la grilla."""
        self.grid_spacing_changed.emit(value)
    
    def _on_choose_grid_color(self):
        """Abre un diálogo para elegir el color de la grilla."""
        color = QColorDialog.getColor(
            self._grid_color,
            self,
            "Seleccionar Color de Grilla",
            QColorDialog.ShowAlphaChannel
        )
        
        if color.isValid():
            self._grid_color = color
            self._update_grid_color_button()
            self.grid_color_changed.emit(color)
    
    def _update_grid_color_button(self):
        """Actualiza el color de fondo del botón de color."""
        self.btn_grid_color.setStyleSheet(
            f"background-color: rgba({self._grid_color.red()}, "
            f"{self._grid_color.green()}, "
            f"{self._grid_color.blue()}, "
            f"{self._grid_color.alpha()});"
        )


        