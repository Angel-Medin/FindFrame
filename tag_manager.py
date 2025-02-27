import sqlite3
from pathlib import Path

class TagManagerSQLite:
    def __init__(self, db_path="tags.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Tabla img: almacena nombre y ruta (única) de cada imagen.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS img (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                path TEXT UNIQUE
            )
        """)
        # Tabla tag: almacena cada etiqueta de forma única.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        """)
        # Tabla intermedia img_tag: relación muchos a muchos entre imágenes y etiquetas.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS img_tag (
                img_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (img_id, tag_id),
                FOREIGN KEY (img_id) REFERENCES img(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_img_path ON img(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tag_name ON tag(name)")
        self.conn.commit()

    def initialize_images(self, image_paths):
        """
        Inserta en la tabla 'img' cada imagen (si no existe) a partir de su ruta.
        image_paths es una lista de objetos Path.
        """
        cursor = self.conn.cursor()
        for path in image_paths:
            name = path.name
            cursor.execute("INSERT OR IGNORE INTO img (name, path) VALUES (?, ?)", (name, str(path)))
        self.conn.commit()

    def get_image_id(self, image_path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM img WHERE path = ?", (str(image_path),))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_tag_id(self, tag):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM tag WHERE name = ?", (tag,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_tags(self, image_path):
        cursor = self.conn.cursor()
        query = """
            SELECT t.name
            FROM tag t
            JOIN img_tag it ON t.id = it.tag_id
            JOIN img i ON i.id = it.img_id
            WHERE i.path = ?
        """
        cursor.execute(query, (str(image_path),))
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def add_tag(self, image_path, tag):
        cursor = self.conn.cursor()
        img_id = self.get_image_id(image_path)
        if img_id is None:
            name = Path(image_path).name if not isinstance(image_path, Path) else image_path.name
            cursor.execute("INSERT OR IGNORE INTO img (name, path) VALUES (?, ?)", (name, str(image_path)))
            self.conn.commit()
            img_id = self.get_image_id(image_path)
        cursor.execute("INSERT OR IGNORE INTO tag (name) VALUES (?)", (tag,))
        self.conn.commit()
        tag_id = self.get_tag_id(tag)
        if tag_id is None:
            return
        cursor.execute("INSERT OR IGNORE INTO img_tag (img_id, tag_id) VALUES (?, ?)", (img_id, tag_id))
        self.conn.commit()

    def remove_tag(self, image_path, tag):
        cursor = self.conn.cursor()
        img_id = self.get_image_id(image_path)
        tag_id = self.get_tag_id(tag)
        if img_id is None or tag_id is None:
            return
        cursor.execute("DELETE FROM img_tag WHERE img_id = ? AND tag_id = ?", (img_id, tag_id))
        self.conn.commit()

    def filter_images(self, positive_tags, negative_tags):
        """
        Retorna una lista de rutas (str) de imágenes que cumplen:
         - Si positive_tags no está vacío: la imagen debe tener TODAS las etiquetas positivas.
         - Si negative_tags no está vacío: la imagen NO debe tener ninguna etiqueta negativa.
        """
        cursor = self.conn.cursor()
        if positive_tags:
            placeholders = ",".join("?" for _ in positive_tags)
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
        else:
            cursor.execute("SELECT path FROM img")
            results = [row[0] for row in cursor.fetchall()]
        if negative_tags:
            placeholders = ",".join("?" for _ in negative_tags)
            query = f"""
            SELECT DISTINCT img.path
            FROM img
            JOIN img_tag ON img.id = img_tag.img_id
            JOIN tag ON tag.id = img_tag.tag_id
            WHERE tag.name IN ({placeholders})
            """
            cursor.execute(query, negative_tags)
            negative_paths = {row[0] for row in cursor.fetchall()}
            results = [path for path in results if path not in negative_paths]
        return results

    def close(self):
        self.conn.close()
