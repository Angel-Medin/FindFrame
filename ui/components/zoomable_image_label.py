from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QCursor

class ZoomableImageLabel(QLabel):
    """
    Etiqueta que permite hacer zoom con la rueda del mouse y
    desplazarse (pan) arrastrando la imagen.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(self.sizePolicy().Ignored, self.sizePolicy().Ignored)
        self.setScaledContents(True)
        
        self._pixmap = None
        self._scale_factor = 1.0
        self._zoom_step = 0.1
        self._min_scale = 0.1
        self._max_scale = 5.0
        
        self._panning = False
        self._last_mouse_pos = QPoint()

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        
        if pixmap:
            # Calcular escala inicial para ajustar a la ventana (fit to view) si es muy grande
            # o mantener tamaño original si cabe.
            # Accedemos al scroll area padre (o abuelo) para ver el tamaño disponible
            parent = self.parent()
            while parent and not hasattr(parent, 'viewport'):
                parent = parent.parent()
            
            if parent:
                viewport_size = parent.viewport().size()
                if viewport_size.isValid() and not viewport_size.isEmpty():
                     # Lógica simple: si la imagen es más grande que el viewport, ajustamos al 90% del viewport
                     # Si es más pequeña, usamos tamaño original.
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
            # Asegurar un tamaño mínimo visible
            if new_size.width() < 100 or new_size.height() < 100:
                self._scale_factor = 1.0
                new_size = pixmap.size()
            
            self.resize(new_size)

    def wheelEvent(self, event):
        if not self._pixmap:
            return

        # Calcular nuevo factor de escala
        angle = event.angleDelta().y()
        if angle > 0:
            factor = 1.25
        else:
            factor = 0.8

        new_scale = self._scale_factor * factor
        
        # Limitar zoom
        if new_scale < self._min_scale or new_scale > self._max_scale:
            return

        self._scale_factor = new_scale
        
        # Redimensionar el label
        new_size = self._pixmap.size() * self._scale_factor
        self.resize(new_size)

        # Ajustar scrollbars para mantener el foco del zoom (opcional, básico por ahora)
        # Una implementación más avanzada ajustaría el scroll para centrar en el cursor
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._panning = True
            self._last_mouse_pos = event.globalPos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.globalPos() - self._last_mouse_pos
            self._last_mouse_pos = event.globalPos()
            
            # Mover scrollbars del área padre
            # Se asume que el padre (o abuelo) es un QScrollArea
            scroll_area = self.parent().parent()
            if hasattr(scroll_area, 'horizontalScrollBar'):
                h_bar = scroll_area.horizontalScrollBar()
                v_bar = scroll_area.verticalScrollBar()
                
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)

    def reset_zoom(self):
        """Reinicia el zoom al tamaño original o ajuste de ventana."""
        self._scale_factor = 1.0
        if self._pixmap:
            self.adjustSize()
