from pathlib import Path


class ImageService:
    def __init__(self, tag_manager):
        self.tag_manager = tag_manager


        self._tags_cache = {}
        self._filter_cache = {}
        self._image_id_cache = {}

    def get_tags(self, image_path: Path) -> list[str]:
        """
        Devuelve los tags de una imagen.
        Usa cache de tags y de image_id.
        """
        # 1️⃣ Cache de tags
        if image_path in self._tags_cache:
            return self._tags_cache[image_path]

        # 2️⃣ Obtener image_id usando cache
        image_id = self._get_image_id(image_path)
        if image_id is None:
            return []

        # 3️⃣ Consultar tags por ID
        tags = self.tag_manager.get_tags_by_id(image_id)

        # 4️⃣ Guardar en cache
        self._tags_cache[image_path] = tags

        return tags

    def add_tags(self, image_path: Path, tags: list[str]):
        """
        Agrega tags a una imagen usando image_id cacheado.
        """
        image_id = self._get_image_id(image_path)
        if image_id is None:
            return

        for tag in tags:
            self.tag_manager.add_tag_by_id(image_id, tag)

        # Invalida cache de tags
        self._tags_cache.pop(image_path, None)
        self._filter_cache.clear()

    def remove_tag(self, image_path: Path, tag: str):
        """
        Elimina un tag usando image_id cacheado.
        """
        image_id = self._get_image_id(image_path)
        if image_id is None:
            return

        self.tag_manager.remove_tag_by_id(image_id, tag)

        # Invalida cache de tags
        self._tags_cache.pop(image_path, None)
        self._filter_cache.clear()

    def filter_images(self, positive_tags, negative_tags) -> list[Path]:
        """
        Filtra imágenes usando tags positivos y negativos.
        Usa cache si es posible.
        """
        pos = frozenset(t.strip() for t in positive_tags if t.strip())
        neg = frozenset(t.strip() for t in negative_tags if t.strip())

        cache_key = (pos, neg)

        if cache_key in self._filter_cache:
            return self._filter_cache[cache_key]
        
        
        filtered = self.tag_manager.filter_images(list(pos), list(neg))
        paths = [Path(p) for p in filtered if Path(p).exists()]
        self._filter_cache[cache_key] = paths
        

        return paths
    
    def _get_image_id(self, image_path: Path) -> int | None:
        """
        Devuelve el image_id usando cache.
        """
        if image_path in self._image_id_cache:
            return self._image_id_cache[image_path]

        image_id = self.tag_manager.get_image_id(image_path)
        if image_id is not None:
            self._image_id_cache[image_path] = image_id

        return image_id

    def get_all_tags(self) -> list[str]:
        return self.tag_manager.get_all_tags()





