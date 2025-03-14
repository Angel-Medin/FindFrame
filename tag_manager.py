import sqlite3
from pathlib import Path

class TagManagerSQLite:
    def __init__(self, db_path="tags.db"):
        """
        Inicializa el gestor de etiquetas con la ruta de la base de datos.
        Crea las tablas e índices necesarios si no existen.
        Args:
            db_path (str): Ruta del archivo de la base de datos SQLite.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Habilita integridad referencial
        self.create_tables()

    def create_tables(self):
        """Crea las tablas e índices necesarios para el sistema de etiquetas."""
        cursor = self.conn.cursor()
        
        # Tabla de imágenes: Almacena metadatos básicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS img (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,          -- Nombre del archivo
                path TEXT UNIQUE    -- Ruta única del archivo
            )
        """)
        
        # Tabla de etiquetas: Catálogo de tags únicos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE     -- Nombre único de la etiqueta
            )
        """)
        
        # Tabla de relación muchos-a-muchos entre imágenes y etiquetas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS img_tag (
                img_id INTEGER,      -- ID de la imagen
                tag_id INTEGER,      -- ID de la etiqueta
                PRIMARY KEY (img_id, tag_id),
                FOREIGN KEY (img_id) REFERENCES img(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
            )
        """)
        
        # Crea índices para mejorar rendimiento de consultas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_img_path ON img(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_name ON tag(name)")
        
        self.conn.commit()

    def initialize_images(self, image_paths):
        """
        Inserta imágenes en la base de datos si no existen previamente.
        Args:
            image_paths (list[Path]): Lista de objetos Path con rutas de imágenes.
        """
        cursor = self.conn.cursor()
        for path in image_paths:
            name = path.name
            # Ignora inserciones duplicadas gracias a la restricción UNIQUE
            cursor.execute("INSERT OR IGNORE INTO img (name, path) VALUES (?, ?)", 
                          (name, str(path)))
        self.conn.commit()

    def update_image_url(self,img_name,new_image_path):
        """
        Actualiza la ruta de una imagen basado en su nombre.
        Args:
            imag_name(str): Nombre de la imagen
        """
        cursor = self.conn.cursor()
        cursor.execute("UPDATE img SET path = ? WHERE name = ?",(new_image_path,img_name))
        self.conn.commit()


    def get_image_id(self, image_path):
        """
        Obtiene el ID de una imagen basado en su ruta.
        Args:
            image_path (str/Path): Ruta de la imagen
        Returns:
            int: ID de la imagen o None si no existe
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM img WHERE path = ?", (str(image_path),))
        result = cursor.fetchone()
        return result[0] if result is not None else None

    def get_tag_id(self, tag):
        """
        Obtiene el ID de una etiqueta basado en su nombre.
        Args:
            tag (str): Nombre de la etiqueta
        Returns:
            int: ID de la etiqueta o None si no existe
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM tag WHERE name = ?", (tag,))
        result = cursor.fetchone()
        return result[0] if result is not None else None

    def get_tags(self, image_path):
        """
        Recupera todas las etiquetas asociadas a una imagen.
        Args:
            image_path (str/Path): Ruta de la imagen
        Returns:
            list[str]: Lista de nombres de etiquetas
        """
        cursor = self.conn.cursor()
        query = """
            SELECT t.name
            FROM tag t
            JOIN img_tag it ON t.id = it.tag_id
            JOIN img i ON i.id = it.img_id
            WHERE i.path = ?
            ORDER BY t.name ASC
        """
        cursor.execute(query, (str(image_path),))
        return [row[0] for row in cursor.fetchall()]

    def add_tag(self, image_path, tag):
        """
        Asocia una etiqueta a una imagen, creando registros necesarios si no existen.
        Args:
            image_path (str/Path): Ruta de la imagen
            tag (str): Nombre de la etiqueta
        """
        cursor = self.conn.cursor()
        img_id = self.get_image_id(image_path)
        
        # Si la imagen no existe, la registramos
        if not img_id:
            name = Path(image_path).name
            cursor.execute("INSERT OR IGNORE INTO img (name, path) VALUES (?, ?)", 
                          (name, str(image_path)))
            self.conn.commit()
            img_id = self.get_image_id(image_path)
        
        # Aseguramos que la etiqueta exista
        cursor.execute("INSERT OR IGNORE INTO tag (name) VALUES (?)", (tag,))
        self.conn.commit()
        tag_id = self.get_tag_id(tag)
        
        # Creamos la relación si no existe
        if img_id and tag_id:
            cursor.execute("""
                INSERT OR IGNORE INTO img_tag (img_id, tag_id) 
                VALUES (?, ?)
            """, (img_id, tag_id))
            self.conn.commit()

    def remove_tag(self, image_path, tag):
        """
        Elimina una etiqueta de una imagen específica.
        Args:
            image_path (str/Path): Ruta de la imagen
            tag (str): Nombre de la etiqueta
        """
        cursor = self.conn.cursor()
        img_id = self.get_image_id(image_path)
        tag_id = self.get_tag_id(tag)
        
        if img_id and tag_id:
            cursor.execute("DELETE FROM img_tag WHERE img_id = ? AND tag_id = ?", 
                          (img_id, tag_id))
            self.conn.commit()

    def filter_images(self, positive_tags, negative_tags):
        """
        Filtra imágenes según etiquetas positivas (requeridas) y negativas (excluidas).
        Args:
            positive_tags (list[str]): Etiquetas que deben estar presentes
            negative_tags (list[str]): Etiquetas que no deben estar presentes
        Returns:
            list[str]: Rutas de imágenes que cumplen los criterios
        """
        cursor = self.conn.cursor()
        results = []
        
        print(f"Positive tags: {positive_tags}")
        print(f"Negative tags: {negative_tags}")
        
        # Filtro de etiquetas positivas
        if positive_tags:
            placeholders = ",".join("?" * len(positive_tags))
            query = f"""
                SELECT img.path
                FROM img
                JOIN img_tag ON img.id = img_tag.img_id
                JOIN tag ON tag.id = img_tag.tag_id
                WHERE tag.name IN ({placeholders})
                GROUP BY img.id
                HAVING COUNT(DISTINCT tag.name) = ?
            """
            cursor.execute(query, (*positive_tags, len(positive_tags)))
            results = [row[0] for row in cursor.fetchall()]
            print(f"Images after positive filter: {len(results)}")
        else:
            cursor.execute("SELECT path FROM img")
            results = [row[0] for row in cursor.fetchall()]
            print(f"All images: {len(results)}")
        
        # Filtro de etiquetas negativas
        if negative_tags:  # Eliminamos la condición "and results"
            placeholders = ",".join("?" * len(negative_tags))
            query = f"""
                SELECT DISTINCT img.path
                FROM img
                JOIN img_tag ON img.id = img_tag.img_id
                JOIN tag ON tag.id = img_tag.tag_id
                WHERE tag.name IN ({placeholders})
            """
            print(f"Negative query: {query}")
            print(f"Negative params: {negative_tags}")
            cursor.execute(query, negative_tags)
            excluded = {row[0] for row in cursor.fetchall()}
            print(f"Images to exclude: {len(excluded)}")
            results = [p for p in results if p not in excluded]
            print(f"Images after negative filter: {len(results)}")
        
        return results

    def close(self):
        """Cierra la conexión a la base de datos."""
        self.conn.close()