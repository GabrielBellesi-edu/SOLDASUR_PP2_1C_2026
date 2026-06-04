# Bitácora Temporal de Ingesta Weber (SOLDASUR v4)

Este es un archivo de control temporal para retomar el trabajo mañana sobre el módulo de scraping e ingesta de productos de Weber Argentina.

---

## 📌 ¿Qué hicimos hoy?

1. **Evasión de Cloudflare (Turnstile):**
   * Detectamos que la web de Weber bloquea las peticiones de Playwright con un captcha de Cloudflare ("Un momento...").
   * Se implementó una lógica en `ir_a()` dentro de `weber_rag_scraper.py` y `Gscraper.py` que detecta la pantalla y **espera hasta 60 segundos** en consola para que resuelvas el desafío manualmente la primera vez.
   * La sesión aprobada se guarda en `./user_data/` para que las siguientes páginas carguen en piloto automático.

2. **Detección del Catálogo Omitido (Filtros):**
   * Descubrimos que el scraper omitía revestimientos plásticos, selladores, anclajes y mezclas de asiento porque la lista blanca de categorías era muy restrictiva y buscaba revoques solo en plural (`revoques`).
   * Ampliamos la lista blanca en `weber_rag_scraper.py` y agregamos los mapeos en `01_build_catalog.py` (`CATEGORY_MAP`).

3. **Desarrollo de Gscraper.py:**
   * Desarrollamos un scraper alternativo mucho más robusto: recorre la URL de búsqueda de productos de Drupal (`/search-content/content_type/product?page=X`) de forma paginada.
   * Logró recolectar exitosamente **100 productos reales** listados en la web en piloto automático.

---

## 🚀 ¿Cómo usarlo actualmente?

Para correr una prueba rápida o el scraping completo:

* **Prueba rápida (5 productos sin PDFs):**
  ```powershell
  python weber_ingest/Gscraper.py --max-productos 5 --sin-pdfs
  ```
* **Scraping completo (Extrae los 100 productos y baja PDFs técnicos):**
  ```powershell
  python weber_ingest/Gscraper.py
  ```
  *(Recordá: En la primera carga, se te abrirá la ventana gráfica del navegador de Playwright. Si salta la pantalla de "Un momento...", resolvé el captcha manualmente y el script seguirá solo).*

---

## ⚠️ Problemas Detectados / Notas Importantes

* **Playwright Dependencies:** El entorno virtual requiere `playwright` y `tqdm` instalados. Ya están agregados en `requirements.txt`.
* **Playwright Browser Install:** Si corrés en una máquina limpia, se debe ejecutar `playwright install` para descargar los binarios del navegador.
* ** user_data/ en gitignore:** Las cookies y caché persistentes se guardan en `user_data/`. Ya lo agregamos a `.gitignore` para no subir archivos basura al repositorio final.

---

## 📅 ¿Qué falta hacer mañana? (Próximos Pasos)

1. **Ejecutar la Ingesta RAG Completa:**
   * Ejecutar el comando completo `python weber_ingest/Gscraper.py` para descargar todos los productos e inyectar/descargar las fichas técnicas en PDF en `weber_data/documentos/` (demorará aproximadamente 10-15 minutos).
   * Ejecutar `python weber_ingest/01_build_catalog.py` para compilar los JSONs y PDFs de `weber_data/` en `data/weber_catalog.json`.
   * Ejecutar `python weber_ingest/02_build_embeddings.py` para generar el índice semántico FAISS actualizado en `embeddings/weber_products.faiss` y su metadata.
2. **Implementar el Enrutador Semántico:**
   * Reemplazar la lista estática `WEBER_KEYWORDS` de `app/main.py` por una clasificación por similitud coseno basada en embeddings (usando el modelo instanciado de SentenceTransformers) para enrutar de forma robusta las consultas al RAG de Weber o PEISA según la intención semántica de la consulta del cliente.
3. **Expandir weber_expert.js:**
   * Añadir los productos faltantes (como Microcolor, pastinas, etc.) en el cuestionario interactivo de la calculadora de Weber del frontend.
4. **Extraer Metadatos Técnicos Adicionales:**
   * Investigar cómo recuperar información extra de la web de Weber (como "área" de aplicación [ej. fachada], "actividad" [ej. pisos], "colores" [ej. blanco], "ancho de junta" [ej. 5mm]) a nivel de scraper y normalización de catálogo para enriquecer las consultas del RAG y del sistema experto.
