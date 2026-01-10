from pathlib import Path
from image_loader import get_image_paths

class ImageController:
    def __init__(self, tag_manager, image_service):
        self.tag_manager = tag_manager
        self.image_service = image_service

    def load_folder(self, folder_path: Path):
        """
        Carga imágenes desde una carpeta y las registra en la DB.
        Devuelve una lista de Path.
        """
        image_paths = get_image_paths(folder_path)
        if not image_paths:
            return []

        self.tag_manager.initialize_images(image_paths)
        return image_paths

    def apply_filters(self, positive_tags, negative_tags):
        """
        Devuelve una nueva lista de Path filtrados.
        No toca UI.
        No modifica estado visual.
        """
        filtered = self.tag_manager.filter_images(positive_tags, negative_tags)
        return [Path(p) for p in filtered]

    def add_tags(self, image_path, tags):
        """
        Asocia una o varias etiquetas a una imagen.
        """
           
        self.image_service.add_tags(image_path,tags)
    
    def remove_tag(self, image_path, tag):
        self.image_service.remove_tag(image_path,tag)


    def get_tags_for_image(self, image_path):
        """
        Devuelve una lista de tags para una imagen.
        """
        return self.image_service.get_tags(image_path)