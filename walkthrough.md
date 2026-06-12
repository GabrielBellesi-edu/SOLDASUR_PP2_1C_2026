# Walkthrough: Cambios de la Versión v5.0.1

Hemos completado la reestructuración del chat de **SOLDASUR** a la versión 5.0.1, implementando el enrutamiento dinámico, el menú interactivo para calculadoras y la galería de productos dinámica.

---

## 1. Cambios Realizados y Resultados

1.  **Enrutamiento y Selección de Marcas Corregido:**
    *   Se corrigió el problema donde al hacer clic en `"PEISA"` o `"WEBER"` en el menú de búsqueda de productos se abría la calculadora por error.
    *   Ahora la lógica en [soldasur.js](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/web_app/soldasur.js) prioriza de manera absoluta la navegación de catálogo si el usuario selecciona el nombre o logo de una marca registrada.
    *   El enrutamiento de calculadoras se restringe a coincidencias exactas con el botón configurado (por ejemplo, `"Calculadora Weber (Construcción)"` o `"Calculadora PEISA (Calefacción)"`).

2.  **Saludo Inicial y Menú Principal Dinámico:**
    *   El saludo inicial de Soldy ahora menciona explícitamente sus tres funciones principales: buscar productos por marca, realizar cálculos técnicos y responder preguntas libres.
    *   Se eliminó el botón de pregunta libre (ya que existe el input de texto en la parte inferior).
    *   Se agregó la opción `"Calculadoras"`, la cual abre dinámicamente un submenú que recopila todas las marcas activas con sistema experto (`has_calculator: true` en `brands_registry.json`).

3.  **Desacoplamiento y Sistema Experto Genérico:**
    *   Tanto PEISA como Weber ahora corren de forma unificada utilizando la clase `GenericExpertClient` en el frontend, la cual se comunica con el backend a través de los endpoints `/api/expert/{brand}/start` y `/api/expert/{brand}/reply`.
    *   Se eliminó toda dependencia hardcodeada en el frontend respecto a marcas añadidas.

4.  **Limpieza de Referencias Específicas:**
    *   Se removieron referencias explícitas a marcas de demostración externas en el registro central (`brands_registry.json`) y en el archivo de prompts (`prompts.json`).
    *   Se actualizó el [manual de escalamiento](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/manualparaescalamiento.md) utilizando `"Tigre"` como marca genérica para ilustrar el proceso de **"Agregar nuevas marcas"**.

---

## 2. Archivos Modificados

*   **[soldasur.js](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/web_app/soldasur.js)**: Reescritura del flujo de inicio, submenú de calculadoras y ruteo de clics.
*   **[peisa_expert.js](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/web_app/js_modules/peisa_expert.js)**: Limpieza del estado global al resetear.
*   **[chatbot.js](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/web_app/js_modules/chatbot.js)**: Renderizado de imágenes totalmente dinámico y genérico.
*   **[brands_registry.json](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/configs/brands_registry.json)**: Eliminación de la entrada hardcodeada.
*   **[prompts.json](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/configs/prompts.json)**: Eliminación del prompt hardcodeado.
*   **[manualparaescalamiento.md](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/manualparaescalamiento.md)**: Reemplazo por marca genérica.
*   **[v5.0.1.md](file:///d:/ESTUDIO/CPMA/DEV/22%20-%20PRACTICA%20PROFESIONALIZANTE%20II/Repo/v5/SOLDASUR_PP2_1C_2026/docs/v5.0.1.md)**: Nueva documentación del sistema.

---

## 3. Verificación de Funcionamiento

*   **Menú Principal:** Muestra "Calculadoras" y "Buscar productos".
*   **Buscar productos:** Abre el menú de marcas ("PEISA", "Weber"). Al presionar sobre cualquiera de ellas, se listan correctamente las categorías del catálogo sin abrir la calculadora.
*   **Calculadoras:** Despliega el submenú correspondiente con PEISA y Weber. Al hacer clic en Weber, inicia el asistente unificado con sus 5 ramas de decisión funcionando en tiempo real desde el backend.
