from pathlib import Path


def rename_images_with_prefix(folder_path, prefix):
    """
    Renombra todas las imágenes de una carpeta agregando un prefijo.
    Args:
        folder_path (Path): Ruta de la carpeta con imágenes
        prefix (str): Prefijo a agregar
    Returns:
        dict: Diccionario con {ruta_antigua: ruta_nueva} de archivos renombrados exitosamente
    """
    from infrastructure.image_loader import get_image_paths
    
    image_paths = get_image_paths(folder_path)
    renamed = {}
    errors = []
    
    for old_path in image_paths:
        try:
            # Crear nuevo nombre: prefijo + "_" + nombre original
            new_name = f"{prefix}_{old_path.name}"
            new_path = old_path.parent / new_name
            
            # Verificar que no exista conflicto
            if new_path.exists():
                errors.append(f"Ya existe: {new_name}")
                continue
            
            # Renombrar el archivo
            old_path.rename(new_path)
            renamed[str(old_path)] = str(new_path)
            
        except PermissionError:
            errors.append(f"Sin permisos: {old_path.name}")
        except Exception as e:
            errors.append(f"Error en {old_path.name}: {str(e)}")
    
    return {"renamed": renamed, "errors": errors}
