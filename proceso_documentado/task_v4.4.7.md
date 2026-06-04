# Checklist de Tareas v4.4.7 — Soporte para Extracción de Imágenes en el Scraper de Weber

Este archivo hace seguimiento a los cambios y la verificación para la versión **v4.4.7**.

---

## 📋 Tareas de Desarrollo

- [x] **1. Actualizar el Scraper de Weber (`weber_product_scraper.py`)**
  - [x] Agregar soporte para crear el directorio `scraping/data_raw/weber/img`.
  - [x] Implementar extracción de `imagen_url` usando Open Graph y swiper/galería.
  - [x] Agregar el método `descargar_imagen` utilizando inyección de `fetch` con ArrayBuffer para descargar imágenes evadiendo bloqueos de Cloudflare.
  - [x] Incorporar los flags `--sin-img` en la CLI y vincularlos a `descargar_imagenes` en el loop principal.
  - [x] Guardar la ruta local en el campo `imagen_local` dentro del JSON del producto.

- [x] **2. Pruebas de Verificación**
  - [x] Ejecutar el scraper con `--max-productos 1` para validar la descarga de la imagen y la estructura del JSON resultante.

- [x] **3. Documentación**
  - [x] Crear bitácora `proceso_documentado/v4.4.7.md`.
  - [x] Crear task list `proceso_documentado/task_v4.4.7.md` (este archivo).
