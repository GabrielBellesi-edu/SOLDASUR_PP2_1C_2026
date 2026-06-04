"""
ingest.py – Orquestador central de ingesta RAG para SOLDASUR v4.2.0.
====================================================================
Uso:
    python RAG_engine/scripts/ingest.py --peisa
    python RAG_engine/scripts/ingest.py --weber
    python RAG_engine/scripts/ingest.py --all
"""

import sys
import argparse
from pathlib import Path

# Agregar el directorio actual al path de búsqueda de Python para permitir imports relativos y absolutos
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from peisa_ingest import run_peisa_ingest
except ImportError as e:
    print(f"Error al importar peisa_ingest: {e}")
    run_peisa_ingest = None

try:
    from weber_build_catalog import build_catalog
    from weber_build_embeddings import build_embeddings
except ImportError as e:
    print(f"Error al importar weber scripts: {e}")
    build_catalog = None
    build_embeddings = None


def main():
    parser = argparse.ArgumentParser(description="Orquestador de Ingesta RAG - SOLDASUR")
    parser.add_argument("--peisa", action="store_true", help="Ejecuta la ingesta del catálogo de PEISA (calefacción)")
    parser.add_argument("--weber", action="store_true", help="Ejecuta la ingesta del catálogo de Weber (construcción)")
    parser.add_argument("--all", action="store_true", help="Ejecuta la ingesta de todas las marcas")
    
    args = parser.parse_args()

    # Si no se proveen argumentos, mostrar ayuda
    if not (args.peisa or args.weber or args.all):
        parser.print_help()
        sys.exit(0)

    ejecuto_algo = False

    if args.peisa or args.all:
        print("\n=== INICIANDO INGESTA PEISA ===")
        if run_peisa_ingest:
            run_peisa_ingest()
        else:
            print("[ERROR] No se pudo ejecutar peisa_ingest por problemas de importación.")
        ejecuto_algo = True

    if args.weber or args.all:
        print("\n=== INICIANDO INGESTA WEBER ===")
        if build_catalog and build_embeddings:
            print("[Weber Ingest] Paso 1: Consolidación de Catálogo...")
            build_catalog("scraping/data_raw/weber", "web_app/data/weber_catalog.json")
            print("\n[Weber Ingest] Paso 2: Generación de Embeddings e Indexación...")
            build_embeddings()
        else:
            print("[ERROR] No se pudieron ejecutar los scripts de Weber por problemas de importación.")
        ejecuto_algo = True

    if ejecuto_algo:
        print("\n=== PROCESO DE INGESTA FINALIZADO ===")


if __name__ == "__main__":
    main()
