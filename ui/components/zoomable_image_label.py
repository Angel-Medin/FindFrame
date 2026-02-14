from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QPointF
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QPen, QColor, QTransform

class ZoomableImageLabel(QLabel):
    """
    Etiqueta que permite hacer zoom con la rueda del mouse y
    desplazarse (pan) arrastrando la imagen.
    Ahora con soporte para guías y grillas que mantienen su posición relativa.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(self.sizePolicy().Ignored, self.sizePolicy().Ignored)
        self.setScaledContents(False)
        
        self._pixmap = None
        self._scale_factor = 1.0
        self._zoom_step = 0.1
        self._min_scale = 0.1
        self._max_scale = 5.0
        
        self._panning = False
        self._last_mouse_pos = QPoint()
        
        # Sistema de guías (ahora en coordenadas normalizadas 0.0-1.0)
        self._guides_enabled = False
        self._guides_locked = False
        self._guide_mode = 'vertical'
        self._vertical_guides = []  # Lista de valores 0.0-1.0 (posición relativa en la imagen)
        self._horizontal_guides = []  # Lista de valores 0.0-1.0
        self._dragging_guide = None
        self._guide_snap_distance = 5
        
        # Sistema de grilla (ahora relativo al tamaño de la imagen)
        self._grid_enabled = False
        self._grid_spacing = 50  # En píxeles de la imagen original
        self._grid_color = QColor(100, 100, 255, 150)
        
        # Estado de espejo
        self._mirrored = False
        
        self.setMouseTracking(True)

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        
        if pixmap:
            parent = self.parent()
            while parent and not hasattr(parent, 'viewport'):
                parent = parent.parent()
            
            if parent:
                viewport_size = parent.viewport().size()
                if viewport_size.isValid() and not viewport_size.isEmpty():
                    if pixmap.width() > viewport_size.width() or pixmap.height() > viewport_size.height():
                        self._scale_factor = min(
                            viewport_size.width() / pixmap.width(),
                            viewport_size.height() / pixmap.height()
                        ) * 0.95
                    else:
                        self._scale_factor = 1.0
                else:
                    self._scale_factor = 1.0
            else:
                self._scale_factor = 1.0
                
            new_size = pixmap.size() * self._scale_factor
            if new_size.width() < 100 or new_size.height() < 100:
                self._scale_factor = 1.0
                new_size = pixmap.size()
            
            self.resize(new_size)
        
        self.update()

    def paintEvent(self, event):
        """Pinta la imagen, grilla y guías."""
        if not self._pixmap:
            super().paintEvent(event)
            return
        
        painter = QPainter(self)
        
        # Dibujar imagen escalada
        scaled_pixmap = self._pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Centrar la imagen
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        painter.drawPixmap(x, y, scaled_pixmap)
        
        # Guardar el rect de la imagen para las guías
        self._image_rect = QRect(x, y, scaled_pixmap.width(), scaled_pixmap.height())
        
        # Dibujar grilla
        if self._grid_enabled:
            self._draw_grid(painter)
        
        # Dibujar guías
        if self._guides_enabled:
            self._draw_guides(painter)

    def _draw_grid(self, painter):
        """Dibuja la grilla sobre la imagen manteniendo posición relativa."""
        if not hasattr(self, '_image_rect') or not self._pixmap:
            return
        
        pen = QPen(self._grid_color)
        pen.setWidth(1)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        
        rect = self._image_rect
        
        # Calcular el espaciado escalado según el zoom actual
        scaled_spacing = int(self._grid_spacing * self._scale_factor)
        
        # Evitar división por cero o espaciado muy pequeño
        if scaled_spacing < 1:
            scaled_spacing = 1
        
        # Líneas verticales
        x = rect.left()
        while x <= rect.right():
            painter.drawLine(int(x), rect.top(), int(x), rect.bottom())
            x += scaled_spacing
        
        # Líneas horizontales
        y = rect.top()
        while y <= rect.bottom():
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
            y += scaled_spacing


    def _draw_guides(self, painter):
        """Dibuja las guías sobre la imagen manteniendo posición relativa."""
        if not hasattr(self, '_image_rect') or not self._pixmap:
            return
        
        rect = self._image_rect
        
        # Color diferente si están bloqueadas
        if self._guides_locked:
            pen = QPen(QColor(0, 0, 139, 180))
        else:
            pen = QPen(QColor(220, 20, 60, 180))
        
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Guías verticales (convertir de coordenadas normalizadas a píxeles)
        for normalized_x in self._vertical_guides:
            x = rect.left() + int(normalized_x * rect.width())
            if rect.left() <= x <= rect.right():
                painter.drawLine(x, rect.top(), x, rect.bottom())
        
        # Guías horizontales (convertir de coordenadas normalizadas a píxeles)
        for normalized_y in self._horizontal_guides:
            y = rect.top() + int(normalized_y * rect.height())
            if rect.top() <= y <= rect.bottom():
                painter.drawLine(rect.left(), y, rect.right(), y)

    def wheelEvent(self, event):
        if not self._pixmap:
            return

        angle = event.angleDelta().y()
        if angle > 0:
            factor = 1.25
        else:
            factor = 0.8

        new_scale = self._scale_factor * factor
        
        if new_scale < self._min_scale or new_scale > self._max_scale:
            return

        self._scale_factor = new_scale
        new_size = self._pixmap.size() * self._scale_factor
        self.resize(new_size)
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()
        
        # Si las guías están bloqueadas, permitir pan normal
        if self._guides_locked or not self._guides_enabled:
            if event.button() == Qt.LeftButton:
                self._panning = True
                self._last_mouse_pos = event.globalPos()
                self.setCursor(Qt.ClosedHandCursor)
            return
        
        # Modo guías activo y desbloqueadas
        if event.button() == Qt.LeftButton:
            # Verificar si clickeamos cerca de una guía existente
            guide = self._find_guide_near(pos)
            
            if guide:
                self._dragging_guide = guide
                self.setCursor(Qt.SizeAllCursor)
            else:
                # Crear nueva guía según el modo seleccionado
                if hasattr(self, '_image_rect') and self._image_rect.contains(pos):
                    rect = self._image_rect
                    
                    if self._guide_mode == 'vertical':
                        # Convertir posición de píxeles a normalizada (0.0-1.0)
                        normalized_x = (pos.x() - rect.left()) / rect.width()
                        self._vertical_guides.append(normalized_x)
                        self._dragging_guide = ('vertical', len(self._vertical_guides) - 1)
                    else:  # horizontal
                        # Convertir posición de píxeles a normalizada (0.0-1.0)
                        normalized_y = (pos.y() - rect.top()) / rect.height()
                        self._horizontal_guides.append(normalized_y)
                        self._dragging_guide = ('horizontal', len(self._horizontal_guides) - 1)
                    
                    self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        
        # Si está arrastrando una guía (solo si no están bloqueadas)
        if not self._guides_locked and self._guides_enabled and self._dragging_guide:
            if not hasattr(self, '_image_rect'):
                return
                
            guide_type, index = self._dragging_guide
            rect = self._image_rect
            
            if guide_type == 'vertical':
                if 0 <= index < len(self._vertical_guides):
                    # Convertir posición del mouse a coordenadas normalizadas
                    if rect.left() <= pos.x() <= rect.right():
                        normalized_x = (pos.x() - rect.left()) / rect.width()
                        self._vertical_guides[index] = max(0.0, min(1.0, normalized_x))
            else:
                if 0 <= index < len(self._horizontal_guides):
                    # Convertir posición del mouse a coordenadas normalizadas
                    if rect.top() <= pos.y() <= rect.bottom():
                        normalized_y = (pos.y() - rect.top()) / rect.height()
                        self._horizontal_guides[index] = max(0.0, min(1.0, normalized_y))
            
            self.update()
            return
        
        # Pan de la imagen
        if self._panning:
            delta = event.globalPos() - self._last_mouse_pos
            self._last_mouse_pos = event.globalPos()
            
            scroll_area = self.parent().parent()
            if hasattr(scroll_area, 'horizontalScrollBar'):
                h_bar = scroll_area.horizontalScrollBar()
                v_bar = scroll_area.verticalScrollBar()
                
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
        
        # Cambiar cursor si estamos cerca de una guía (solo si no están bloqueadas)
        if self._guides_enabled and not self._guides_locked:
            guide = self._find_guide_near(pos)
            if guide:
                guide_type = guide[0]
                if guide_type == 'vertical':
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.SizeVerCursor)
            elif not self._panning:
                self.setCursor(Qt.CrossCursor)
        elif not self._panning:
            self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._panning = False
            self._dragging_guide = None
            if self._guides_enabled and not self._guides_locked:
                self.setCursor(Qt.CrossCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        """Doble clic en una guía para eliminarla (solo si no están bloqueadas)."""
        if not self._guides_enabled or self._guides_locked:
            return
        
        pos = event.pos()
        guide = self._find_guide_near(pos)
        
        if guide:
            guide_type, index = guide
            if guide_type == 'vertical':
                self._vertical_guides.pop(index)
            else:
                self._horizontal_guides.pop(index)
            self.update()

    def _find_guide_near(self, pos):
        """Encuentra una guía cerca de la posición dada."""
        if not hasattr(self, '_image_rect'):
            return None
        
        rect = self._image_rect
        
        # Buscar guía vertical
        for i, normalized_x in enumerate(self._vertical_guides):
            x = rect.left() + int(normalized_x * rect.width())
            if abs(pos.x() - x) < self._guide_snap_distance:
                return ('vertical', i)
        
        # Buscar guía horizontal
        for i, normalized_y in enumerate(self._horizontal_guides):
            y = rect.top() + int(normalized_y * rect.height())
            if abs(pos.y() - y) < self._guide_snap_distance:
                return ('horizontal', i)
        
        return None

    def reset_zoom(self):
        """Reinicia el zoom al tamaño original o ajuste de ventana."""
        self._scale_factor = 1.0
        if self._pixmap:
            self.adjustSize()
            self.update()

    # Métodos públicos para controlar guías y grilla
    def toggle_guides(self, enabled):
        """Activa/desactiva el modo de guías."""
        self._guides_enabled = enabled
        # Actualizar cursor según el estado
        if enabled and not self._guides_locked:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def lock_guides(self, locked):
        """Bloquea/desbloquea las guías."""
        self._guides_locked = locked
        # Actualizar cursor
        if self._guides_enabled and not locked:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        self.update()

    def set_guide_mode(self, mode):
        """Establece el modo de guía: 'vertical' o 'horizontal'."""
        if mode in ['vertical', 'horizontal']:
            self._guide_mode = mode

    def clear_guides(self):
        """Elimina todas las guías."""
        self._vertical_guides.clear()
        self._horizontal_guides.clear()
        self.update()

    def toggle_grid(self, enabled):
        """Activa/desactiva la grilla."""
        self._grid_enabled = enabled
        self.update()

    def set_grid_spacing(self, spacing):
        """Establece el espaciado de la grilla (en píxeles de la imagen original)."""
        self._grid_spacing = max(10, spacing)
        self.update()

    def set_grid_color(self, color):
        """Establece el color de la grilla."""
        self._grid_color = color
        self.update()

    def mirror_image(self, enabled):
        """Espeja la imagen horizontalmente y transforma las guías."""
        if not self._pixmap:
            return
        
        # Solo aplicar si el estado cambia realmente
        if enabled == self._mirrored:
            return
        
        self._mirrored = enabled
        
        # Espejar el pixmap horizontalmente
        transform = QTransform()
        transform.scale(-1, 1)
        self._pixmap = self._pixmap.transformed(transform)
        
        # Espejar las guías verticales (coordenadas normalizadas)
        self._vertical_guides = [1.0 - g for g in self._vertical_guides]
        
        # Las guías horizontales no cambian al espejar horizontalmente
        # La grilla es simétrica, no requiere ajustes
        
        self.update()