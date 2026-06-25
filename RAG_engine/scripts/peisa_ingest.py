"""
peisa_ingest.py – Ingesta para PEISA a partir de peisa_catalog.json.
Genera products_peisa.db y products_peisa.faiss.
"""

import os
import json
import sqlite3
import faiss
from pathlib import Path
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/distiluse-base-multilingual-cased-v2"

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH    = SCRIPT_DIR.parent / "database" / "products_peisa.db"
INDEX_PATH = SCRIPT_DIR.parent / "database" / "products_peisa.faiss"
CATALOG_PATH = SCRIPT_DIR.parent.parent / "web_app" / "data" / "peisa_catalog.json"

def normalize_text(p) -> str:
    """Concatena campos semánticos y numéricos para generar el embedding."""
    parts = [
        str(p.get("type") or ""),
        str(p.get("family") or ""),
        str(p.get("model") or ""),
        str(p.get("description") or ""),
        f"{p.get('power_w')} watts" if p.get('power_w') else "",
        f"{p.get('liters')} liters" if p.get('liters') else "",
        f"{p.get('max_pressure_bar')} bar" if p.get('max_pressure_bar') else "",
        str(p.get("category") or ""),
    ]
    return " ".join(part for part in parts if part).strip()

def run_peisa_ingest():
    if not CATALOG_PATH.exists():
        print(f"[ERROR] [PEISA Ingest] No se encontró el catálogo en {CATALOG_PATH}")
        return

    print(f"[PEISA Ingest] Cargando catálogo desde {CATALOG_PATH} ...")
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        products = json.load(f)

    # Asegurar el tipado correcto y campos requeridos para la base de datos
    mapped_products = []
    texts = []
    for p in products:
        mapped = {
            "type": p.get("type") or "",
            "family": p.get("family") or "",
            "model": p.get("model") or "",
            "description": p.get("description") or "",
            "dimentions": p.get("dimentions") or p.get("dimensions") or "",
            "power_w": float(p.get("power_w") or 0.0),
            "liters": float(p.get("liters") or 0.0),
            "max_pressure_bar": float(p.get("max_pressure_bar") or 0.0),
            "category": p.get("category") or "",
            "subcategory": p.get("subcategory") or "",
            "url": p.get("url") or ""
        }
        mapped_products.append(mapped)
        texts.append(normalize_text(mapped))

    print(f"[PEISA Ingest] Generando embeddings con el modelo {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=64,
        normalize_embeddings=True
    ).astype("float32")

    print("[PEISA Ingest] Creando y poblando base de datos SQLite ...")
    if DB_PATH.exists():
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE products (
            type TEXT,
            family TEXT,
            model TEXT,
            description TEXT,
            dimentions TEXT,
            power_w REAL,
            liters REAL,
            max_pressure_bar REAL,
            category TEXT,
            subcategory TEXT,
            url TEXT
        )
    """)
    for p in mapped_products:
        cursor.execute("""
            INSERT INTO products (type, family, model, description, dimentions, power_w, liters, max_pressure_bar, category, subcategory, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            p["type"], p["family"], p["model"], p["description"], p["dimentions"],
            p["power_w"], p["liters"], p["max_pressure_bar"], p["category"], p["subcategory"], p["url"]
        ))
    conn.commit()
    conn.close()

    print("[PEISA Ingest] Creando índice FAISS ...")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Similitud del coseno (vectores normalizados L2)
    index.add(embeddings)
    faiss.write_index(index, str(INDEX_PATH))

    print(f"[OK] [PEISA Ingest] Ingesta completada con éxito:")
    print(f"  • Base de datos: {DB_PATH}")
    print(f"  • Índice vectorial: {INDEX_PATH}")

if __name__ == "__main__":
    run_peisa_ingest()
