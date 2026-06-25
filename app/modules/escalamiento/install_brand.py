#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
install_brand.py - Instalador automático de nuevas marcas para SOLDASUR (v5.0.2)
=============================================================================
Ubicación: app/modules/escalamiento/install_brand.py
Lee la carpeta 'scraping/data_raw/<marca_lower>' en la raíz, compila el índice vectorial FAISS
y genera el código de consultas RAG + registro de configuraciones de forma 100% automática.
"""

import json
import os
import sys
import re
from pathlib import Path

# Configuración de Rutas (Subiendo 4 niveles desde app/modules/escalamiento/ hasta la raíz)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Obtener nombre de la marca (ej: Durlock o durlock)
input_folder = sys.argv[1] if len(sys.argv) > 1 else ""

if not input_folder:
    print("\n[ERROR] Debes proporcionar el nombre de la marca.")
    print("Ejemplo: python install_brand.py Durlock\n")
    sys.exit(1)

INPUT_DIR = BASE_DIR / "scraping" / "data_raw" / input_folder.lower().strip()
DATABASE_DIR = BASE_DIR / "RAG_engine" / "database"
QUERY_DIR = BASE_DIR / "RAG_engine" / "query"
CONFIGS_DIR = BASE_DIR / "configs"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def print_banner():
    print("=" * 75)
    print("      SOLDASUR S.A. - INSTALADOR AUTOMÁTICO DE NUEVAS MARCAS (v5.0.0)")
    print("=" * 75)


def check_dependencies():
    """Verifica que las librerías necesarias estén instaladas."""
    print("[1/5] Verificando dependencias...")
    missing = []
    
    try:
        import sentence_transformers
    except ImportError:
        missing.append("sentence-transformers")
        
    try:
        import faiss
    except ImportError:
        missing.append("faiss-cpu")
        
    try:
        import numpy
    except ImportError:
        missing.append("numpy")

    if missing:
        print(f"\n[ERROR] Faltan dependencias críticas: {', '.join(missing)}")
        print("Por favor, ejecutá el siguiente comando para instalarlas:")
        print("pip install sentence-transformers faiss-cpu numpy\n")
        sys.exit(1)
        
    print("  [OK] Dependencias verificadas exitosamente.")


def load_input_files():
    """Valida y carga los archivos de configuración y catálogo desde scraping/data_raw/<marca_lower>/."""
    brand_lower = input_folder.lower().strip()
    print(f"[2/5] Cargando archivos de entrada desde './scraping/data_raw/{brand_lower}'...")
    
    if not INPUT_DIR.exists():
        print(f"\n[ERROR] No se encontró la carpeta: {INPUT_DIR}")
        print("Asegúrate de haber creado la carpeta con el nombre de tu marca dentro de 'scraping/data_raw/'.")
        print("Estructura requerida:")
        print(f"  scraping/data_raw/{brand_lower}/config.json")
        print(f"  scraping/data_raw/{brand_lower}/<brand>_catalog.json (o catalog.json)")
        sys.exit(1)

    config_path = INPUT_DIR / "config.json"
    if not config_path.exists():
        print(f"\n[ERROR] No se encontró el archivo: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"\n[ERROR] Error leyendo 'config.json': {e}")
        sys.exit(1)

    # Validar campos obligatorios en config
    required_keys = ["brand_key", "display_name", "direct_keywords", "anchor_text", "system_prompt"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        print(f"\n[ERROR] Faltan campos obligatorios en 'config.json': {', '.join(missing_keys)}")
        sys.exit(1)

    # Limpiar y normalizar clave de marca
    config["brand_key"] = config["brand_key"].upper().strip()
    config["brand_lower"] = config["brand_key"].lower()
    brand_lower = config["brand_lower"]

    # Buscar el catálogo (marca_catalog.json o catalog.json)
    specific_catalog_path = INPUT_DIR / f"{brand_lower}_catalog.json"
    generic_catalog_path = INPUT_DIR / "catalog.json"

    if specific_catalog_path.exists():
        catalog_path = specific_catalog_path
    elif generic_catalog_path.exists():
        catalog_path = generic_catalog_path
    else:
        print(f"\n[ERROR] No se encontró el catálogo de productos.")
        print(f"Se buscó en:\n  - {specific_catalog_path}\n  - {generic_catalog_path}")
        sys.exit(1)

    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    except Exception as e:
        print(f"\n[ERROR] Error leyendo '{catalog_path.name}': {e}")
        sys.exit(1)
    
    print(f"  [OK] Configuración cargada para la marca: {config['display_name']} ({config['brand_key']})")
    print(f"  [OK] Catálogo cargado desde '{catalog_path.name}': {len(catalog)} productos detectados.")
    
    return config, catalog


def get_applications_robust(product: dict) -> list:
    """Extrae de forma robusta las aplicaciones de un producto con fallback a múltiples claves y formatos."""
    raw_apps = (
        product.get("aplicar") or 
        product.get("aplicacion") or 
        product.get("aplicaciones") or 
        product.get("applications")
    )
    if not raw_apps:
        return []
        
    if isinstance(raw_apps, list):
        normalized = []
        for item in raw_apps:
            if isinstance(item, dict):
                val = item.get("nombre") or item.get("slug")
                if val:
                    normalized.append(str(val))
            elif item:
                normalized.append(str(item))
        return normalized
    elif isinstance(raw_apps, dict):
        val = raw_apps.get("nombre") or raw_apps.get("slug")
        return [str(val)] if val else []
    elif isinstance(raw_apps, str):
        return [x.strip() for x in re.split(r'[,;\n]+', raw_apps) if x.strip()]
        
    return []


def build_chunk_text(product: dict, brand_display: str = "General") -> str:
    """Construye el texto semántico que se utilizará para embedear un producto."""
    # Priorizar categories_processed (amigable/estilizada)
    category = None
    processed_cats = product.get("categories_processed")
    if isinstance(processed_cats, list) and processed_cats:
        category = processed_cats[0]
    elif isinstance(processed_cats, str) and processed_cats:
        category = processed_cats
        
    if not category:
        category = product.get("category")
        
    if not category:
        cats = product.get("categories")
        if isinstance(cats, list) and cats:
            category = cats[0].replace("-", " ").title()
        elif isinstance(cats, str) and cats:
            category = cats.replace("-", " ").title()
            
    if not category:
        category = product.get("family", "General")

    partes = [
        f"Producto: {product.get('model', product.get('name', product.get('model_name', '')))}",
        f"Categoría: {category}",
        f"Descripción: {product.get('description', '')}",
    ]
    
    if product.get("advantages"):
        adv = product.get("advantages")
        if isinstance(adv, list):
            partes.append("Beneficios: " + " | ".join(adv[:5]))
        elif isinstance(adv, str):
            partes.append(f"Beneficios: {adv}")

    if product.get("technical_features"):
        tf = product.get("technical_features")
        if isinstance(tf, list):
            partes.append("Características: " + " | ".join(tf[:5]))
        elif isinstance(tf, str):
            partes.append(f"Características: {tf}")

    # Obtener aplicaciones de forma robusta e incluirlas en el chunk semántico
    apps = get_applications_robust(product)
    if apps:
        partes.append("Aplicaciones: " + ", ".join(apps))

    # Obtener presentación de forma robusta
    presentacion = product.get("presentacion")
    if not presentacion:
        specs = product.get("specifications", {})
        for k, v in specs.items():
            if any(x in k.lower() for x in ["placa", "espesor", "formato"]):
                presentacion = f"{k}: {v}"
                break
    if not presentacion:
        presentacion = f"Insumo {brand_display}"

    partes.append(f"Presentación: {presentacion}")

    return "\n".join(partes)


def compile_vector_db(config: dict, catalog: list):
    """Genera los embeddings de los productos y escribe los archivos FAISS y metadata JSON."""
    brand_lower = config["brand_lower"]
    display_name = config["display_name"]
    
    faiss_out = DATABASE_DIR / f"products_{brand_lower}.faiss"
    meta_out = DATABASE_DIR / f"metadata_{brand_lower}.json"

    print(f"[3/5] Compilando base de datos vectorial para '{display_name}'...")
    
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    texts = []
    metadata = []

    for product in catalog:
        text = build_chunk_text(product, display_name)
        texts.append(text)
        
        # Priorizar categories_processed (amigable/estilizada)
        category = None
        processed_cats = product.get("categories_processed")
        if isinstance(processed_cats, list) and processed_cats:
            category = processed_cats[0]
        elif isinstance(processed_cats, str) and processed_cats:
            category = processed_cats
            
        if not category:
            category = product.get("category")
            
        if not category:
            cats = product.get("categories")
            if isinstance(cats, list) and cats:
                category = cats[0].replace("-", " ").title()
            elif isinstance(cats, str) and cats:
                category = cats.replace("-", " ").title()
                
        if not category:
            category = product.get("family", "General")

        # Obtener presentación de forma robusta
        presentacion = product.get("presentacion")
        if not presentacion:
            specs = product.get("specifications", {})
            for k, v in specs.items():
                if any(x in k.lower() for x in ["placa", "espesor", "formato"]):
                    presentacion = f"{k}: {v}"
                    break
        if not presentacion:
            presentacion = f"Insumo {display_name}"

        # Guardar en metadatos limpios para consumo del frontend
        metadata.append({
            "model":       product.get("model", product.get("name", product.get("model_name", "Producto"))),
            "description": product.get("description", ""),
            "category":    category,
            "url":         product.get("url", "#"),
            "brand":       display_name,
            "presentacion":presentacion,
            "imagen_local": product.get("imagen_local", ""),
            "imagen_url":   product.get("imagen_url", ""),
            "applications": get_applications_robust(product),
        })

    print(f"  -> Generando embeddings para {len(texts)} productos con el modelo: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalizar para similitud coseno
    faiss.normalize_L2(embeddings)

    # Crear índice FAISS
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Guardar archivos
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(faiss_out))
    
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"  [OK] Índice FAISS guardado en: {faiss_out}")
    print(f"  [OK] Catálogo formateado guardado en: {meta_out}")


def create_rag_code(config: dict):
    """Crea los archivos RAG de query y LLM autogenerados a partir de plantillas."""
    brand_lower = config["brand_lower"]
    brand_upper = config["brand_key"]
    brand_display = config["display_name"]
    
    query_file = QUERY_DIR / f"rag_query_{brand_lower}.py"
    llm_file = QUERY_DIR / f"rag_llm_{brand_lower}.py"

    print(f"[4/5] Generando scripts RAG para '{brand_display}'...")

    # Template para modulo RAG QUERY
    query_template = f'''"""
rag_query_{brand_lower}.py – Buscador vectorial (Retriever) para productos {brand_display}.
AUTOGENERADO POR install_brand.py
"""

import json
import re
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import faiss
    FAISS_OK = True
except ImportError:
    FAISS_OK = False

try:
    from sentence_transformers import SentenceTransformer
    ST_OK = True
except ImportError:
    ST_OK = False


# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FAISS_PATH = SCRIPT_DIR.parent / "database" / "products_{brand_lower}.faiss"
META_PATH  = SCRIPT_DIR.parent / "database" / "metadata_{brand_lower}.json"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ── Singleton del modelo (carga una sola vez) ─────────────────────────────────
_model = None
_index = None
_metadata = None


def _load_resources():
    """Carga el modelo y el índice FAISS (lazy loading)."""
    global _model, _index, _metadata

    if _model is None and ST_OK:
        print("[{brand_display}RAG] Cargando modelo de embeddings...")
        _model = SentenceTransformer(MODEL_NAME)

    if _index is None and FAISS_OK:
        if Path(FAISS_PATH).exists():
            _index = faiss.read_index(str(FAISS_PATH))
            with open(META_PATH, encoding="utf-8") as f:
                _metadata = json.load(f)
            print(f"[{brand_display}RAG] Índice cargado: {{_index.ntotal}} productos {brand_display}")
        else:
            print(f"[{brand_display}RAG] AVISO: No se encontró {{FAISS_PATH}}")


def search_{brand_lower}(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca productos {brand_display} relevantes para la consulta.
    Retorna lista de dicts con información del producto y score de similitud.
    """
    _load_resources()

    if _model is None or _index is None:
        return _fallback_search(query, top_k)

    # Generar embedding de la consulta
    query_vec = _model.encode([query], convert_to_numpy=True)
    faiss.normalize_L2(query_vec)

    # Buscar en el índice
    scores, indices = _index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        product = _metadata[idx].copy()
        product["similarity_score"] = float(score)
        results.append(product)

    return results


def _fallback_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Búsqueda por texto simple si FAISS no está disponible."""
    if _metadata is None:
        try:
            with open(META_PATH, encoding="utf-8") as f:
                meta = json.load(f)
        except FileNotFoundError:
            return []
    else:
        meta = _metadata

    query_lower = query.lower()
    scored = []
    for product in meta:
        apps_str = " ".join(product.get("applications", []))
        text = f"{{product.get('model','')}} {{product.get('description','')}} {{product.get('category','')}} {{apps_str}}".lower()
        score = sum(1 for word in query_lower.split() if word in text)
        if score > 0:
            p = product.copy()
            p["similarity_score"] = score
            scored.append(p)

    scored.sort(key=lambda x: x["similarity_score"], reverse=True)
    return scored[:top_k]


def get_{brand_lower}_product_by_model(model_name: str) -> Optional[Dict[str, Any]]:
    """Busca y retorna un producto del catálogo por su nombre de modelo (case-insensitive)."""
    _load_resources()
    if _metadata:
        model_lower = model_name.lower().strip()
        for p in _metadata:
            if p.get("model", "").lower().strip() == model_lower:
                return p
    return None
'''

    # Template para modulo RAG LLM
    system_prompt_escaped = config["system_prompt"].replace('"""', '\\"\\"\\"')
    
    llm_template = f'''"""
rag_llm_{brand_lower}.py – Generador RAG / LLM para productos {brand_display}.
AUTOGENERADO POR install_brand.py
"""

import requests
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .rag_query_{brand_lower} import search_{brand_lower}, get_{brand_lower}_product_by_model

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def _load_configured_model() -> str:
    """Carga el modelo configurado en configs/models.json con fallback a llama3.2:3b"""
    models_path = Path(__file__).resolve().parent.parent.parent / "configs" / "models.json"
    if models_path.exists():
        try:
            with open(models_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ollama_model", "llama3.2:3b")
        except Exception:
            pass
    return "llama3.2:3b"


# Estandarizamos el System Prompt por defecto (fallback)
SYSTEM_PROMPT_{brand_upper}_DEFAULT = """{system_prompt_escaped}"""


def _load_prompt_config() -> Dict[str, Any]:
    """Carga la configuración de prompts del archivo configs/prompts.json."""
    config_path = Path(__file__).resolve().parent.parent.parent / "configs" / "prompts.json"
    
    # Valores por defecto de fallback
    default_config = {{
        "system_prompt": SYSTEM_PROMPT_{brand_upper}_DEFAULT,
        "temperature": {config.get("temperature", 0.2)},
        "max_tokens": {config.get("max_tokens", 250)}
    }}
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("{brand_lower}", default_config)
        except Exception as e:
            print(f"[{brand_display}RAG] Error cargando configs/prompts.json ({{e}}). Usando fallback.")
    return default_config


def answer_{brand_lower}(
    query: str,
    context_products: List[Dict[str, Any]],
    last_active_product: Optional[str] = None
) -> str:
    """
    Genera una respuesta usando Ollama con los productos {brand_display} como contexto.
    """
    if not context_products:
        return "No encontré productos de {brand_display} para tu consulta en este momento."

    # Construir contexto de productos
    context_lines = []
    for p in context_products[:2]:  # Top 2 productos
        linea = f"- {{p.get('model','')}}: {{p.get('description','')}}"
        if p.get("presentacion"):
            linea += f" | Presentación: {{p['presentacion']}}"
        context_lines.append(linea)

    prompt = f"""Productos {brand_display} relevantes:
{{chr(10).join(context_lines)}}
"""
    if last_active_product:
        prompt += f"\\nContexto de conversación: El usuario estaba hablando o recibió recomendación sobre '{{last_active_product}}'. Si la consulta es una pregunta de seguimiento, responde asumiendo que se refiere a este producto."

    prompt += f"\\nConsulta del cliente: {{query}}\\n\\nRespuesta:"

    # Cargar prompts y configuraciones parametrizadas
    config = _load_prompt_config()
    model = _load_configured_model()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={{
                "model": model,
                "prompt": prompt,
                "system": config.get("system_prompt", SYSTEM_PROMPT_{brand_upper}_DEFAULT),
                "stream": False,
                "options": {{
                    "num_predict": config.get("max_tokens", 250),
                    "temperature": config.get("temperature", 0.2)
                }}
            }},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        print(f"[{brand_display}RAG] Error Ollama: {{e}}")

    return _format_fallback_response(context_products)


def _format_fallback_response(products: List[Dict[str, Any]]) -> str:
    """Respuesta de fallback cuando Ollama no está disponible."""
    if not products:
        return "Soy el asistente de SOLDASUR. No encontré productos de {brand_display} para tu consulta."

    p = products[0]
    return f"Hola, para tu consulta sobre {brand_display}, te recomiendo **{{p.get('model','')}}**: {{p.get('description','')}}"


SIMILARITY_THRESHOLD = 0.25


def _filter_by_relevance(
    productos: List[Dict[str, Any]],
    min_score: float = SIMILARITY_THRESHOLD,
    keep_at_least: int = 1
) -> List[Dict[str, Any]]:
    """Filtra productos por similarity_score."""
    filtered = [p for p in productos if p.get("similarity_score", 0) >= min_score]
    if not filtered and productos:
        filtered = productos[:keep_at_least]
    return filtered


def search_and_answer(
    query: str,
    last_active_product: Optional[str] = None,
    top_k: int = 3
) -> Dict[str, Any]:
    """Función de alto nivel para RAG dinámico."""
    productos = search_{brand_lower}(query, top_k)
    productos = _filter_by_relevance(productos)

    effective_last_active = None
    if last_active_product:
        p_activo = get_{brand_lower}_product_by_model(last_active_product)
        if p_activo:
            productos = [p for p in productos if p.get("model", "").lower().strip() != last_active_product.lower().strip()]
            productos.insert(0, p_activo)
            effective_last_active = last_active_product

    respuesta = answer_{brand_lower}(query, productos, effective_last_active)
    productos_frontend = productos[:2] if productos else []

    return {{
        "respuesta": respuesta,
        "productos": productos_frontend,
        "marca": "{brand_display}"
    }}
'''

    QUERY_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(query_file, "w", encoding="utf-8") as f:
        f.write(query_template)
    print(f"  [OK] Buscador guardado en: {query_file}")
    
    with open(llm_file, "w", encoding="utf-8") as f:
        f.write(llm_template)
    print(f"  [OK] Inferencia LLM guardada en: {llm_file}")


def register_brand_configurations(config: dict):
    """Agrega la nueva marca en configs/brands_registry.json y configs/prompts.json."""
    brand_key = config["brand_key"]
    brand_lower = config["brand_lower"]
    display_name = config["display_name"]
    
    registry_path = CONFIGS_DIR / "brands_registry.json"
    prompts_path = CONFIGS_DIR / "prompts.json"

    print(f"[5/5] Registrando configuraciones en './configs'...")

    # 1. Actualizar configs/brands_registry.json
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = {"brands": {}}

    registry["brands"][brand_key] = {
        "key": brand_key,
        "display_name": display_name,
        "intent_type": f"{brand_lower}_query",
        "direct_keywords": [kw.lower().strip() for kw in config["direct_keywords"]],
        "anchor_text": config["anchor_text"],
        "rag_module": f"RAG_engine.query.rag_llm_{brand_lower}",
        "rag_function": "search_and_answer",
        "response_formatter": "generic",
        "has_calculator": config.get("has_calculator", False),
        "calculator_display": config.get("calculator_display", f"Calculadora {display_name}")
    }

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Marca '{brand_key}' agregada a {registry_path}")

    # 2. Actualizar configs/prompts.json
    if prompts_path.exists():
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts = json.load(f)
    else:
        prompts = {}

    prompts[brand_lower] = {
        "system_prompt": config["system_prompt"],
        "temperature": config.get("temperature", 0.2),
        "max_tokens": config.get("max_tokens", 250)
    }

    with open(prompts_path, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Prompt de '{brand_lower}' agregado a {prompts_path}")


def copy_calculator_and_logo(config: dict):
    """Copia la base de conocimiento y el motor del sistema experto si has_calculator es True, y copia el logo si existe."""
    brand_lower = config["brand_lower"]
    display_name = config["display_name"]
    
    # 1. Copiar Logo
    logo_file = None
    if INPUT_DIR.exists():
        for f_path in INPUT_DIR.iterdir():
            if f_path.is_file() and 'logo' in f_path.name.lower():
                logo_file = f_path
                break
            
    if logo_file:
        dest_logo = BASE_DIR / "web_app" / "img" / f"{brand_lower}-logo.png"
        import shutil
        try:
            shutil.copy(logo_file, dest_logo)
            print(f"  [OK] Logo de marca copiado a: {dest_logo}")
        except Exception as e:
            print(f"  [WARNING] Error copiando logo: {e}")
    else:
        print(f"  [WARNING] No se encontró logo en la carpeta de origen. Se recomienda agregar un archivo conteniendo 'logo' en su nombre.")

    # 2. Copiar Sistema Experto (Calculadora)
    if config.get("has_calculator", False):
        print(f"Instalando sistema experto para '{display_name}'...")
        kb_src = INPUT_DIR / "calculator_kb.json"
        engine_src = INPUT_DIR / "calculator_engine.py"
        
        kb_dest = BASE_DIR / "app" / f"advisor_knowledge_base_{brand_lower}.json"
        engine_dest = BASE_DIR / "app" / "modules" / "expertSystem" / f"expert_engine_{brand_lower}.py"
        
        if not kb_src.exists():
            print(f"\n[ERROR] Se especificó has_calculator=true pero no se encontró la base de conocimiento: {kb_src}")
            sys.exit(1)
        if not engine_src.exists():
            print(f"\n[ERROR] Se especificó has_calculator=true pero no se encontró el motor: {engine_src}")
            sys.exit(1)
            
        import shutil
        try:
            shutil.copy(kb_src, kb_dest)
            print(f"  [OK] Base de conocimiento experta copiada a: {kb_dest}")
            shutil.copy(engine_src, engine_dest)
            print(f"  [OK] Motor experto copiado a: {engine_dest}")
        except Exception as e:
            print(f"\n[ERROR] Error instalando archivos del sistema experto: {e}")
            sys.exit(1)


def main():
    print_banner()
    check_dependencies()
    config, catalog = load_input_files()
    compile_vector_db(config, catalog)
    create_rag_code(config)
    copy_calculator_and_logo(config)
    register_brand_configurations(config)
    
    print("=" * 75)
    print(f" [OK] INSTALACION EXITOSA! La marca '{config['display_name']}' esta ahora en el chat.")
    print(" Reinicia el servidor de Uvicorn si no cargo los cambios automaticamente.")
    print("=" * 75)


if __name__ == "__main__":
    main()
