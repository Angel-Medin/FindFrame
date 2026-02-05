
import os
import subprocess
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtCore import QObject, Qt, pyqtSignal, QThread, QStringListModel
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QFileDialog, QVBoxLayout, QWidget, QHBoxLayout,
                             QScrollArea, QFrame, QListWidget, QLineEdit,
                             QSizePolicy, QGridLayout, QCompleter)

from infrastructure.image_loader import get_image_paths
from infrastructure.tag_manager import TagManagerSQLite
from services.thumbnail_service import ThumbnailWorker
from controllers.image_controller import ImageController
from services.image_service import ImageService
from models.navigation_model import NavigationModel
from services.image_loader_service import ImageLoaderService
import logging
from ui.components.completers import MultiTagCompleter
from ui.components.toolbar import Toolbar
from ui.components.thumbnail_panel import ThumbnailPanel
from ui.components.image_viewer_panel import ImageViewerPanel
from ui.components.image_tags_panel import ImageTagsPanel


logger = logging.getLogger(__name__)

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor de Imágenes")
        self.setGeometry(100, 100, 1000, 700)
        # 1. Inicializar servicios y modelos de DATOS primero
        self.tag_manager = TagManagerSQLite()
        self.navigation = NavigationModel()
        self.image_loader = ImageLoaderService()
        self.image_service = ImageService(self.tag_manager)

        # 2. Crear el MODELO antes de la UI
        self.tag_model = QStringListModel(self.image_service.get_all_tags())
        self.controller = ImageController(self.tag_manager,self.image_service)

        # 3. Construir la UI
        self.setup_ui()
        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self.show_image)
        self.image_loader.preview_ready.connect(self._on_preview_ready)




    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setFocusPolicy(Qt.StrongFocus)
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.central_widget.setFocus()

        # Barra de tareas superior (solo botones)
        self.toolbar = Toolbar()
        self.toolbar.load_folder_requested.connect(self.load_folder)
        self.toolbar.update_folder_requested.connect(self.update_image_url)
            
        # Conexiones para guías y grilla
        self.toolbar.toggle_guides_requested.connect(self._on_toggle_guides)
        self.toolbar.lock_guides_requested.connect(self._on_lock_guides)
        self.toolbar.guide_mode_changed.connect(self._on_guide_mode_changed)
        self.toolbar.clear_guides_requested.connect(self._on_clear_guides)
        self.toolbar.toggle_grid_requested.connect(self._on_toggle_grid)
        self.toolbar.grid_spacing_changed.connect(self._on_grid_spacing_changed)
        self.toolbar.grid_color_changed.connect(self._on_grid_color_changed)
                
        # Conexiones para el menú de opciones
        self.toolbar.add_bulk_tag_requested.connect(self._on_add_bulk_tag)
        self.toolbar.rename_images_requested.connect(self._on_rename_images)
        self.toolbar.delete_tag_requested.connect(self._on_delete_tag)
            
        
        self.main_layout.addWidget(self.toolbar)

        # Filtros debajo de la barra de tareas
        self.filter_layout = QHBoxLayout()
        self.positive_tags_input = QLineEdit()
        self.setup_tag_autocomplete(self.positive_tags_input)
        self.positive_tags_input.setPlaceholderText("Etiquetas positivas (separadas por comas)")
        self.filter_layout.addWidget(self.positive_tags_input)
        
        self.negative_tags_input = QLineEdit()
        self.setup_tag_autocomplete(self.negative_tags_input)
        self.negative_tags_input.setPlaceholderText("Etiquetas negativas (separadas por comas)")
        self.filter_layout.addWidget(self.negative_tags_input)
        
        self.btn_apply_filters = QPushButton("Aplicar Filtros")
        self.btn_apply_filters.clicked.connect(self._on_apply_filters)
        self.filter_layout.addWidget(self.btn_apply_filters)
        self.main_layout.addLayout(self.filter_layout)

        # Layout principal para los paneles
        self.content_layout = QHBoxLayout()
        self.main_layout.addLayout(self.content_layout)

    def setup_left_panel(self):
        # Panel de miniaturas
        self.thumbnail_panel = ThumbnailPanel()
        self.thumbnail_panel.thumbnail_clicked.connect(self.thumbnail_clicked)
        self.content_layout.addWidget(self.thumbnail_panel, 1)

    def setup_center_panel(self):
        # Panel central del visor
        self.viewer_panel = ImageViewerPanel()
        self.viewer_panel.next_requested.connect(self.show_next)
        self.viewer_panel.previous_requested.connect(self.show_previous)
        self.content_layout.addWidget(self.viewer_panel, 4)

    def setup_right_panel(self):
        # Panel de etiquetas
        self.tags_panel = ImageTagsPanel(self.tag_model, self.setup_tag_autocomplete)
        self.tags_panel.tag_added.connect(self._on_tag_added)
        self.tags_panel.tag_removed.connect(self._on_tag_removed)
        self.tags_panel.open_external_requested.connect(self.external_app)
        self.content_layout.addWidget(self.tags_panel, 1)
   
    def highlight_thumbnail(self):
        """Delega el resaltado de thumbnail al panel de miniaturas."""
        current_image = self.navigation.current_image()
        self.thumbnail_panel.highlight_thumbnail(current_image)

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
            self.viewer_panel.set_loading_text("No se encontraron imágenes a actualizar.")
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
            self.viewer_panel.set_loading_text("Error al recargar vistas.")

    def _on_apply_filters(self):
        """Maneja la aplicación de filtros."""
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
            self.viewer_panel.set_loading_text("No se encontraron imágenes con esos filtros.")
            self.thumbnail_panel.clear_thumbnails()
            self.viewer_panel.set_navigation_enabled(False, False)
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
                self.viewer_panel.set_loading_text("No se encontraron imágenes.")
                # Deshabilitamos botones si la carpeta está vacía
                self.viewer_panel.set_navigation_enabled(False, False)
                self.thumbnail_panel.clear_thumbnails()
                return

        self.show_image()
        self.load_thumbnails_threaded()

    def _on_tag_removed(self, tag_to_remove):
        """Maneja la señal de eliminar etiqueta desde el panel de tags."""
        if self.navigation.count() == 0:
            return
        
        current_image = self.navigation.current_image()
        self.controller.remove_tag(current_image, tag_to_remove)
        self.update_tag_list()

    def update_tag_list(self):
        """Actualiza la lista de etiquetas en el panel de tags."""
        current_image = self.navigation.current_image()

        if current_image is None:
            self.tags_panel.clear_tag_list()
            return
        
        tags = self.controller.get_tags_for_image(current_image)
        self.tags_panel.update_tag_list(tags)

    def _preload_neighbors(self):
        count = self.navigation.count()
        if count == 0:
            return

        size = self.viewer_panel.get_image_label_size()
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

            self.viewer_panel.set_image(pixmap)
        except Exception as e:
            print(f"[ImageViewer] Error al mostrar preview: {e}")

    def _on_tag_added(self, tags_to_add):
        """Maneja la señal de agregar etiquetas desde el panel de tags."""
        current_image = self.navigation.current_image()

        if not current_image:
            print("[ImageViewer] No hay ninguna imagen seleccionada para etiquetar.")
            return
        
        self.controller.add_tags(current_image, tags_to_add)

        # Actualiza el autocompletado al instante
        self.tag_model.setStringList(self.image_service.get_all_tags())
        self.update_tag_list()

    def setup_tag_autocomplete(self, line_edit: QLineEdit):
        completer = MultiTagCompleter(self.tag_model, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        line_edit.setCompleter(completer)

    def _on_toggle_guides(self, enabled):
        """Activa/desactiva el modo de guías en el visor."""
        self.viewer_panel.image_label.toggle_guides(enabled)

    def _on_lock_guides(self, locked):
        """Bloquea/desbloquea las guías."""
        self.viewer_panel.image_label.lock_guides(locked)

    def _on_guide_mode_changed(self, mode):
        """Cambia el modo de guía (vertical/horizontal)."""
        self.viewer_panel.image_label.set_guide_mode(mode)

    def _on_clear_guides(self):
        """Limpia todas las guías del visor."""
        self.viewer_panel.image_label.clear_guides()

    def _on_toggle_grid(self, enabled):
        """Activa/desactiva la grilla en el visor."""
        self.viewer_panel.image_label.toggle_grid(enabled)

    def _on_grid_spacing_changed(self, spacing):
        """Cambia el espaciado de la grilla."""
        self.viewer_panel.image_label.set_grid_spacing(spacing)

    def _on_grid_color_changed(self, color):
        """Cambia el color de la grilla."""
        self.viewer_panel.image_label.set_grid_color(color)

    def load_thumbnails_threaded(self):
        """Carga lazy de thumbnails usando el nuevo sistema."""
        # Ya no usa threads, el panel maneja todo internamente
        self.thumbnail_panel.set_images(self.navigation._images)

    def show_image(self):
        try:
            current_image = self.navigation.current_image()
            if current_image is None:
                return

            # Placeholder inmediato
            self.viewer_panel.set_loading_text("Cargando imagen...")

            current_index = self.navigation.current_index()
            total = self.navigation.count()

            self.viewer_panel.set_filename(
                current_image.name, current_index, total
            )

            self.update_tag_list()
            self.viewer_panel.set_navigation_enabled(
                self.navigation.can_previous(),
                self.navigation.can_next()
            )
            self.highlight_thumbnail()
            
            # 👇 NUEVO: Precargar thumbnails alrededor de la imagen actual
            self.thumbnail_panel.preload_around_index(current_index)

            # Pedido asíncrono
            self.image_loader.request_preview_async(
                current_image,
                self.viewer_panel.get_image_label_size()
            )

            # Preload sigue igual
            self._preload_neighbors()

        except Exception as e:
            print(f"[ImageViewer] Error en show_image: {e}")
            self.viewer_panel.set_loading_text("Error al mostrar la imagen.")

    def _on_add_bulk_tag(self):
        """Maneja la opción de agregar tag masivo a carpeta."""
        from ui.components.options_dialogs import BulkTagDialog
        from infrastructure.image_loader import get_image_paths
        from pathlib import Path
        
        dialog = BulkTagDialog(self.tag_model, self.setup_tag_autocomplete, self)
        if dialog.exec_():
            folder_path = Path(dialog.folder_path)
            tag = dialog.tag
            
            # Obtener imágenes de la carpeta
            image_paths = get_image_paths(folder_path)
            
            if not image_paths:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Advertencia", 
                                  "No se encontraron imágenes en la carpeta seleccionada.")
                return
            
            # Agregar tag a todas las imágenes
            count = self.controller.add_tag_to_folder(image_paths, tag)
            
            # Actualizar el autocompleter si se agregó un nuevo tag
            self.tag_model.setStringList(self.image_service.get_all_tags())
            
            # Mostrar mensaje de éxito
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Éxito", 
                                  f"Se agregó el tag '{tag}' a {count} imagen(es).")

    def _on_rename_images(self):
        """Maneja la opción de renombrar imágenes con prefijo."""
        from ui.components.options_dialogs import RenameImagesDialog
        from infrastructure.file_renamer import rename_images_with_prefix
        from pathlib import Path
        
        dialog = RenameImagesDialog(self)
        if dialog.exec_():
            folder_path = Path(dialog.folder_path)
            prefix = dialog.prefix
            
            # Renombrar imágenes
            result = rename_images_with_prefix(folder_path, prefix)
            renamed = result["renamed"]
            errors = result["errors"]
            
            # Actualizar rutas en base de datos
            for old_path, new_path in renamed.items():
                old_name = Path(old_path).name
                self.tag_manager.update_image_url(old_name, new_path)
            
            # Mostrar resultado
            from PyQt5.QtWidgets import QMessageBox
            message = f"Se renombraron {len(renamed)} imagen(es) exitosamente."
            if errors:
                message += f"\n\nErrores ({len(errors)}):\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    message += f"\n... y {len(errors) - 5} errores más."
            
            QMessageBox.information(self, "Resultado del Renombrado", message)
            
            # Si la carpeta actual está siendo visualizada, refrescar
            if self.navigation.has_images():
                current_image = self.navigation.current_image()
                if current_image and current_image.parent == folder_path:
                    # Recargar la carpeta
                    from infrastructure.image_loader import get_image_paths
                    image_paths = get_image_paths(folder_path)
                    self.navigation.set_images(image_paths)
                    self.show_image()
                    self.load_thumbnails_threaded()

    def _on_delete_tag(self):
        """Maneja la opción de eliminar tag de la base de datos."""
        from ui.components.options_dialogs import DeleteTagDialog
        
        dialog = DeleteTagDialog(
            self.tag_model, 
            self.setup_tag_autocomplete,
            self.controller.count_images_with_tag,
            self
        )
        
        if dialog.exec_():
            tag = dialog.tag_to_delete
            
            # Eliminar tag
            success = self.controller.delete_tag_globally(tag)
            
            if success:
                # Actualizar el autocompleter
                self.tag_model.setStringList(self.image_service.get_all_tags())
                
                # Refrescar la lista de tags de la imagen actual si está visible
                if self.navigation.has_images():
                    self.update_tag_list()
                
                # Mostrar mensaje de éxito
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self, "Éxito", 
                                      f"El tag '{tag}' fue eliminado exitosamente de la base de datos.")
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Error", 
                                  f"No se pudo eliminar el tag '{tag}'.")


