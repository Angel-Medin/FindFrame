import sys
from PyQt5.QtWidgets import QApplication
from ui.viewer import ImageViewer
from infrastructure.logging_config import setup_logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STYLE_PATH = BASE_DIR / "assets" / "style.qss"


    



def main():
    setup_logging()

    app = QApplication(sys.argv)
    try:
        with open(STYLE_PATH, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print("No se pudo cargar el archivo de estilos:", e)    

    window = ImageViewer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
