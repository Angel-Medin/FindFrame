from pathlib import Path

def get_image_paths(folder: Path):
    """
    Devuelve una lista ordenada de objetos Path que representan
    los archivos de imagen en la carpeta (incluyendo subcarpetas)
    con extensiones .jpg, .jpeg, .png, .bmp y .gif.
    """
    image_extensions = {".jpg", ".webp", ".jpeg", ".png",".jfif" ,".bmp", ".gif"}
    
    # Obtenemos todas las imágenes
    images = [path for path in folder.rglob("*") 
             if path.suffix.lower() in image_extensions]
    
    # Ordenamos por fecha de modificación (st_mtime = timestamp de modificación)
    images.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    
    return images