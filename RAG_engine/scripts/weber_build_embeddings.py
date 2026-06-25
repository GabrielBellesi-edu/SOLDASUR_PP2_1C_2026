"""
weber_build_embeddings.py  –  Generación de embeddings Weber (Paso 2)
==================================================================
Lee web_app/data/weber_catalog.json y genera embeddings con SentenceTransformers,
guardando el índice FAISS en RAG_engine/database/products_weber.faiss
y los metadatos en RAG_engine/database/metadata_weber.json.
"""

import json
import os
import numpy as np
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    ST_OK = True
except ImportError:
    ST_OK = False

try:
    import faiss
    FAISS_OK = True
except ImportError:
    FAISS_OK = False


SCRIPT_DIR = Path(__file__).resolve().parent
CATALOG_PATH = SCRIPT_DIR.parent.parent / "web_app" / "data" / "weber_catalog.json"
FAISS_PATH   = SCRIPT_DIR.parent / "database" / "products_weber.faiss"
META_PATH    = SCRIPT_DIR.parent / "database" / "metadata_weber.json"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def build_chunk_text(product: dict) -> str:
    """
    Construye el texto que se va a embedear para un producto.
    Combina los campos más relevantes para la búsqueda semántica.
    """
    partes = [
        f"Producto: {product.get('model', '')}",
        f"Categoría: {product.get('category', '')}",
        f"Descripción: {product.get('description', '')}",
    ]

    if product.get("descripcion_larga"):
        partes.append(f"Detalles: {product['descripcion_larga']}")

    if product.get("advantages"):
        partes.append("Beneficios: " + " | ".join(product["advantages"][:5]))

    if product.get("technical_features"):
        partes.append("Características: " + " | ".join(product["technical_features"][:5]))

    if product.get("rendimiento"):
        partes.append(f"Rendimiento: {product['rendimiento']}")

    if product.get("presentacion"):
        partes.append(f"Presentación: {product['presentacion']}")

    if product.get("soporte"):
        partes.append("Soportes: " + ", ".join(product["soporte"]))

    if product.get("colores"):
        partes.append("Colores disponibles: " + ", ".join(product["colores"]))

    # Si tiene texto de PDF, agregar los primeros 500 chars (muy relevante)
    if product.get("pdf_text"):
        partes.append(product["pdf_text"][:500])

    return "\n".join(partes)

def build_embeddings():
    if not ST_OK:
        print("ERROR: sentence-transformers no instalado.")
        return

    if not FAISS_OK:
        print("ERROR: faiss-cpu no instalado.")
        return

    # Cargar catálogo
    if not CATALOG_PATH.exists():
        print(f"ERROR: No se encontró {CATALOG_PATH}")
        print("       Ejecutar primero: python weber_build_catalog.py")
        return

    with open(CATALOG_PATH, encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"[Weber Embeddings] Cargando catálogo: {len(catalog)} productos Weber")

    # Construir textos para embedding
    texts = []
    metadata = []

    for product in catalog:
        text = build_chunk_text(product)
        texts.append(text)
        metadata.append({
            "model":       product.get("model", ""),
            "description": product.get("description", ""),
            "descripcion_larga": product.get("descripcion_larga", ""),
            "category":    product.get("category", ""),
            "url":         product.get("url", ""),
            "brand":       "Weber",
            "rendimiento": product.get("rendimiento", ""),
            "presentacion":product.get("presentacion", ""),
            "tiempo_secado":product.get("tiempo_secado", ""),
            "soporte":     product.get("soporte", []),
            "colores":     product.get("colores", []),
            "advantages":  product.get("advantages", []),
            "restricciones": product.get("restricciones", []),
            "filtros":     product.get("filtros", {}),
            "atributos_tecnicos": product.get("atributos_tecnicos", {}),
            "imagen_local": product.get("imagen_local", ""),
            "imagen_url":   product.get("imagen_url", ""),
            "pdf_text_snippet": product.get("pdf_text", "")[:800],
        })

    # Generar embeddings
    print(f"[Weber Embeddings] Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"[Weber Embeddings] Generando embeddings para {len(texts)} productos...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalizar para búsqueda por similitud coseno
    faiss.normalize_L2(embeddings)

    # Crear índice FAISS
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = cosine similarity tras normalización
    index.add(embeddings)

    print(f"[Weber Embeddings] Índice FAISS creado: {index.ntotal} vectores de dimensión {dim}")

    # Guardar índice y metadatos
    FAISS_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[OK] [Weber Embeddings] Índice guardado en: {FAISS_PATH}")
    print(f"     Metadatos en:       {META_PATH}")

if __name__ == "__main__":
    build_embeddings()
