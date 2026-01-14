# FindFrame

**FindFrame** es una aplicación de escritorio desarrollada en Python con PyQt5 para **visualizar, navegar, filtrar y etiquetar imágenes** de forma eficiente, incluso en carpetas grandes.

---

## ✨ Características principales

* 📁 Carga de carpetas con imágenes
* 🖼️ Visor central con redimensionado dinámico
* 🧭 Navegación por teclado y botones
* 🧷 Sistema de etiquetas con persistencia (SQLite)
* 🔍 Filtros por etiquetas positivas y negativas
* 🧱 Miniaturas (thumbnails) generadas en segundo plano
* ⚡ Cache en memoria (LRU) para previews y thumbnails
* 🧵 Carga asíncrona usando `QThread`
* 📋 Logging estructurado para depuración

---

## 🏗️ Arquitectura general

```
UI → Controller → Services → Models / Infrastructure
```

### Capas principales

* **UI**

  * `viewer.py`
  * Maneja la interfaz gráfica y eventos del usuario

* **Controllers**

  * `ImageController`
  * Orquesta la lógica entre UI, servicios y modelos

* **Services**

  * `ImageLoaderService`: carga de imágenes, previews, thumbnails y cache
  * `ImageService`: lógica de negocio relacionada a imágenes
  * Workers y servicios auxiliares

* **Models**

  * `NavigationModel`: estado y navegación de imágenes

* **Infrastructure**

  * Acceso a filesystem
  * Base de datos SQLite
  * Configuración de logging

---

## 📂 Estructura del proyecto

```
findframe/
│
├── main.py
├── controllers/
│   └── viewer.py
│
├── controllers/
│   └── image_controller.py
│
├── models/
│   └── navigation_model.py
│
├── services/
│   ├── image_loader_service.py
│   ├── image_load_worker.py
│   ├── image_service.py
│   └── thumbnail_service.py
│
├── infrastructure/
│   ├── image_loader.py
│   ├── tag_manager.py
│   └── logging_config.py
│
├── assets/
│   └── style.qss
│
├── tags.db
├── app.log
├── errores.txt
├── README.md
└── .gitignore
```

---

## 🧠 Decisiones de diseño importantes

* **QThread** se utiliza para evitar bloquear la UI al cargar imágenes grandes
* **Cache LRU** limita el uso de memoria y mejora el rendimiento
* **Separación por capas** para facilitar refactorización y testing


---


