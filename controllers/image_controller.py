from pathlib import Path
from infrastructure.image_loader import get_image_paths

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
        """
        return self.image_service.filter_images(positive_tags, negative_tags)

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

    def add_tag_to_folder(self, image_paths, tag):
        """
        Agrega un tag a todas las imágenes de una lista.
        Args:
            image_paths (list[Path]): Lista de rutas de imágenes
            tag (str): Nombre del tag a agregar
        Returns:
            int: Cantidad de imágenes procesadas
        """
        return self.image_service.add_tag_to_folder(image_paths, tag)

    def count_images_with_tag(self, tag):
        """
        Cuenta cuántas imágenes tienen un tag específico.
        Args:
            tag (str): Nombre del tag
        Returns:
            int: Cantidad de imágenes con ese tag
        """
        return self.image_service.count_images_with_tag(tag)

    def delete_tag_globally(self, tag):
        """
        Elimina un tag de la base de datos y de todas las imágenes.
        Args:
            tag (str): Nombre del tag a eliminar
        Returns:
            bool: True si se eliminó exitosamente
        """
        return self.image_service.delete_tag_globally(tag)