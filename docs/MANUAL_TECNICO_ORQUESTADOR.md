# Mapa de Flujo del Orquestador (Enrutamiento de Consultas)

Este documento describe detalladamente cómo el **Orquestador Inteligente** (`ConversationOrchestrator`) clasifica y deriva las consultas de los usuarios entre los distintos motores del sistema: el **Flujo Experto de Calefacción (PEISA)**, el **RAG de Calefacción (PEISA)**, y el **RAG de Construcción (Weber)**.

---

## 1. Diagrama de Flujo del Enrutador

El siguiente diagrama ilustra la lógica paso a paso utilizada por `IntentClassifier.classify()` para determinar el enrutamiento de un mensaje:

```mermaid
flowchart TD
    Start([Mensaje del Usuario]) --> CheckExpertMode{¿Está en Modo Experto?}
    
    %% Flujo Modo Experto
    CheckExpertMode -- Sí --> CheckClarification{¿Es pregunta aclaratoria?}
    CheckClarification -- Sí --> IntentClarification[Intención: CLARIFICATION\n-> RAG PEISA con botón 'Continuar']
    CheckClarification -- No --> CheckNumeric{¿Es entrada numérica / opción?}
    CheckNumeric -- Sí --> IntentGuided[Intención: GUIDED_CALCULATION\n-> Avanza en Flujo Experto]
    CheckNumeric -- No --> CheckSwitchMode
    
    %% Flujo General / No Experto
    CheckExpertMode -- No --> CheckSwitchMode{¿Es cambio de modo explícito?\n(Ej: 'quiero preguntar libremente')}
    
    CheckSwitchMode -- Sí --> IntentSwitch[Intención: SWITCH_MODE\n-> Cambia modo en Contexto]
    CheckSwitchMode -- No --> CheckContextualRouting{¿Hay marca activa previa?\n(last_active_brand en Contexto)}
    
    %% Enrutamiento Contextual
    CheckContextualRouting -- Sí --> CheckGreeting{¿Es un saludo simple?\n(hola, gracias, chau, etc.)}
    CheckGreeting -- No --> CheckBrandConflict{¿Tiene palabras clave\nde la OTRA marca?}
    
    CheckBrandConflict -- No (Se mantiene marca) --> RouteActiveBrand{¿Cuál es la marca activa?}
    RouteActiveBrand -- WEBER --> IntentWeberContext[Intención: WEBER_QUERY\n-> RAG Weber (Confianza 0.95)]
    RouteActiveBrand -- PEISA --> IntentPeisaContext[Intención: FREE_QUERY\n-> RAG PEISA (Confianza 0.95)]
    
    CheckGreeting -- Sí (Es saludo) --> CheckFastCascading
    CheckBrandConflict -- Sí (Conflicto de marcas) --> CheckFastCascading
    CheckContextualRouting -- No --> CheckFastCascading
    
    %% Enrutamiento Rápido (Regex Heurístico)
    CheckFastCascading{¿Tiene palabras clave directas?}
    CheckFastCascading -- Weber Keywords --> IntentWeberFast[Intención: WEBER_QUERY\n-> RAG Weber (Confianza 1.0)]
    CheckFastCascading -- PEISA Keywords --> IntentPeisaFast[Intención: FREE_QUERY\n-> RAG PEISA (Confianza 1.0)]
    CheckFastCascading -- Ninguna --> CheckSemantic{¿Modelo Semántico\nvectorial disponible?}
    
    %% Enrutamiento Semántico
    CheckSemantic -- Sí --> ComputeCosineSim[Calcular Similitud de Coseno con Anclas]
    ComputeCosineSim --> CompareScores{¿Alguna supera el\numbral de 0.35?}
    CompareScores -- Sí (Weber > PEISA) --> IntentWeberSemantic[Intención: WEBER_QUERY\n-> RAG Weber (Confianza = Sim Weber)]
    CompareScores -- Sí (PEISA > Weber) --> IntentPeisaSemantic[Intención: FREE_QUERY\n-> RAG PEISA (Confianza = Sim PEISA)]
    CompareScores -- No --> FallbackRegex
    CheckSemantic -- No --> FallbackRegex
    
    %% Fallbacks e Híbrido
    FallbackRegex{¿Coincide con expresiones\nregulares de Weber?}
    FallbackRegex -- Sí --> IntentWeberRegex[Intención: WEBER_QUERY\n-> RAG Weber (Confianza 0.8)]
    FallbackRegex -- No --> MatchOtherPatterns{¿Coincide con otros patrones?\n(Búsqueda, cálculo guiado, etc.)}
    
    MatchOtherPatterns -- Sí --> RoutePattern[Enrutar según patrón coincidente]
    MatchOtherPatterns -- No --> IntentHybrid[Intención: HYBRID\n-> Modo Híbrido (RAG PEISA + Sugerencia Experta)]
```

---

## 2. Definición de Variables y Conceptos Clave

Para entender las decisiones de enrutamiento, es fundamental conocer las siguientes variables que maneja el clasificador:

*   **`last_active_brand`**: Almacena la marca de la cual se habló por última vez en la sesión (`"WEBER"` o `"PEISA"`).
*   **`is_simple_greeting`**: Coincide con expresiones de saludo o despedida puras como `"hola"`, `"buenas"`, `"gracias"`, `"chau"`, etc. Evita que un simple saludo quede atrapado por el contexto de marca previa.
*   **`DIRECT_WEBER_KEYWORDS`**: Palabras de descarte rápido para Weber (`weber`, `pastina`, `mortero`, `revoque`, `ceresita`, `weberplast`, `microcemento`, `microcolor`, `microbase`, `autonivela`).
*   **`DIRECT_PEISA_KEYWORDS`**: Palabras de descarte rápido para PEISA (`peisa`, `caldera`, `radiador`, `toallero`, `calefon`, `termo`, `climatiz`).
*   **Textos Ancla Semánticos (Embeddings)**:
    *   *Weber:* `"colocación de revestimientos cerámicas porcelanatos baldosas impermeabilización de losas piscinas pastina revoque fino mezcla adhesivo cemento"`
    *   *PEISA:* `"calefacción caldera radiador toallero calefón termotanque agua caliente sanitaria climatización"`

---

## 3. Situaciones y Escenarios Comunes

A continuación se detallan las distintas situaciones por las que puede pasar el orquestador:

### Escenario A: Inicio de Conversación / Saludo Inicial
*   **Mensaje:** `"hola"` o `"buenas tardes"`
*   **Estado del Contexto:** Sin marca activa (`last_active_brand = None`).
*   **Evaluación:**
    1.  No está en modo experto ni es cambio de modo explícito.
    2.  No hay marca activa previa.
    3.  No contiene palabras clave directas.
    4.  El modelo semántico calcula similitudes muy bajas (menores a `0.35`) porque el mensaje es muy corto y genérico.
    5.  Cae en los patrones por defecto.
*   **Resultado:** Clasifica como `IntentType.HYBRID` (Confianza 0.5) y deriva a **Modo Híbrido** (RAG PEISA por defecto para charla abierta, y ofrece sugerencias del calculador).

### Escenario B: Continuación del Contexto de Marca (Weber)
*   **Mensaje:** `"¿Cuánto tarda en secar?"`
*   **Estado del Contexto:** Marca activa previa `last_active_brand = "WEBER"`.
*   **Evaluación:**
    1.  No es un saludo simple (no es `"hola"`, etc.).
    2.  `last_brand` es `"WEBER"`.
    3.  El mensaje no contiene palabras clave de PEISA (`not has_peisa_kw` es `True`).
*   **Resultado:** Enrutamiento Contextual Directo. Clasifica como `IntentType.WEBER_QUERY` (Confianza 0.95) y deriva al **RAG de Weber**. La marca activa se mantiene en `"WEBER"`.

### Escenario C: Cambio Explícito de Marca por Palabra Clave Directa
*   **Mensaje:** `"Me cansé de construir, ahora quiero ver calefactores PEISA"`
*   **Estado del Contexto:** Marca activa previa `last_active_brand = "WEBER"`.
*   **Evaluación:**
    1.  No es saludo.
    2.  Hay marca activa previa (`"WEBER"`).
    3.  Sin embargo, el mensaje contiene la palabra `"peisa"`, por lo que `has_peisa_kw` es `True` (hay conflicto/cambio de marca). El enrutamiento contextual se salta.
    4.  Pasa a la fase de *Enrutamiento Rápido por Palabras Clave Directas*.
    5.  Detecta `"peisa"` en `DIRECT_PEISA_KEYWORDS`.
*   **Resultado:** Clasifica como `IntentType.FREE_QUERY` (Confianza 1.0) y deriva al **RAG de PEISA**. `last_active_brand` se actualiza a `"PEISA"`.

### Escenario D: Clasificación Semántica (Pregunta abierta sin marca directa)
*   **Mensaje:** `"Necesito impermeabilizar la losa del techo"`
*   **Estado del Contexto:** Sin marca activa previa (`last_active_brand = None`).
*   **Evaluación:**
    1.  No hay palabras clave rápidas de Weber o PEISA en la consulta (ej. *"impermeabilizar"* o *"losa"* no están en las palabras heurísticas cortas directas).
    2.  El clasificador recurre al modelo semántico vectorial.
    3.  Calcula la similitud de coseno:
        *   Similitud con ancla Weber: `~0.42` (Alto debido a "impermeabilizar" y "losa").
        *   Similitud con ancla PEISA: `~0.15`.
    4.  Dado que `sim_weber > sim_peisa` y supera el umbral de `0.35`.
*   **Resultado:** Clasifica como `IntentType.WEBER_QUERY` (Confianza `0.42`) y deriva al **RAG de Weber**. Actualiza `last_active_brand` a `"WEBER"`.

### Escenario E: Interrupción Aclaratoria en Modo Experto
*   **Mensaje:** El usuario está respondiendo preguntas sobre las dimensiones de su casa en el calculador paso a paso de calefacción, pero pregunta: `"¿Qué es una caldera de condensación?"`
*   **Estado del Contexto:** Modo activo `ConversationMode.EXPERT`.
*   **Evaluación:**
    1.  El mensaje coincide con los patrones de `IntentType.CLARIFICATION` (`"qué es"`, etc.).
*   **Resultado:** Clasifica como `IntentType.CLARIFICATION`. El orquestador pausa el nodo actual del flujo experto (`paused_expert_node`), responde la pregunta técnica de calefacción usando el RAG de PEISA, y le presenta al usuario un botón/opción para "Continuar con el cálculo".

---

## 4. Resumen de Flujos de Destino

| Intención Clasificada | Destino del Orquestador | Comportamiento en la UI | Marca Activa Resultante |
| :--- | :--- | :--- | :--- |
| `GUIDED_CALCULATION` | Motor Experto (`expert_engine`) | Flujo guiado paso a paso con opciones | `PEISA` |
| `FREE_QUERY` | RAG PEISA (`rag_llm_peisa`) | Respuesta de asesor técnico PEISA | `PEISA` |
| `WEBER_QUERY` | RAG Weber (`rag_llm_weber`) | Respuesta de asesor de construcción Weber | `WEBER` |
| `CLARIFICATION` | RAG PEISA + Pausa de Experto | Respuesta técnica + Botón para reanudar | Sin cambios |
| `SWITCH_MODE` | Cambiar modo de contexto | Actualiza la UI/modo de conversación | Sin cambios |
| `HYBRID` / `FALLBACK` | RAG PEISA + Sugerencia Experta | Respuesta RAG + Botón "Calcular paso a paso" | `PEISA` (por defecto) |
