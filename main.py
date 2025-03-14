import sys
from PyQt5.QtWidgets import QApplication
from viewer import ImageViewer

def main():
    app = QApplication(sys.argv)

    # Cargar el stylesheet desde el fichero externo
    try:
        with open("style.qss", "r") as file:
            app.setStyleSheet(file.read())
    except Exception as e:
        print("No se pudo cargar el archivo de estilos:", e)    

    window = ImageViewer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
