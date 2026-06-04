"""
query.py – busca en el índice FAISS y aplica filtrado estructurado.

Uso:
    python query.py "¿Tienen calderas de más de 17000 W?" [-k 5]
"""

import sys, argparse, re, sqlite3, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from rich.table import Table
from rich import print

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH    = SCRIPT_DIR.parent / "embeddings" / "products.db"
INDEX_PATH = SCRIPT_DIR.parent / "embeddings" / "products.faiss"
MODEL_NAME = "sentence-transformers/distiluse-base-multilingual-cased-v2"

TOP_K_DEFAULT = 3
SEARCH_POOL_K = 80           # se recuperan más, luego se filtra

# ────────────────────────────────────────────────────────────────────────────
def _extract_watts(text: str) -> float | None:
    """Detecta “17000 W”, “17 kW”, “18.5KW” … y los pasa a watts."""
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(k?m?)\s*w", text, flags=re.I)
    if not m:
        return None
    val = float(m.group(1).replace(",", "."))
    factor = m.group(2).lower()
    if factor == "kw":
        val *= 1_000
    elif factor == "mw":
        val *= 1_000_000
    return val

def _embed(text: str, model):
    return model.encode([text], normalize_embeddings=True).astype("float32")

def _fetch_rows(conn, ids):
    ph = ",".join("?" * len(ids))
    sql = f"""
        SELECT rowid, type, family, model, description,
               dimentions, power_w, liters, max_pressure_bar
        FROM products WHERE rowid IN ({ph})
    """
    rows = conn.execute(sql, ids).fetchall()
    return {r[0]: r[1:] for r in rows}

# ────────────────────────────────────────────────────────────────────────────
def search_filtered(question: str, top_k: int = TOP_K_DEFAULT):
    """
    Devuelve una lista de dicts con los mejores productos,
    aplicando filtro por potencia y tipo “caldera” si procede.
    """
    watts_req   = _extract_watts(question)
    want_boiler = "caldera" in question.lower()

    # recursos singleton
    global _IDX, _MODEL, _CONN
    if "_IDX" not in globals():
        _MODEL = SentenceTransformer(MODEL_NAME)
        _IDX   = faiss.read_index(str(INDEX_PATH))
        _CONN  = sqlite3.connect(str(DB_PATH))

    D, I = _IDX.search(_embed(question, _MODEL), SEARCH_POOL_K)

    valid_idxs = [i for i in I[0] if i != -1]
    rows = _fetch_rows(_CONN, [int(i)+1 for i in I[0]])  # FAISS usa índices 0-based, SQLite rowid es 1-based

    resultados = []
    for idx, dist in zip(valid_idxs, D[0]):
        rowid = int(idx) + 1  # FAISS usa índices 0-based, SQLite rowid es 1-based
        if rowid not in rows:
            continue
        (
            typ, fam, mod, desc,
            dims, pwr, lts, pbar
        ) = rows[rowid]

        if want_boiler and typ.lower() != "caldera":
            continue
        if watts_req and (pwr or 0) < watts_req:
            continue

        resultados.append({
            "type": typ,
            "family": fam,
            "model": mod,
            "description": desc,
            "dimentions": dims,
            "power_w": pwr,
            "liters": lts,
            "max_pressure_bar": pbar,
            "score": float(dist)          # útil para debug / orden
        })
        if len(resultados) == top_k:
            break
    return resultados

# ────────────────────────────────────────────────────────────────────────────
def _cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("-k", "--top_k", type=int, default=TOP_K_DEFAULT)
    args = ap.parse_args()

    hits = search_filtered(args.question, args.top_k)

    tbl = Table(title="Resultados filtrados")
    tbl.add_column("Rank"); tbl.add_column("Type")
    tbl.add_column("Model"); tbl.add_column("Power (W)")
    tbl.add_column("Descripción", overflow="fold")

    for i, p in enumerate(hits, 1):
        tbl.add_row(str(i), p["type"], p["model"],
                    str(p["power_w"]), p["description"][:60]+"…")
    print(tbl)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python query.py \"<pregunta>\"")
        sys.exit(1)
    _cli()