from pathlib import Path
from typing import List, Optional

class NavigationModel:
    def __init__(self):
        self._images: List[Path] = []
        self._index: int = 0

    # --- estado básico ---

    def set_images(self, images: List[Path]):
        """
        Establece la lista de imágenes, filtrando automáticamente 
        aquellas que ya no existen en el disco.
        """
        # Filtramos la lista antes de guardarla
        self._images = [p for p in images if p.exists()]
        
        # Ajustamos el índice: 0 si hay imágenes, -1 si quedó vacía
        if self._images:
            self._index = 0
        else:
            self._index = -1

    def clear(self):
        self._images = []
        self._index = -1 # Consistente con set_images

    # --- consultas ---

    def has_images(self) -> bool:
        return bool(self._images)

    def count(self) -> int:
        return len(self._images)

    def current_index(self) -> int:
        return self._index

    def current_image(self) -> Optional[Path]:
        if 0 <= self._index < len(self._images):
            return self._images[self._index]
        return None

    # --- navegación ---

    def can_next(self) -> bool:
        return self._index < len(self._images) - 1

    def can_previous(self) -> bool:
        return self._index > 0

    def next(self):
        if self.can_next():
            self._index += 1

    def previous(self):
        if self.can_previous():
            self._index -= 1

    def jump_to(self, index: int):
        if 0 <= index < len(self._images):
            self._index = index

    def jump_relative(self, delta: int):
        if not self._images:
            return
        new_index = max(0, min(self._index + delta, len(self._images) - 1))
        self._index = new_index



    def image_at(self, index):
        if 0 <= index < len(self._images):
            return self._images[index]
        return None
