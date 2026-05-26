"""
02_build_embeddings.py  –  Generación de embeddings Weber (Paso 2)
==================================================================
Lee data/weber_catalog.json y genera embeddings con SentenceTransformers,
guardando el índice FAISS en embeddings/weber_products.faiss
y los metadatos en embeddings/weber_metadata.json.

Requiere el catálogo generado por 01_build_catalog.py.

Uso:
    python 02_build_embeddings.py

Instalar dependencias:
    pip install faiss-cpu sentence-transformers
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


CATALOG_PATH = "data/weber_catalog.json"
FAISS_PATH   = "embeddings/weber_products.faiss"
META_PATH    = "embeddings/weber_metadata.json"

# Mismo modelo que usa el sistema PEISA (mantener consistencia)
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

    # Si tiene texto de PDF, agregar los primeros 500 chars (muy relevante)
    if product.get("pdf_text"):
        partes.append(product["pdf_text"][:500])

    return "\n".join(partes)


def build_embeddings():
    if not ST_OK:
        print("ERROR: sentence-transformers no instalado.")
        print("       pip install sentence-transformers")
        return

    if not FAISS_OK:
        print("ERROR: faiss-cpu no instalado.")
        print("       pip install faiss-cpu")
        return

    # Cargar catálogo
    catalog_path = Path(CATALOG_PATH)
    if not catalog_path.exists():
        print(f"ERROR: No se encontró {CATALOG_PATH}")
        print("       Ejecutar primero: python 01_build_catalog.py")
        return

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"📦 Cargando catálogo: {len(catalog)} productos Weber")

    # Construir textos para embedding
    texts = []
    metadata = []

    for product in catalog:
        text = build_chunk_text(product)
        texts.append(text)
        metadata.append({
            "model":       product.get("model", ""),
            "description": product.get("description", ""),
            "category":    product.get("category", ""),
            "url":         product.get("url", ""),
            "brand":       "Weber",
            "rendimiento": product.get("rendimiento", ""),
            "presentacion":product.get("presentacion", ""),
            "tiempo_secado":product.get("tiempo_secado", ""),
            "soporte":     product.get("soporte", []),
            "advantages":  product.get("advantages", []),
            "restricciones": product.get("restricciones", []),
        })

    # Generar embeddings
    print(f"🤖 Cargando modelo: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print(f"⚙️  Generando embeddings para {len(texts)} productos...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalizar para búsqueda por similitud coseno
    faiss.normalize_L2(embeddings)

    # Crear índice FAISS
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = cosine similarity tras normalización
    index.add(embeddings)

    print(f"✅ Índice FAISS creado: {index.ntotal} vectores de dimensión {dim}")

    # Guardar índice y metadatos
    Path(FAISS_PATH).parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, FAISS_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"💾 Índice guardado en: {FAISS_PATH}")
    print(f"💾 Metadatos en:       {META_PATH}")
    print()
    print("✅ Embeddings listos. El RAG Weber puede usarlos.")


if __name__ == "__main__":
    build_embeddings()
