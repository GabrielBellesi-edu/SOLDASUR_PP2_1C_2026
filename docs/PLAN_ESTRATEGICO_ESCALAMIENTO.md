# Plan Estratégico de Escalamiento del Proyecto: Soldy
## Planificación Estratégica, Hoja de Ruta de Integración y Hoja de Ruta de Expansión Multimarca
### Ubicación: docs/PLAN_ESTRATEGICO_ESCALAMIENTO.md

---

## 📌 1. Introducción y Visión de Crecimiento

El proyecto **Soldy** fue concebido y desarrollado bajo una premisa fundamental de ingeniería de software: **la escalabilidad**. Lo que inicialmente se planteó como un requerimiento acotado para incorporar los productos Weber de Saint-Gobain a una solución heredada que solo soportaba la marca de calefacción PEISA, se transformó en un **Ecosistema Multimarca Escalable**. 

Este documento constituye el **Plan Estratégico de Escalamiento** diseñado para guiar a la gerencia técnica y comercial de **Soldasur S.A.** en la incorporación progresiva de nuevos catálogos de productos, calculadoras de obra adicionales y la integración de canales del sistema con la infraestructura transaccional interna de la empresa.

---

## 2. Dimensiones del Escalamiento

El escalamiento del sistema Soldy se estructura en cuatro dimensiones fundamentales de la operación comercial 
y de sistemas:

```
                  [ ESCALAMIENTO DE SOLDY ]
                              |
     +-----------------+------+-----------------+
     |                 |                        |
[Catálogo]       [Calculadoras]          [Tecnológico/ERP]
  Durlock,         Sistemas Expertos       Stock en tiempo real
  IPS, Sanitarios  basados en JSON         y conexión con el CRM
```

### 2.1. Escalamiento de Catálogo y Contenidos (RAG)
Consiste en la incorporación semántica de la biblioteca completa de productos de los proveedores estratégicos de Soldasur. La base de datos vectorial de FAISS local de la aplicación permite agregar decenas de miles de vectores de productos sin sufrir degradación de performance.
*   **Marcas de fase inmediata:** *Durlock* (construcción en seco).
*   **Marcas de fase intermedia:** *IPS* (tuberías de fusión para agua y gas) y *Ferrum* (línea de sanitarios y loza).
*   **Marcas de fase de consolidación:** *Bosch* o *DeWalt* (máquinas y herramientas de mano).

### 2.2. Escalamiento Funcional (Calculadoras y Lógica Experta)
Permite la automatización dinámica de cálculos para las nuevas marcas. Existen dos metodologías de escalamiento lógico en el backend:
1.  **Calculadoras Genéricas mediante JSON:** El sistema levanta el árbol de decisión interactivo de la base de conocimiento utilizando el archivo estructurado `advisor_knowledge_base_<marca>.json` en la carpeta `app/`. No requiere escribir código Python.
2.  **Motores Personalizados:** Para lógicas de cálculo complejas (como dobles encolados o fórmulas volumétricas físicas), el desarrollador añade un script dinámico en la ruta de sistemas expertos (`app/modules/expertSystem/expert_engine_<marca>.py`), el cual es importado en caliente por la API de FastAPI.

### 2.3. Escalamiento Tecnológico (Integración Corporativa)
Consiste en conectar a Soldy con los sistemas transaccionales preexistentes de Soldasur S.A.:
*   **Integración con el ERP:** Conectar las consultas del chatbot a la API del ERP de la empresa para contrastar el catálogo de recomendaciones con el **stock físico en tiempo real** de la sucursal de Ushuaia o Río Grande, informando al cliente la disponibilidad inmediata de compra.
*   **Integración con el CRM de Ventas:** Capturar los datos calculados por el cliente (ej. listado de materiales Weber para una obra de 50 m²) y transferirlos automáticamente como un presupuesto de pre-venta al sistema de gestión comercial con un número de identificador único.

### 2.4. Escalamiento del Canal de Distribución (Despliegue)
*   **Punto de Venta Interno:** Acceso directo desde las computadoras del mostrador para los asesores comerciales en salón.
*   **Canal Web:** Widget interactivo flotante en el sitio web de comercio electrónico de Soldasur S.A.
*   **Tótem Físico:** Despliegue de la interfaz táctil en terminales de consulta autónomas dentro de los salones de ventas físicos de la Patagonia.

---

## 3. Plan de Escalamiento a Corto, Mediano y Largo Plazo

El plan de trabajo estratégico se desglosa en una hoja de ruta de tres fases consecutivas a realizarse a lo largo de 12 meses.

```
       CORTO PLAZO (0-3 meses)                MEDIANO PLAZO (3-6 meses)                 LARGO PLAZO (6-12 meses)
+------------------------------------+  +------------------------------------+  +------------------------------------+
| * Integrar Durlock.                |  | * Integrar API ERP (Stock Físico). |  | * Integración CRM (Presupuestos).  |
| * Cuantización del LLM local.      |  | * Despliegue de Tótems en salón.   |  | * Historial de clientes.           |
| * Pruebas piloto con vendedores.   |  | * Ingesta de IPS e instalaciones.  |  | * Incorporar Herramientas Bosch.   |
+------------------------------------+  +------------------------------------+  +------------------------------------+
```

### 3.1. Fase de Corto Plazo (0 a 3 meses)
*   **Hito 1: Integración Completa de la marca Durlock:**
    *   Implementación de los scrapers correspondientes para placas y perfiles.
    *   Ejecución del instalador automático [install_brand.py](../SOLDASUR_PP2_1C_2026/app/modules/escalamiento/install_brand.py) para levantar el índice FAISS.
    *   Ajuste de palabras clave heurísticas y prompt del sistema en `configs/prompts.json`.
*   **Hito 2: Cuantización y Optimización de Ollama:**
    *   Implementación de modelos cuantizados de 4 bits (`llama3.2:3b-instruct-q4_K_M`) para reducir el consumo de RAM en las computadoras de mostrador a menos de 2 GB.
*   **Hito 3: Fase Piloto en Sucursal Río Grande:**
    *   Despliegue de Soldy en tres computadoras de asesores seleccionados para evaluar la usabilidad y la velocidad de carga de información en mostrador.

### 3.2. Fase de Mediano Plazo (3 a 6 meses)
*   **Hito 1: Conexión con el Stock Físico (ERP):**
    *   Desarrollo de un endpoint intermedio en FastAPI que consulte la base de datos de stock de la sucursal de consulta activa.
    *   Ajuste del motor RAG para inyectar una etiqueta técnica: *"Stock disponible en Ushuaia: Sí (25 unidades)"*.
*   **Hito 2: Despliegue de Tótems Interactivos:**
    *   Adaptación de la hoja de estilos [soldasur.css](../SOLDASUR_PP2_1C_2026/web_app/soldasur.css) para resoluciones de pantalla táctil verticales de salón de ventas.
    *   Instalación del software cliente en la sucursal de Ushuaia para autoasistencia.
*   **Hito 3: Ingesta de la marca IPS:**
    *   Carga y procesamiento del catálogo de tuberías y accesorios de termofusión para agua y gas.

### 3.3. Fase de Largo Plazo (6 a 12 meses)
*   **Hito 1: Integración de Presupuestación CRM:**
    *   Habilitar al chatbot la capacidad de enviar un link único de cotización directo al WhatsApp o correo electrónico del cliente, enlazado con el CRM comercial de Soldasur.
*   **Hito 2: Personalización por Historial:**
    *   Reconocimiento del perfil de cliente (Arquitecto, Constructor, Particular) para priorizar el tono del vocabulario técnico y las recomendaciones comerciales correspondientes.

---

## 4. El Estándar Técnico de Integración

Para asegurar que cualquier equipo de desarrollo futuro o administrador de TI de Soldasur pueda escalar la plataforma de forma autónoma, se debe cumplir de manera estricta el protocolo de tres etapas implementado en la arquitectura **v5.1.0**:

### Etapa A: Estandarización de Entrada
Cualquier scraper o proceso manual debe empaquetar la nueva información respetando la estructura de carpetas definida en el manual de escalamiento de datos [MANUAL_ESCALAMIENTO.md](../SOLDASUR_PP2_1C_2026/docs/MANUAL_ESCALAMIENTO.md).
*   La propiedad `"imagen_local"` en el catálogo JSON debe ser relativa a la carpeta de scraping y comenzar obligatoriamente con el prefijo estático `data_raw/<marca_lower>/img/` usando barras diagonales `/`.
*   Las categorías en `"categories_processed"` deben detallar los nombres estilizados y amigables para el menú final de la interfaz del chat.

### Etapa B: El Proceso Automatizado
Se debe ejecutar el script CLI pasando el identificador exacto de la marca:
```bash
python app/modules/escalamiento/install_brand.py NombreMarca
```
Este pipeline asegura de manera automática e inquebrantable la coherencia de los embeddings vectoriales, la compilación de FAISS, la autogeneración de los scripts RAG (`rag_query_<marca>.py` y `rag_llm_<marca>.py`), el registro de prompts, variables de temperatura y el alta en el orquestador sin modificar código central.

---

## 5. Matriz de Riesgos y Acciones de Mitigación

El escalamiento de un sistema híbrido de inteligencia artificial conlleva riesgos tecnológicos e informáticos específicos que deben mitigarse planificadamente:

| Evento de Riesgo | Probabilidad | Impacto | Acción de Mitigación Estratégica |
| :--- | :---: | :---: | :--- |
| **Degradación de RAM por Ollama local** | Alta | Medio | Utilizar versiones cuantizadas de modelos ligeros (` llama3.2:3b` o similares de 4 bits). Configurar a Ollama para liberar el modelo de la memoria RAM tras 5 minutos de inactividad (`OLLAMA_NUM_PARALLEL=1` y `OLLAMA_KEEP_ALIVE=5m`). |
| **Inconsistencias en Catálogos JSON** | Media | Alto | Implementar validadores de esquemas JSON estrictos (mediante la librería `Pydantic` en python) antes de correr el indexador `install_brand.py` para rechazar catálogos sin campos obligatorios. |
| **Latencia de Inferencia en Mostrador** | Media | Alto | En servidores de producción local, instalar placas de video dedicadas compatibles con aceleración CUDA de Nvidia. Limitar el parámetro `"max_tokens"` a `150` en [configs/prompts.json](../SOLDASUR_PP2_1C_2026/configs/prompts.json). |
| **Conflicto de Enrutamiento Semántico** | Baja | Medio | Ajustar de manera precisa los textos ancla descriptivos de la clave `"anchor_text"` en el registro [configs/brands_registry.json](../SOLDASUR_PP2_1C_2026/configs/brands_registry.json) para delimitar claramente los campos temáticos de las marcas aliadas. |
