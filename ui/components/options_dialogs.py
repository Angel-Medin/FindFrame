from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt


class BulkTagDialog(QDialog):
    """Diálogo para agregar un tag masivo a todas las imágenes de una carpeta."""
    
    def __init__(self, tag_model, setup_autocomplete_func, parent=None):
        super().__init__(parent)
        self.tag_model = tag_model
        self.setup_autocomplete_func = setup_autocomplete_func
        self.folder_path = None
        self.tag = None
        
        self.setWindowTitle("Agregar Tag a Carpeta")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Carpeta:"))
        self.folder_label = QLabel("(Ninguna seleccionada)")
        self.folder_label.setStyleSheet("color: gray;")
        folder_layout.addWidget(self.folder_label, 1)
        
        btn_browse = QPushButton("Seleccionar...")
        btn_browse.clicked.connect(self._select_folder)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)
        
        # Campo de tag con autocompleter
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tag a agregar:"))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Ingrese el tag")
        self.setup_autocomplete_func(self.tag_input)
        tag_layout.addWidget(self.tag_input, 1)
        layout.addLayout(tag_layout)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(self._on_accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
    
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.folder_label.setStyleSheet("")
    
    def _on_accept(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Error", "Debe seleccionar una carpeta.")
            return
        
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "Error", "Debe ingresar un tag.")
            return
        
        self.tag = tag
        self.accept()


class RenameImagesDialog(QDialog):
    """Diálogo para renombrar imágenes agregando un prefijo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.folder_path = None
        self.prefix = None
        
        self.setWindowTitle("Renombrar Imágenes con Prefijo")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Selector de carpeta
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Carpeta:"))
        self.folder_label = QLabel("(Ninguna seleccionada)")
        self.folder_label.setStyleSheet("color: gray;")
        folder_layout.addWidget(self.folder_label, 1)
        
        btn_browse = QPushButton("Seleccionar...")
        btn_browse.clicked.connect(self._select_folder)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)
        
        # Campo de prefijo
        prefix_layout = QHBoxLayout()
        prefix_layout.addWidget(QLabel("Prefijo:"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("ej: nueva_version")
        self.prefix_input.textChanged.connect(self._update_preview)
        prefix_layout.addWidget(self.prefix_input, 1)
        layout.addLayout(prefix_layout)
        
        # Vista previa
        self.preview_label = QLabel("Vista previa: imagen.jpg → <prefijo>_imagen.jpg")
        self.preview_label.setStyleSheet("color: blue; font-style: italic;")
        layout.addWidget(self.preview_label)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(self._on_accept)
        btn_ok.setDefault(True)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
    
    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if folder:
            self.folder_path = folder
            self.folder_label.setText(folder)
            self.folder_label.setStyleSheet("")
            self._update_preview()
    
    def _update_preview(self):
        prefix = self.prefix_input.text().strip()
        if prefix:
            self.preview_label.setText(f"Vista previa: imagen.jpg → {prefix}_imagen.jpg")
        else:
            self.preview_label.setText("Vista previa: imagen.jpg → <prefijo>_imagen.jpg")
    
    def _on_accept(self):
        if not self.folder_path:
            QMessageBox.warning(self, "Error", "Debe seleccionar una carpeta.")
            return
        
        prefix = self.prefix_input.text().strip()
        if not prefix:
            QMessageBox.warning(self, "Error", "Debe ingresar un prefijo.")
            return
        
        # Validar caracteres no permitidos en nombres de archivo
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        if any(char in prefix for char in invalid_chars):
            QMessageBox.warning(self, "Error", 
                              f"El prefijo contiene caracteres no permitidos: {', '.join(invalid_chars)}")
            return
        
        # Confirmación adicional
        reply = QMessageBox.question(
            self, 
            "Confirmar Renombrado",
            f"¿Está seguro de renombrar todas las imágenes de la carpeta con el prefijo '{prefix}'?\n\n"
            "Esta operación modificará los nombres de archivo en el sistema.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.prefix = prefix
            self.accept()


class DeleteTagDialog(QDialog):
    """Diálogo para eliminar un tag de la base de datos."""
    
    def __init__(self, tag_model, setup_autocomplete_func, count_func, parent=None):
        super().__init__(parent)
        self.tag_model = tag_model
        self.setup_autocomplete_func = setup_autocomplete_func
        self.count_func = count_func  # Función para contar imágenes con el tag
        self.tag_to_delete = None
        
        self.setWindowTitle("Eliminar Tag de Base de Datos")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Advertencia
        warning_label = QLabel("⚠️ ADVERTENCIA: Esta acción es IRREVERSIBLE")
        warning_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        layout.addWidget(warning_label)
        
        # Campo de tag con autocompleter
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("Tag a eliminar:"))
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Seleccione o ingrese el tag")
        self.setup_autocomplete_func(self.tag_input)
        self.tag_input.textChanged.connect(self._update_count)
        tag_layout.addWidget(self.tag_input, 1)
        layout.addLayout(tag_layout)
        
        # Información de imágenes afectadas
        self.info_label = QLabel("Ingrese un tag para ver cuántas imágenes serán afectadas")
        self.info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.info_label)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_ok = QPushButton("Eliminar Tag")
        btn_ok.clicked.connect(self._on_accept)
        btn_ok.setStyleSheet("background-color: #d32f2f; color: white;")
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
    
    def _update_count(self):
        tag = self.tag_input.text().strip()
        if tag:
            count = self.count_func(tag)
            if count > 0:
                self.info_label.setText(
                    f"Este tag está asociado a {count} imagen(es). "
                    f"Se eliminará de todas ellas y del autocompleter."
                )
                self.info_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.info_label.setText("Este tag no existe en la base de datos.")
                self.info_label.setStyleSheet("color: gray; font-style: italic;")
        else:
            self.info_label.setText("Ingrese un tag para ver cuántas imágenes serán afectadas")
            self.info_label.setStyleSheet("color: gray; font-style: italic;")
    
    def _on_accept(self):
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "Error", "Debe ingresar un tag.")
            return
        
        count = self.count_func(tag)
        if count == 0:
            QMessageBox.information(self, "Información", 
                                  "El tag ingresado no existe en la base de datos.")
            return
        
        # Confirmación final
        reply = QMessageBox.question(
            self,
            "Confirmación Final",
            f"¿Está ABSOLUTAMENTE SEGURO de eliminar el tag '{tag}'?\n\n"
            f"Se eliminará de {count} imagen(es) y del autocompleter.\n"
            f"Esta operación NO SE PUEDE DESHACER.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tag_to_delete = tag
            self.accept()
