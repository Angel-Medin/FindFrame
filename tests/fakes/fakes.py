from pathlib import Path

class FakeTagManager:
    def __init__(self):
        self._images = {}   # image_id -> Path
        self._tags = {}     # image_id -> set(tags)
        self._id_counter = 1
        self.filter_call_count = 0

    # ---------- Inicialización ----------

    def initialize_images(self, images):
        for img in images:
            image_id = self._id_counter
            self._id_counter += 1
            self._images[image_id] = img
            self._tags[image_id] = set()

    def set_tags(self, image: Path, tags: list[str]):
        image_id = self.get_image_id(image)
        if image_id is not None:
            self._tags[image_id] = set(tags)

    # ---------- Métodos requeridos por ImageService ----------

    def get_image_id(self, image_path: Path):
        for image_id, path in self._images.items():
            if path == image_path:
                return image_id
        return None

    def get_tags_by_id(self, image_id: int):
        return list(self._tags.get(image_id, []))

    def add_tag_by_id(self, image_id: int, tag: str):
        self._tags.setdefault(image_id, set()).add(tag)

    def remove_tag_by_id(self, image_id: int, tag: str):
        self._tags.get(image_id, set()).discard(tag)

    def filter_images(self, positive_tags, negative_tags):
        self.filter_call_count += 1
        result = []

        for image_id, path in self._images.items():
            tags = self._tags.get(image_id, set())

            if positive_tags and not all(t in tags for t in positive_tags):
                continue

            if negative_tags and any(t in tags for t in negative_tags):
                continue

            result.append(path)

        return result
