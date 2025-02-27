from pathlib import Path

def get_image_paths(folder: Path):
    """
    Devuelve una lista ordenada de objetos Path que representan
    los archivos de imagen en la carpeta (incluyendo subcarpetas)
    con extensiones .jpg, .jpeg, .png, .bmp y .gif.
    """
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
    return sorted([path for path in folder.rglob("*") if path.suffix.lower() in image_extensions])
