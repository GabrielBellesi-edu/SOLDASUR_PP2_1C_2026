"""
ingest.py – crea índice FAISS + catálogo SQLite a partir de un CSV

Uso:
    python ingest.py data/processed/products_mock.csv
Requisitos:
    pip install sentence-transformers faiss-cpu pandas tqdm
"""
import sys, os, sqlite3, faiss
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pathlib import Path

MODEL_NAME = "sentence-transformers/distiluse-base-multilingual-cased-v2"

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH    = SCRIPT_DIR.parent / "embeddings" / "products.db"
INDEX_PATH = SCRIPT_DIR.parent / "embeddings" / "products.faiss"

# ────────────────────────────────────────────────────────────────────────────
def normalize_text(row) -> str:
    """Concatena campos semánticos + numéricos para el embedding."""
    parts = [
        str(row.get("type_en")  or row.get("type")),
        str(row.get("family_en")or row.get("family")),
        str(row.get("model_en") or row.get("model")),
        str(row.get("description_en") or row.get("description")),
        f"{row.get('power_w', '')} watts",
        f"{row.get('liters', '')} liters",
        f"{row.get('max_pressure_bar', '')} bar",
        str(row.get("category", "")),
    ]
    return " ".join(p for p in parts if p and p != "nan").strip()

def build_sqlite(df, path=DB_PATH):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    df.to_sql("products", conn, index=False)
    conn.close()

def build_faiss(embeddings, path=INDEX_PATH):
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)          # cosine ≈ dot-product sobre vectores L2
    index.add(embeddings)
    faiss.write_index(index, str(path))

# ────────────────────────────────────────────────────────────────────────────
def main(csv_path):
    if not os.path.exists(csv_path):
        print(f"CSV {csv_path} not found")
        return

    print("Loading CSV …")
    df    = pd.read_csv(csv_path)
    texts = [normalize_text(r) for _, r in df.iterrows()]

    print(f"Generating embeddings with {MODEL_NAME} …")
    model      = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        batch_size=64,
        normalize_embeddings=True        # ⬅️  L2 = 1 desde aquí
    ).astype("float32")

    print("Saving SQLite database …")
    build_sqlite(df)

    print("Building FAISS index …")
    build_faiss(embeddings)

    print(f"Done! Saved\n  • {DB_PATH}\n  • {INDEX_PATH}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <csv_file>")
        sys.exit(1)
    main(sys.argv[1])
