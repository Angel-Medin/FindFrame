from pathlib import Path


class ImageService:
    def __init__(self, tag_manager):
        self.tag_manager = tag_manager

        # Cache: Path -> list[str]
        self._tags_cache = {}

    def get_tags(self, image_path: Path) -> list[str]:
        """
        Devuelve los tags de una imagen.
        Usa cache si están disponibles.
        """
        if image_path in self._tags_cache:
            return self._tags_cache[image_path]

        # Si no está en cache, consultamos a la DB
        tags = self.tag_manager.get_tags(str(image_path))

        # Guardamos en cache
        self._tags_cache[image_path] = tags

        return tags

    def add_tags(self, image_path: Path, tags: list[str]):
        """
        Agrega tags a una imagen y limpia cache.
        """
        for tag in tags:
            self.tag_manager.add_tag(str(image_path), tag)

        # Invalida cache de esta imagen
        self._tags_cache.pop(image_path, None)

    def remove_tag(self, image_path: Path, tag: str):
        """
        Elimina un tag de una imagen y limpia cache.
        """
        self.tag_manager.remove_tag(str(image_path), tag)

        # Invalida cache de esta imagen
        self._tags_cache.pop(image_path, None)
