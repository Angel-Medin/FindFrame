import os
import subprocess
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QFileDialog, QVBoxLayout, QWidget, QHBoxLayout,
                             QScrollArea, QFrame, QListWidget, QLineEdit,
                             QSizePolicy, QGridLayout)

from infrastructure.image_loader import get_image_paths
from infrastructure.tag_manager import TagManagerSQLite
from services.thumbnail_service import ThumbnailWorker
from controllers.image_controller import ImageController
from services.image_service import ImageService
from models.navigation_model import NavigationModel
from services.image_loader_service import ImageLoaderService
import logging

logger = logging.getLogger(__name__)


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Imágenes")
        self.setGeometry(100, 100, 1000, 700)
        #self.image_paths = []
        #self.index = 0
        self.thumbnail_labels = []
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.show_image)
        self.tag_manager = TagManagerSQLite()
        self.navigation = NavigationModel()
        self.image_loader = ImageLoaderService()
        self.image_service = ImageService(self.tag_manager)
        self.controller = ImageController(self.tag_manager,self.image_service)

        self.image_loader.preview_ready.connect(self._on_preview_ready)


        
        # Atributos para el hilo de carga de miniaturas
        self.thread = None
        self.worker = None

        self.setup_ui()
        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()

    def setup_ui(self):
        # ... (El resto del setup_ui es idéntico al original)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setFocusPolicy(Qt.StrongFocus)
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.central_widget.setFocus()

        # Botón para cargar carpeta
        self.btn_load = QPushButton("Cargar Carpeta")
        self.btn_load.clicked.connect(self.load_folder)
        self.main_layout.addWidget(self.btn_load)

        # Filtros
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

        # Layout principal
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

    def setup_left_panel(self):
        self.thumbnails_layout = QVBoxLayout()
        self.btn_update_folder = QPushButton("Actualizar Carpeta")
        self.thumbnails_layout.addWidget(self.btn_update_folder)
        self.btn_update_folder.clicked.connect(self.update_image_url)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedWidth(320)
        self.scroll_area.setFocusPolicy(Qt.NoFocus)
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget) # QGridLayout
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)
        self.scroll_area.setWidget(self.scroll_widget)
        self.thumbnails_layout.addWidget(self.scroll_area)
        self.content_layout.addLayout(self.thumbnails_layout, 1)

    def setup_center_panel(self):
        self.center_layout = QVBoxLayout()
        self.content_layout.addLayout(self.center_layout, 4)
        self.image_label = QLabel("No hay imagen cargada", alignment=Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setMinimumSize(100, 100)
        self.center_layout.addWidget(self.image_label)
        self.filename_label = QLabel("", alignment=Qt.AlignCenter)
        self.filename_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.filename_label.setMaximumHeight(40)
        self.center_layout.addWidget(self.filename_label)
        self.nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.clicked.connect(self.show_previous)
        self.btn_prev.setEnabled(False)
        self.nav_layout.addWidget(self.btn_prev)
        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.clicked.connect(self.show_next)
        self.btn_next.setEnabled(False)
        self.nav_layout.addWidget(self.btn_next)
        self.center_layout.addLayout(self.nav_layout)

    def setup_right_panel(self):
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
        self.btn_open_external = QPushButton("Abrir Ubicación")
        self.btn_open_external.clicked.connect(self.external_app)
        self.right_layout.addWidget(self.btn_open_external)

    def load_thumbnails_threaded(self):
        # Detener el hilo anterior si todavía está en ejecución
        # Esta comprobación ahora es segura porque `self.thread` será None si el anterior terminó.
        if self.thread is not None and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait() # Espera a que el hilo termine limpiamente

        self.clear_thumbnails_layout()

        self.thread = QThread()
        self.worker = ThumbnailWorker(self.navigation._images)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.process_thumbnails)
        self.worker.finished.connect(self.thread.quit)
        
        # Sigue siendo correcto eliminar los objetos para evitar fugas de memoria
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # --- CAMBIO CLAVE ---
        # Conectamos la señal finished a nuestro nuevo método de limpieza
        self.thread.finished.connect(self._clear_thread_references)

        self.worker.thumbnail_ready.connect(self.add_thumbnail)
        self.thread.start()
    
    def _clear_thread_references(self):
        """Slot para limpiar las referencias al hilo y al worker una vez que han terminado."""
        self.worker = None
        self.thread = None

    def add_thumbnail(self, path, pixmap, index):
        thumb_label = QLabel()
        thumb_label.setFixedSize(100, 100)
        thumb_label.setPixmap(pixmap)
        thumb_label.setAlignment(Qt.AlignCenter)
        thumb_label.setFrameShape(QFrame.Box)
        
        thumb_label.setProperty("image_path", path)
        thumb_label.mousePressEvent = lambda event, idx=index: self.thumbnail_clicked(idx)

        row, col = divmod(len(self.thumbnail_labels), 3)
        self.scroll_layout.addWidget(thumb_label, row, col, Qt.AlignCenter)
        self.thumbnail_labels.append(thumb_label)
        
        if self.navigation.current_index() == index:
            self.highlight_thumbnail()
    
    def clear_thumbnails_layout(self):
        # ... (Este método no cambia)
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.thumbnail_labels = []

    def highlight_thumbnail(self):
        current_image = self.navigation.current_image()
        if current_image is None:
            return

        for thumb_label in self.thumbnail_labels:
            if thumb_label.property("image_path") == current_image:
                thumb_label.setStyleSheet("border: 5px solid red;")
                self.scroll_area.ensureWidgetVisible(thumb_label)
            else:
                thumb_label.setStyleSheet("")


    def show_image(self):
        try:


            current_image = self.navigation.current_image()
            if current_image is None:
                return

            # Placeholder inmediato
            self.image_label.setText("Cargando imagen...")

            current_index = self.navigation.current_index()
            total = self.navigation.count()

            self.filename_label.setText(
                f"{current_image.name} ({current_index + 1}/{total})"
            )

            self.update_tag_list()
            self.btn_prev.setEnabled(self.navigation.can_previous())
            self.btn_next.setEnabled(self.navigation.can_next())
            self.highlight_thumbnail()

            # 🔥 PEDIDO ASÍNCRONO
            self.image_loader.request_preview_async(
                current_image,
                self.image_label.size()
            )

            # Preload sigue igual
            self._preload_neighbors()

        except Exception as e:
            print(f"[ImageViewer] Error en show_image: {e}")
            self.image_label.setText("Error al mostrar la imagen.")

    def show_next(self):
        self.navigation.next()
        self.show_image()

    def show_previous(self):
        self.navigation.previous()
        self.show_image()

    def thumbnail_clicked(self, index):
        self.navigation.jump_to(index)
        self.show_image()



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(100)

        # if self.image_paths:
        #     self.show_image()

    def external_app(self):
        # Obtenemos la imagen actual directamente del modelo de navegación
        current_image_path = self.navigation.current_image()
        
        if not current_image_path: 
            return
            
        # Convertimos a string para el comando de sistema
        path_str = str(current_image_path)
        
        try:
            # Usamos /select, para que Windows abra la carpeta y deje el archivo marcado
            subprocess.Popen(["explorer", "/select,", path_str])
        except Exception as e:
            print(f"Error al abrir la ubicación: {e}")
            # Intento de respaldo: abrir el archivo con la app por defecto
            try:
                os.startfile(path_str)
            except Exception as e2:
                print(f"Error crítico: {e2}")

    def keyPressEvent(self, event):
        if self.navigation.count() == 0:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key_Down:
            self.navigation.jump_relative(3)
            self.show_image()
        elif event.key() == Qt.Key_Up:
            self.navigation.jump_relative(-3)
            self.show_image()
        else:
            super().keyPressEvent(event)





    def closeEvent(self, event):
        logger.info("Cerrando aplicación")

        try:
            self.image_loader.shutdown()
        except Exception:
            logger.exception("Error al cerrar ImageLoaderService")

        super().closeEvent(event)


    def update_image_url(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not folder: return
        new_paths = get_image_paths(Path(folder))
        if not new_paths:
            self.image_label.setText("No se encontraron imágenes a actualizar.")
            return

        for path in new_paths:
            img_name = path.name
            cursor = self.tag_manager.conn.cursor()
            cursor.execute("SELECT id FROM img WHERE name = ?", (img_name,))
            if cursor.fetchone():
                self.tag_manager.update_image_url(img_name, str(path))
            else:
                self.tag_manager.initialize_images([path])

        self.navigation.set_images(new_paths)

        try:
            self.show_image()
            self.load_thumbnails_threaded() # Usamos la versión con hilos
        except Exception as e:
            print(f"Error al actualizar la carpeta: {e}")
            self.image_label.setText("Error al recargar vistas.")


    def apply_filters(self):
        pos_text = self.positive_tags_input.text().strip()
        neg_text = self.negative_tags_input.text().strip()

        positive_tags = [t.strip() for t in pos_text.split(',') if t.strip()]
        negative_tags = [t.strip() for t in neg_text.split(',') if t.strip()]

        # El controlador filtra y nos da la nueva lista
        filtered_paths = self.controller.apply_filters(
            positive_tags,
            negative_tags
        )

        # Actualizamos el modelo con los resultados del filtro
        self.navigation.set_images(filtered_paths)

        if not self.navigation.has_images():
            self.image_label.setText("No se encontraron imágenes con esos filtros.")
            self.clear_thumbnails_layout()
            # Importante: show_image no se llama si no hay imágenes para evitar errores
            self.btn_next.setEnabled(False)
            self.btn_prev.setEnabled(False)
            return

        QTimer.singleShot(0, self.show_image)
        self.load_thumbnails_threaded()



    def load_folder(self):          
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not folder:
            return

        image_paths = self.controller.load_folder(Path(folder))
        self.navigation.set_images(image_paths)

        if not self.navigation.has_images():
                self.image_label.setText("No se encontraron imágenes.")
                # Deshabilitamos botones si la carpeta está vacía
                self.btn_next.setEnabled(False)
                self.btn_prev.setEnabled(False)
                self.clear_thumbnails_layout()
                return

        self.show_image()
        self.load_thumbnails_threaded()

    def add_tag(self):
        new_tags = self.new_tag_input.text().strip()
         
        if not new_tags or self.navigation.count() == 0:
            return
        
        current_image = self.navigation.current_image()
        tags = [tag.strip() for tag in new_tags.split(',') if tag.strip()]

        self.controller.add_tags(current_image,tags)
        
        self.new_tag_input.clear()
        self.update_tag_list()

    def remove_tag(self):
        selected_items = self.tag_list.selectedItems()
        
        if not selected_items or self.navigation.count() == 0: 
            return
        
        tag_to_remove = selected_items[0].text()
        current_image = self.navigation.current_image()

        self.controller.remove_tag(current_image,tag_to_remove)
        
        self.update_tag_list()

    def update_tag_list(self):
        self.tag_list.clear()
        current_image = self.navigation.current_image()

        if current_image is None:
            return
        

        tags = self.controller.get_tags_for_image(current_image)

        for tag in tags:
            self.tag_list.addItem(tag)

    def _preload_neighbors(self):
        count = self.navigation.count()
        if count == 0:
            return

        size = self.image_label.size()
        index = self.navigation.current_index()

        # Imagen siguiente
        if index + 1 < count:
            next_image = self.navigation.image_at(index + 1)
            self.image_loader.preload_preview(next_image, size)

        # Imagen anterior
        if index - 1 >= 0:
            prev_image = self.navigation.image_at(index - 1)
            self.image_loader.preload_preview(prev_image, size)

    def _on_preview_ready(self, path, pixmap):
        try:
            current = self.navigation.current_image()
            if current != path:
                return  # llegó tarde, ignoramos

            self.image_label.setPixmap(pixmap)
        except Exception as e:
            print(f"[ImageViewer] Error al mostrar preview: {e}")