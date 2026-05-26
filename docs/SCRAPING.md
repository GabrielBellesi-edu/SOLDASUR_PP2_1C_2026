# Documentación de Scraping (PEISA)

Este módulo obtiene/actualiza el catálogo de productos PEISA.

## Archivos

- `app/modules/scraping/product_scraper.py`
  - Scraping real de `https://peisa.com.ar/productos`.
  - Extracción de tarjetas de productos (modelo, descripción, tipo), categoría/subcategoría (h1 y texto rojo), URL.
  - Detalle de producto: descripción completa, ventajas, características técnicas y especificaciones; normaliza potencia a Watts si es posible.
  - Mapeos: `map_category_to_family`, `determine_family`, `determine_type`.
  - Persistencia: `save_catalog()` fusiona con `data/products_catalog.json` (actualiza por URL; agrega nuevos).
  - `get_products_catalog(use_scraping=True)` permite forzar lectura desde archivo sin web.

- `app/modules/scraping/inspect_peisa.py`
  - Inspección/diagnóstico: guarda HTML y lista clases/enlaces de la página de productos para ajustar selectores.

## Flujo principal

1) `scrape_peisa_products()`
   - GET a `/productos` con headers tipo navegador y timeout.
   - Encuentra `<a href="/productos/..."><article>...</article></a>`.
   - Para cada card: determina categoría/subcategoría (busca `h1` previo), extrae `model`, `description`, `type`, `family` y `url`.
   - Luego visita la URL del producto para extraer `technical_features`, `advantages`, `specifications`, y `power_w` si es posible.
   - Pausas cortas (`time.sleep`) para evitar sobrecargar.

2) `save_catalog(filename, use_scraping)`
   - Carga catálogo existente (si hay) y lo indexa por URL.
   - Ejecuta `get_products_catalog()`; actualiza/merge por URL.
   - Guarda `data/products_catalog.json` con indentación y UTF-8.

## Ejecución

- Scraping real y guardado:
  ```bash
  python app/modules/scraping/product_scraper.py
  ```
- Sin scraping (solo re-escribir desde archivo existente):
  ```bash
  python app/modules/scraping/product_scraper.py --no-scraping
  ```
- Inspección de estructura HTML:
  ```bash
  python app/modules/scraping/inspect_peisa.py
  ```

## Consideraciones y límites

- La estructura del sitio puede cambiar; si falla extracción de cards/detalles, ajustar selectores (`find`, `find_all`, regex de href, etc.).
- Respetar tiempos (sleep) y headers para parecer navegador.
- Robots.txt/ToS: verificar políticas si se publica.
- Algunas páginas pueden no incluir listas `<ul>` de ventajas o características; el scraper intenta extraer del texto largo con heurísticas.
- Normalización de potencia: busca patrones `NN (W|kW|kcal)` y convierte a `power_w`.

## Uso en el proyecto

- El catálogo JSON resultante alimenta:
  - Chatbot (front-end) para armar el context prompt, renderizar tarjetas y enlaces.
  - RAG engine (back-end) para embeddings y ranking semántico.

## Esquema de salida (products_catalog.json)

Cada producto incluye típicamente los siguientes campos:

```json
{
  "model": "Caldera Prima 24",
  "description": "Caldera mural de alta eficiencia...",
  "category": "Calderas centrales",
  "subcategory": "De potencia",
  "type": "Caldera mural",
  "family": "Calderas",
  "url": "https://peisa.com.ar/productos/prima-24",
  "technical_features": ["Intercambiador ...", "Encendido electrónico ..."],
  "advantages": ["Alta eficiencia ...", "Bajo consumo ..."],
  "specifications": {"Potencia": "24 kW", "Alimentación": "220V"},
  "power_w": 24000
}
```

Notas:
- `power_w` se normaliza a Watts cuando puede detectarse en la página de producto.
- No todos los campos están presentes en todos los productos (depende de la página fuente).

## Resolución de problemas

- La página cambió estructura: ejecutar `inspect_peisa.py` para ver clases y enlaces; ajustar selectores en `product_scraper.py`.
- Muy pocos productos detectados: revisar el patrón `href` y la detección de `<article>` en tarjetas.
- Corte de conexión: el scraper usa timeouts y captura excepciones; reintentar o aumentar `timeout`.
