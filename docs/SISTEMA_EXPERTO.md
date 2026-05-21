# Documentación del Sistema Experto

Esta guía documenta el flujo guiado por reglas para dimensionar calefacción (piso radiante, radiadores y calderas).

## ¿Qué es la KB (Knowledge Base)?

**KB** es la abreviatura de **Knowledge Base** (Base de Conocimiento).

Es el archivo JSON que contiene **todo el conocimiento del sistema experto**: reglas de decisión, flujo de conversación, fórmulas de cálculo y lógica de negocio para asesorar en calefacción.

**Archivo:** `app/peisa_advisor_knowledge_base.json`

### ¿Qué contiene la KB?

1. **Reglas de decisión**: Qué preguntar según las respuestas anteriores
2. **Flujo de conversación**: Secuencia de nodos (preguntas → cálculos → respuestas)
3. **Fórmulas y cálculos**: Expresiones matemáticas para dimensionar calefacción
4. **Lógica de negocio**: Criterios para recomendar productos

La KB es el "cerebro" del sistema experto. El motor (`expert_engine.py`) lee e interpreta esta KB para guiar al usuario paso a paso.

## Archivos clave del Sistema Experto

### 1. Base de Conocimiento (KB) + Reglas
**Archivo:** `app/peisa_advisor_knowledge_base.json`

- **Función**: Define el flujo, preguntas, cálculos y lógica del sistema experto
- **Contenido**: Nodos con `id`, `tipo`, `pregunta`, `opciones`, `acciones`, `siguiente`
- **Rol**: Es la fuente de conocimiento que el motor interpreta

### 2. Motor de Inferencia
**Archivo:** `app/modules/expertSystem/expert_engine.py`

- **Función**: Ejecuta las reglas de la KB
- **Clase principal**: `ExpertEngine`
- **Métodos clave**:
  - `process()`: Interpreta el nodo actual y avanza
  - `_perform_calculation()`: Ejecuta cálculos con eval seguro
  - `_replace_variables()`: Reemplaza variables en textos
- **Rol**: Es el "motor" que lee la KB y la ejecuta

### 3. Integración con Catálogo de Productos
**Archivo:** `app/modules/expertSystem/product_loader.py`

- **Función**: Carga productos y expone funciones de recomendación
- **Fuente de datos**: `data/products_catalog.json` (o fallback a Excel/CSV)
- **Funciones auxiliares disponibles en la KB**:
  - `filter_radiators()`: Filtra radiadores por criterios
  - `recommend_boiler()`: Recomienda calderas
  - `recommend_floor_heating_kit()`: Recomienda kits de piso radiante
  - `recommend_radiator_from_catalog()`: Busca radiadores específicos
  - `recommend_towel_rack_from_catalog()`: Busca toalleros
  - `format_radiator_recommendations()`: Formatea recomendaciones
  - `load_product_catalog()`: Carga el catálogo completo
- **Rol**: Conecta el sistema experto con el catálogo de productos PEISA

### 4. Modelos de Productos (Auxiliar)
**Archivo:** `app/modules/expertSystem/models.py`

- **Función**: Expone `RADIATOR_MODELS` con datos técnicos
- **Contenido**: Coeficientes, instalación, estilos, colores de radiadores
- **Rol**: Proporciona datos técnicos para cálculos

### 5. Front-end del Experto
**Archivo:** `app/modules/expertSystem/expertSystem.js`

- **Función**: Define la UX paso a paso del flujo guiado
- **Contenido**: Mensajes, inputs numéricos, opciones, panel de contexto
- **Rol**: Interfaz de usuario para el sistema experto

### 6. Endpoints Backend
**Archivo:** `app/main.py`

- **Endpoints**:
  - `POST /start`: Inicia conversación con `current_node = 'inicio'`
  - `POST /reply`: Procesa `option_index` o `input_values` y devuelve el siguiente mensaje
- **Rol**: API para versión server-side del sistema experto

## Flujo de Componentes

```
┌─────────────────────────────────────────┐
│  peisa_advisor_knowledge_base.json      │  ← BASE DE CONOCIMIENTO (KB)
│  (Reglas, preguntas, cálculos)          │     ¿Qué preguntar y cómo calcular?
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  expert_engine.py                        │  ← MOTOR DE INFERENCIA
│  (Interpreta y ejecuta la KB)           │     ¿Cómo ejecutar las reglas?
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  product_loader.py                       │  ← INTEGRACIÓN CON CATÁLOGO
│  (Carga productos y funciones auxiliares)│     ¿Qué productos recomendar?
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  data/products_catalog.json              │  ← CATÁLOGO DE PRODUCTOS
│  (Productos PEISA actualizados)         │     Datos de productos
└─────────────────────────────────────────┘
```

## Estructura de la KB (JSON)

Cada elemento es un nodo con campos posibles:
- `id`: identificador único.
- `pregunta`: texto mostrado al usuario.
- `tipo`: `entrada_usuario` | `calculo` | `respuesta` | `opciones_dinamicas`.
- `opciones`: lista de `{ texto, valor?, siguiente }` para múltiples elecciones.
- `variable` o `variables`: binding de entradas numéricas a contexto.
- `acciones`: expresiones a evaluar en nodos de `calculo`.
- `siguiente`: id del próximo nodo (para cálculo o flujos lineales).

Ejemplo (radiadores):
- Pide dimensiones (`variables`: largo, ancho, alto).
- Pide nivel de aislación, instalación, estilo, color.
- Nodo `recomendar_modelos` (tipo `calculo`):
  - `volumen = largo * ancho * alto`
  - `carga_termica = volumen * (50|40|30)`
  - `modelos_recomendados = filter_radiators(...)`
  - `modelos_recomendados_formateados = format_radiator_recommendations(...)`
- `mostrar_recomendaciones` devuelve texto con la recomendación.

## Motor `ExpertEngine`

- `process(conversation_id, expert_state, option_index?, input_values?)`
  - Interpreta el nodo actual; guarda respuestas en `expert_state['variables']`.
  - Avanza automáticamente tras `calculo`.
- `_perform_calculation(node, context)`
  - Ejecuta `acciones` (strings) con eval seguro (`__builtins__` bloqueado) y funciones auxiliares:
    - `filter_radiators`, `format_radiator_recommendations`
    - `recommend_boiler`, `recommend_floor_heating_kit`, `recommend_radiator_from_catalog`, `recommend_towel_rack_from_catalog`
    - `format_towel_rack_recommendation`, `load_product_catalog`, `ceil`
- `_replace_variables(text, context)`
  - Reemplaza `{{variable}}` y permite expresiones Jinja2.
- Enriquecimiento RAG (opcional): `_enrich_with_rag` si `rag_engine` fue inyectado y el nodo lo habilita.

## Catálogo dinámico (`product_loader.py`)

- Carga `data/raw/Products_db.xlsx` (o fallback `data/processed/products_mock.csv`).
- Construye diccionarios de radiadores/calderas/piso radiante.
- Calcula `coeficiente` por modelo (350, 500, 600, 700, 800, 1000) y determina instalación/estilo/colores.
- Expone funciones de conveniencia: `get_all_products()`, `get_radiators_dict()`, `find_boiler_by_power()`.

## Front-end del experto (`expertSystem.js`)

- Define la UX paso a paso (mensajes, inputs numéricos, opciones, panel de contexto).
- Implementa cálculos rápidos en cliente como refuerzo visual.
- Llama funciones de recomendación basadas en `data/products_catalog.json`.

## Endpoints de FastAPI (modo server-side)

- `POST /start`: inicia conversación con `current_node = 'inicio'`.
- `POST /reply`: procesa `option_index` o `input_values` y devuelve el siguiente mensaje (pregunta/respuesta/cálculo).

## Extender reglas

1) Agregar un nodo en `peisa_advisor_knowledge_base.json`.
2) Conectar con `siguiente` u `opciones[].siguiente`.
3) Si es `calculo`, añadir expresiones en `acciones`. Podés usar variables del contexto y funciones auxiliares expuestas.
4) (Opcional) Añadir enriquecimiento RAG definiendo `enrich_with_rag: true` y/o `rag_query`.

## Seguridad y buenas prácticas

- `eval` se ejecuta con `__builtins__` deshabilitado y un set de funciones controladas.
- Validación de entradas: los nodos `entrada_usuario` convierten números con coma a punto y capturan `ValueError`.
- Consistencia de unidades: conversión W ↔ kcal/h (factor 0.859845).

## Ejemplo corto

- Piso radiante 80 m² zona sur → `carga_termica = 80 * 125 = 10000 W` (aprox. 8598 kcal/h), sugiere calderas doble servicio.
- Radiador para 4m × 3m × 2.5m con aislación media → `volumen=30m³`, `carga_termica=1200 kcal/h`, recomendar Broen E o Tropical según preferencias.

## Contrato del nodo (esquema)

Ejemplo de esquema mínimo para un nodo en la KB:

```json
{
  "id": "dimensiones_radiador",
  "tipo": "entrada_usuario",
  "pregunta": "Ingresá largo, ancho y alto del ambiente (en metros)",
  "variables": ["largo", "ancho", "alto"],
  "siguiente": "nivel_aislacion"
}
```

Nodo de cálculo con acciones y salto automático:

```json
{
  "id": "recomendar_modelos",
  "tipo": "calculo",
  "acciones": [
    "volumen = largo * ancho * alto",
    "carga_termica = volumen * (50 if aislacion == 'baja' else 40 if aislacion == 'media' else 30)",
    "modelos_recomendados = filter_radiators(carga_termica, tipo_instalacion, estilo_diseno, color_preferido)",
    "modelos_recomendados_formateados = format_radiator_recommendations(modelos_recomendados)"
  ],
  "siguiente": "mostrar_recomendaciones"
}
```

## Funciones auxiliares disponibles (resumen)

- Recomendación/filtrado: `filter_radiators`, `recommend_boiler`, `recommend_radiator_from_catalog`, `recommend_towel_rack_from_catalog`, `recommend_floor_heating_kit`.
- Formato de respuestas: `format_radiator_recommendations`, `format_towel_rack_recommendation`.
- Utilidades: `load_product_catalog`, `ceil`.

Estas funciones son las únicas expuestas al evaluador de expresiones; no hay acceso a `__builtins__` ni a imports.

## Persistencia de estado

- El estado del experto se guarda por `conversation_id`: `current_node`, `variables` y `historial`.
- Al recibir una respuesta/entrada, el motor actualiza el contexto y avanza al siguiente nodo.

## Errores comunes y cómo resolverlos

- Valores numéricos con coma: el motor convierte "4,5" a `4.5`; si falla, devuelve mensaje de validación.
- Variables faltantes: declarar `variables` en nodos de `entrada_usuario` antes de usarlas en `acciones`.
- Unidades: mantener consistencia entre W y kcal/h (usar el factor de conversión indicado).
