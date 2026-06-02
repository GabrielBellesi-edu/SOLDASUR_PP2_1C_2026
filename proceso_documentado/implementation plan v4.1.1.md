# Plan de Implementación v4.1.1 - Neutralización de Marca y Actualización de index.html

Este plan propone cambios para neutralizar la presencia exclusiva de PEISA en la página web principal y unificar la imagen de **SOLDASUR S.A** como proveedor tanto de climatización (PEISA) como de construcción/revestimientos (Weber).

## Cambios de Slogan e Imagen Corporativa
* El slogan de la sección Hero cambiará de *"Más de 30 años climatizando hogares..."* a una versión integrada: **"Más de 30 años equipando, construyendo y climatizando hogares con tecnología de vanguardia y calidad excepcional"**.
* El subtítulo de Características Principales cambiará de *"Experiencia, calidad y tecnología al servicio de tu confort"* a **"Experiencia, calidad y tecnología al servicio de tu hogar"** para abarcar construcción y revestimientos.

## Estructura de Tarjetas de Productos
El catálogo visual de `index.html` pasará de tener 3 tarjetas (todas de calefacción/PEISA) a tener **6 tarjetas en total (rejilla de 3x2)**, agregando 3 tarjetas dedicadas a las soluciones Weber con la misma estética de degradados y bordes armoniosos de TailwindCSS.

---

## Cambios Propuestos

### [HTML Frontend]
Ajustes visuales de textos, sucursales y adición de productos de Weber.

#### [MODIFY] [index.html](../index.html)
* **Slogan Hero (Línea 45):** Reemplazar por un mensaje neutro de construcción y climatización.
* **Características Principales - Sucursales (Línea 99-100):** Modificar de "2 Sucursales" a "4 Sucursales", con el detalle de "Presencia con 2 locales en Río Grande y 2 en Ushuaia para estar siempre cerca tuyo".
* **Sección de Productos (Líneas 121-157):** Agregar 3 nuevas tarjetas en la rejilla de productos que representen las categorías de Weber:
  1. *Colocación de Revestimientos* (degradado ámbar a naranja, borde ámbar).
  2. *Impermeabilización* (degradado teal a azul, borde teal).
  3. *Pisos y Revestimientos Decorativos* (degradado piedra a gris, borde piedra).

---

### [Backend y Lógica de Configuración]
Neutralizar los inicializadores, títulos de servicio y fallbacks del chatbot que solo consideran a PEISA.

#### [MODIFY] [main.py](../../app/main.py)
* **Título de la Aplicación (Línea 24):** Cambiar de `"PEISA - SOLDASUR S.A"` a `"SOLDASUR S.A - Asistente Técnico"`.
* **Health Check (Línea 214):** Cambiar el valor del servicio de `"PEISA - SOLDASUR S.A"` a `"SOLDASUR S.A - Asistente Técnico"`.
* **Greeting Fallback en RAG PEISA:** El chatbot libre en el backend asume PEISA por defecto para preguntas generales o saludos. Se ajustará la respuesta semántica para reflejar ambas marcas si es un saludo neutro.

#### [MODIFY] [chatbot.js](../../app/modules/chatbot/chatbot.js)
* **Filtro de productos de respaldo (`filterRelevantProducts`):** Actualmente solo filtra calderas, radiadores y toalleros. Se actualizará para que si no detecta intención de calefacción, devuelva un mix balanceado de productos PEISA y Weber en lugar de solo PEISA.
* **Resaltado de productos (`cleanHtmlFromMessage`):** Utilizar `productCatalog` (que contiene ambas marcas cargadas desde `core.js`) en lugar de solo `peisaProductsFromJSON` para aplicar negritas y enriquecimiento de enlaces en el chat.

---

### [Documentación e Historial]
Crear el archivo de bitácora de cambios para la versión v4.1.1.

#### [NEW] [v4.1.1.md](v4.1.1.md)
* Detallar todas las modificaciones visuales y lógicas de neutralización de marca, sucursales y adición de productos Weber.

---

## Plan de Verificación

### Verificación Manual
1. Abrir la página principal `index.html` en el navegador y validar visualmente:
   * El nuevo slogan en el Hero.
   * La tarjeta de características principales indicando **4 sucursales**.
   * La sección de productos mostrando **6 tarjetas** (3 de PEISA y 3 de Weber) alineadas estéticamente en la grilla.
2. Iniciar el chat de Soldy y realizar preguntas neutras de prueba (ej: saludar, preguntar por sucursales) para validar que no responda como "tienda exclusiva de PEISA".
