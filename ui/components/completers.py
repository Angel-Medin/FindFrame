from PyQt5.QtWidgets import QCompleter

class MultiTagCompleter(QCompleter):
    def __init__(self, model, parent=None):
        super().__init__(model, parent)

    def splitPath(self, path):
        # Solo tomamos la última palabra después de la coma para filtrar las sugerencias
        return [path.split(',')[-1].strip()]

    def pathFromIndex(self, index):
        # Al seleccionar, mantenemos lo anterior y añadimos la sugerencia
        text = self.widget().text()
        parts = text.split(',')
        if len(parts) > 1:
            # Reconstruimos la cadena: todo lo anterior + el nuevo tag + espacio para el siguiente
            return ", ".join([p.strip() for p in parts[:-1]]) + ", " + index.data()
        return index.data()