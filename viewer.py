from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QLabel, QFileDialog,
    QVBoxLayout, QWidget, QHBoxLayout, QScrollArea,
    QFrame, QListWidget, QLineEdit, QSizePolicy
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from image_loader import get_image_paths
from tag_manager import TagManagerSQLite

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Imágenes (Final)")
        self.setGeometry(100, 100, 1000, 700)
        self.image_paths = []   # Se guardan objetos Path
        self.index = 0
        self.thumbnail_labels = []
        self.tag_manager = TagManagerSQLite()
        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Botón para cargar carpeta
        self.btn_load = QPushButton("📂 Cargar Carpeta")
        self.btn_load.clicked.connect(self.load_folder)
        self.main_layout.addWidget(self.btn_load)

        # Filtros: campos para etiquetas positivas y negativas, y botón para aplicar filtro.
        self.filter_layout = QHBoxLayout()
        self.positive_tags_input = QLineEdit()
        self.positive_tags_input.setPlaceholderText("Etiquetas positivas (separadas por comas)")
        self.filter_layout.addWidget(self.positive_tags_input)
        self.negative_tags_input = QLineEdit()
        self.negative_tags_input.setPlaceholderText("Etiquetas negativas (separadas por comas)")
        self.filter_layout.addWidget(self.negative_tags_input)
        self.btn_apply_filters = QPushButton("Aplicar Filtros")
        self.btn_apply_filters.clicked.connect(self.apply_filters)
        self.filter_layout.addWidget(self.btn_apply_filters)
        self.main_layout.addLayout(self.filter_layout)

        # Layout principal dividido en dos secciones: izquierda (imagen, navegación, miniaturas) y derecha (etiquetas)
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # Sección izquierda
        self.left_layout = QVBoxLayout()
        self.content_layout.addLayout(self.left_layout, 3)

        self.image_label = QLabel("No hay imagen cargada", alignment=Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setMinimumSize(100,100)
        self.left_layout.addWidget(self.image_label)

        self.filename_label = QLabel("", alignment=Qt.AlignCenter)
        self.filename_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.filename_label.setMaximumHeight(40)
        self.left_layout.addWidget(self.filename_label)

        self.nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.clicked.connect(self.show_previous)
        self.btn_prev.setEnabled(False)
        self.nav_layout.addWidget(self.btn_prev)
        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.clicked.connect(self.show_next)
        self.btn_next.setEnabled(False)
        self.nav_layout.addWidget(self.btn_next)
        self.left_layout.addLayout(self.nav_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(120)
        self.scroll_widget = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.left_layout.addWidget(self.scroll_area)

        # Sección derecha: gestión de etiquetas
        self.right_layout = QVBoxLayout()
        self.content_layout.addLayout(self.right_layout, 1)
        self.tag_title = QLabel("Etiquetas de la imagen", alignment=Qt.AlignCenter)
        self.right_layout.addWidget(self.tag_title)
        self.tag_list = QListWidget()
        self.right_layout.addWidget(self.tag_list)
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("Nueva etiqueta")
        self.right_layout.addWidget(self.new_tag_input)
        self.btn_add_tag = QPushButton("Agregar Etiqueta")
        self.btn_add_tag.clicked.connect(self.add_tag)
        self.right_layout.addWidget(self.btn_add_tag)
        self.btn_remove_tag = QPushButton("Eliminar Etiqueta")
        self.btn_remove_tag.clicked.connect(self.remove_tag)
        self.right_layout.addWidget(self.btn_remove_tag)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not folder:
            return
        # Usar pathlib para obtener las rutas de imágenes
        self.image_paths = get_image_paths(Path(folder))
        if not self.image_paths:
            self.image_label.setText("📭 No se encontraron imágenes.")
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)
            return
        # Inicializamos la tabla de imágenes en la BD
        self.tag_manager.initialize_images(self.image_paths)
        self.index = 0
        self.show_image()
        self.load_thumbnails()

    def show_image(self):
        if not self.image_paths:
            return
        try:
            pixmap = QPixmap(str(self.image_paths[self.index]))
            if pixmap.isNull():
                raise ValueError("No se pudo cargar la imagen.")
        except Exception as e:
            print("Error al cargar la imagen:", e)
            self.image_label.setText("No se pudo cargar la imagen.")
            return

        self.image_label.setPixmap(
            pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self.filename_label.setText(f"{self.image_paths[self.index].name} ({self.index+1}/{len(self.image_paths)})")
        self.update_tag_list()
        self.btn_prev.setEnabled(self.index > 0)
        self.btn_next.setEnabled(self.index < len(self.image_paths) - 1)

    def show_next(self):
        if self.index < len(self.image_paths) - 1:
            self.index += 1
            self.show_image()

    def show_previous(self):
        if self.index > 0:
            self.index -= 1
            self.show_image()

    def load_thumbnails(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.thumbnail_labels = []
        for idx, path in enumerate(self.image_paths):
            thumb_label = QLabel()
            thumb_label.setFixedSize(100, 100)
            pix = QPixmap(str(path))
            if pix.isNull():
                pix = QPixmap("assets/placeholder.png")
            thumb_label.setPixmap(pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            thumb_label.setAlignment(Qt.AlignCenter)
            thumb_label.setFrameShape(QFrame.Box)
            thumb_label.mousePressEvent = lambda event, i=idx: self.thumbnail_clicked(i)
            self.scroll_layout.addWidget(thumb_label)
            self.thumbnail_labels.append(thumb_label)

    def thumbnail_clicked(self, index):
        self.index = index
        self.show_image()

    def update_tag_list(self):
        self.tag_list.clear()
        current_image = self.image_paths[self.index]
        for tag in self.tag_manager.get_tags(str(current_image)):
            self.tag_list.addItem(tag)

    def add_tag(self):
        new_tags = self.new_tag_input.text().strip()
        if not new_tags:
            return
        
        current_image = self.image_paths[self.index]
        
        # Dividir las etiquetas por comas y limpiar espacios
        tags = [tag.strip() for tag in new_tags.split(',')]
        
        # Agregar cada etiqueta individualmente
        for tag in tags:
            if tag:  # Ignorar cadenas vacías
                self.tag_manager.add_tag(str(current_image), tag)
    
        self.new_tag_input.clear()
        self.update_tag_list()

    def remove_tag(self):
        selected_items = self.tag_list.selectedItems()
        if not selected_items:
            return
        tag_to_remove = selected_items[0].text()
        current_image = self.image_paths[self.index]
        self.tag_manager.remove_tag(str(current_image), tag_to_remove)
        self.update_tag_list()

    def apply_filters(self):
        pos_text = self.positive_tags_input.text().strip()
        neg_text = self.negative_tags_input.text().strip()
        positive_tags = [tag.strip() for tag in pos_text.split(",") if tag.strip()] if pos_text else []
        negative_tags = [tag.strip() for tag in neg_text.split(",") if tag.strip()] if neg_text else []
        filtered = self.tag_manager.filter_images(positive_tags, negative_tags)
        if filtered:
            self.image_paths = [Path(p) for p in filtered]
            self.index = 0
            self.show_image()
            self.load_thumbnails()
        else:
            self.image_label.setText("No se encontraron imágenes con esos filtros.")
    
    def resizeEvent(self, event):
        """Reescala la imagen al redimensionar la ventana"""
        if self.image_paths:
            self.show_image()
        super().resizeEvent(event)

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = ImageViewer()
    window.show()
    sys.exit(app.exec_())
