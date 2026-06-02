"""
01_build_catalog.py  –  Pipeline de ingestión Weber (Paso 1)
=============================================================
Lee los JSONs de productos Weber + los PDFs de la carpeta documents/
y genera un weber_catalog.json normalizado con la misma estructura
que el products_catalog.json de PEISA.

Uso:
    python 01_build_catalog.py --weber_data /ruta/a/weber_data

Salida:
    data/weber_catalog.json
"""

import json
import re
import os
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF  →  pip install pymupdf
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False
    print("AVISO: PyMuPDF no instalado. Los PDFs no se procesarán.")
    print("       Instalar con:  pip install pymupdf")


# ──────────────────────────────────────────────────────────────────────────────
# Mapeo de categorías Weber (URL keyword → categoría legible)
# ──────────────────────────────────────────────────────────────────────────────
CATEGORY_MAP = {
    "colocacion-ceramicas":     "Colocación de cerámicos y porcellanatos",
    "adhesivos-para-ceramicos": "Adhesivos para cerámicos",
    "adhesivos-para-porcellanatos": "Adhesivos para porcellanatos",
    "adhesivos-flexibles":      "Adhesivos flexibles y grandes formatos",
    "adhesivos-especificos":    "Adhesivos específicos",
    "empastinado":              "Pastinas",
    "limpieza-y-proteccion":    "Limpieza y protección",
    "revocar-paredes":          "Revoques y albañilería",
    "revoques-finos":           "Revoques finos",
    "revoques-manuales":        "Revoques manuales y proyectables",
    "soluciones-para-pisos":    "Pisos",
    "pisos-decorativos":        "Pisos decorativos",
    "carpetas-y-nivelacion":    "Carpetas y nivelación",
    "productos-complementarios":"Complementos para pisos",
    "impermeabilizantes":       "Impermeabilizantes",
    "soluciones-cementicias":   "Impermeabilizantes cementícios",
    "membranas-liquidas":       "Membranas líquidas",
    "tratamiento-de-humedad":   "Tratamiento de humedad",
    "aislacion-termica":        "Aislación térmica",
    "sistema-eifs":             "Sistema EIFS",
    "revoques-termoaislantes":  "Revoques termoaislantes",
    "reparacion-de-hormigon":   "Reparación de hormigón",
    "preparacion-de-superficies": "Pinturas y preparación",
    "pinturas":                 "Pinturas",
    "revestimientos-plasticos": "Revestimientos plásticos",
    "revestimientos-cementicios": "Revestimientos cementícios",
    "revestimiento-de-paredes": "Revestimientos de paredes",
    "revestimientos-decorativos": "Revestimientos decorativos",
    "anclaje-y-fijacion":       "Fijación y anclaje",
    "selladores-y-espumas":     "Selladores y espumas",
    "mezclas-de-asiento":       "Mezclas de asiento",
    "revoque-monocapa":         "Revoques monocapa",
}


def get_category(url: str) -> str:
    """Infiere la categoría del producto a partir de su URL."""
    url_lower = url.lower()
    for key, cat in CATEGORY_MAP.items():
        if key in url_lower:
            return cat
    return "General Weber"


def is_search_page(url: str) -> bool:
    """Detecta si la URL es una página de búsqueda/filtro (no una ficha de producto)."""
    return "/search-content/" in url


def clean_datos_tecnicos(raw: str) -> dict:
    """
    Extrae información estructurada del campo datos_tecnicos de los JSONs de producto.
    Devuelve un dict con: descripcion_corta, beneficios, restricciones, presentacion, soporte.
    """
    result = {
        "descripcion_corta": "",
        "beneficios": [],
        "restricciones": [],
        "presentacion": "",
        "soporte": [],
        "productos_relacionados": [],
    }

    if not raw:
        return result

    lines = [l.strip() for l in raw.splitlines() if l.strip()]

    # La descripción corta suele ser la primera línea con contenido real
    # (saltamos el breadcrumb de navegación)
    nav_keywords = {"inicio", "show gallery", "encontrá un distribuidor",
                    "calculadora de consumo", "documentación del producto",
                    "tutoriales y videos", "comenzar tutorial", "ver video",
                    "descargar", "enviar", "apply", "acerca de este producto"}

    content_lines = [l for l in lines if l.lower() not in nav_keywords
                     and not l.lower().startswith("(pdf")]

    # Buscar descripción corta (primera oración larga que no sea navegación)
    for line in content_lines:
        if len(line) > 30 and not any(k in line.lower() for k in ["buscar", "filtrar", "resetear"]):
            result["descripcion_corta"] = line
            break

    # Buscar sección "Características y beneficios"
    in_benefits = False
    in_restricciones = False
    for line in content_lines:
        ll = line.lower()
        if "características y beneficios" in ll or "beneficios" in ll:
            in_benefits = True
            in_restricciones = False
            continue
        if "restricciones" in ll:
            in_restricciones = True
            in_benefits = False
            continue
        if "productos relacionados" in ll:
            in_benefits = False
            in_restricciones = False
            continue
        if in_benefits and len(line) > 5:
            result["beneficios"].append(line)
        if in_restricciones and len(line) > 5:
            result["restricciones"].append(line)

    # Presentación (buscar patrones como "25kg", "bolsa", etc.)
    for line in content_lines:
        if re.search(r'\d+\s*kg', line.lower()) or "presentación" in line.lower():
            pres = re.search(r'(\d+\s*kg)', line, re.IGNORECASE)
            if pres:
                result["presentacion"] = pres.group(1)
                break

    # Soporte
    soporte_idx = None
    for i, line in enumerate(content_lines):
        if line.lower() == "soporte":
            soporte_idx = i
            break
    if soporte_idx is not None:
        for line in content_lines[soporte_idx + 1:soporte_idx + 5]:
            if line and not any(k in line.lower() for k in nav_keywords):
                result["soporte"].append(line.rstrip(","))

    return result


def extract_pdf_text(pdf_path: Path) -> str:
    """Extrae el texto completo de un PDF usando PyMuPDF."""
    if not PYMUPDF_OK:
        return ""
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        print(f"  Error al leer PDF {pdf_path.name}: {e}")
        return ""


def extract_rendimiento(texto: str) -> str:
    """Extrae el rendimiento/consumo del texto del PDF."""
    patrones = [
        r'(\d+[\.,]?\d*\s*m[²2]\s*(?:aprox\.?\s*)?(?:por|x)\s*bolsa)',
        r'(\d+[\.,]?\d*\s*kg/m[²2])',
        r'rendimiento[:\s]+([^\n]{5,60})',
        r'consumo[:\s]+([^\n]{5,60})',
    ]
    for patron in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_tiempo_secado(texto: str) -> str:
    """Extrae el tiempo de secado del PDF."""
    match = re.search(r'tiempo de secado[:\s]+([^\n]{3,40})', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def extract_presentacion_pdf(texto: str) -> str:
    """Extrae la presentación (peso/formato) del PDF."""
    match = re.search(r'presentaci[oó]n[:\s]+([^\n]{3,40})', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def build_product_entry(json_path: Path, docs_dir: Path) -> dict | None:
    """
    Construye una entrada de producto normalizada combinando JSON + PDF.
    Retorna None si es una página de búsqueda (no una ficha de producto).
    """
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    url = raw.get("url", "")

    # Descartar páginas de búsqueda/filtro
    if is_search_page(url):
        return None

    nombre = raw.get("nombre", "").strip()
    datos = clean_datos_tecnicos(raw.get("datos_tecnicos", ""))
    categoria = get_category(url)

    # Inferir tipo de producto desde la URL
    tipo = url.rstrip("/").split("/")[-2].replace("-", " ").title() if "/" in url else "Weber"

    # Descripción: combinar descripcion del JSON con la limpia de datos_tecnicos
    descripcion = datos["descripcion_corta"]
    if not descripcion:
        descripcion = raw.get("descripcion", "").strip()

    # Buscar PDF de hoja técnica o ficha de producto asociado
    pdf_text = ""
    documentos_raw = raw.get("documentos", [])

    for doc in documentos_raw:
        doc_nombre = doc.get("nombre", "").lower()
        doc_url = doc.get("url", "")
        # Buscar PDF en la carpeta local por nombre de archivo
        pdf_filename = doc_url.split("/")[-1]
        pdf_path = docs_dir / pdf_filename
        if pdf_path.exists():
            extracted = extract_pdf_text(pdf_path)
            if extracted:
                pdf_text += extracted + "\n"
                break  # Con la hoja técnica alcanza

    # Si no encontró por nombre exacto, buscar por nombre de producto
    if not pdf_text:
        nombre_slug = nombre.lower().replace(" ", "_").replace("-", "_")
        for pdf_file in docs_dir.glob("*.pdf"):
            if nombre_slug[:10] in pdf_file.stem.lower():
                extracted = extract_pdf_text(pdf_file)
                if extracted:
                    pdf_text = extracted
                    break

    # Extraer datos técnicos del PDF si lo encontramos
    rendimiento = extract_rendimiento(pdf_text) if pdf_text else ""
    tiempo_secado = extract_tiempo_secado(pdf_text) if pdf_text else ""
    presentacion = extract_presentacion_pdf(pdf_text) if pdf_text else datos["presentacion"]

    # Construir entry en formato compatible con PEISA products_catalog.json
    entry = {
        "model": nombre,
        "description": descripcion,
        "category": categoria,
        "subcategory": tipo,
        "type": "PRODUCTO WEBER",
        "family": "Weber",
        "brand": "Weber",
        "url": url,
        "technical_features": [],
        "advantages": datos["beneficios"],
        "specifications": {},
        "restricciones": datos["restricciones"],
        "rendimiento": rendimiento,
        "tiempo_secado": tiempo_secado,
        "presentacion": presentacion,
        "soporte": datos["soporte"],
        "pdf_text": pdf_text[:3000] if pdf_text else "",  # Primeros 3000 chars para RAG
        "tiene_pdf": bool(pdf_text),
        "documentos": documentos_raw,
    }

    # Extraer features técnicas del PDF
    if pdf_text:
        # Buscar secciones de características técnicas
        lineas_pdf = [l.strip() for l in pdf_text.splitlines() if l.strip()]
        in_features = False
        for linea in lineas_pdf:
            ll = linea.lower()
            if any(k in ll for k in ["descripción y caracterist", "características de empleo", "composición"]):
                in_features = True
            if in_features and ":" in linea and len(linea) > 10:
                entry["technical_features"].append(linea)
            if len(entry["technical_features"]) >= 8:
                break

        # Extraer specifications (pares clave: valor del PDF)
        for linea in lineas_pdf:
            if ":" in linea and len(linea) < 120:
                partes = linea.split(":", 1)
                if len(partes) == 2 and len(partes[0]) < 50:
                    clave = partes[0].strip()
                    valor = partes[1].strip()
                    if clave and valor and len(valor) > 1:
                        entry["specifications"][clave] = valor
                        if len(entry["specifications"]) >= 10:
                            break

    return entry


def build_catalog(weber_data_dir: str, output_path: str = "data/weber_catalog.json"):
    """
    Función principal: recorre la carpeta weber_data y construye el catálogo.
    """
    base = Path(weber_data_dir)
    productos_dir = base / "productos"
    docs_dir = base / "documents"
    if not docs_dir.exists() and (base / "documentos").exists():
        docs_dir = base / "documentos"

    if not productos_dir.exists() or not docs_dir.exists():
        print(f"Aviso: La carpeta de origen de datos o sus subcarpetas no existen en {base}. Creando estructura de directorios...")
        productos_dir.mkdir(parents=True, exist_ok=True)
        docs_dir.mkdir(parents=True, exist_ok=True)

    print(f"Leyendo JSONs desde: {productos_dir}")
    print(f"Buscando PDFs en:    {docs_dir}")
    print()

    catalog = []
    skipped = 0

    json_files = sorted(productos_dir.glob("*.json"))
    print(f"Total JSONs encontrados: {len(json_files)}")

    for json_file in json_files:
        entry = build_product_entry(json_file, docs_dir)
        if entry is None:
            skipped += 1
            continue
        catalog.append(entry)
        pdf_ok = "[PDF]" if entry["tiene_pdf"] else "[sin PDF]"
        print(f"  {pdf_ok}  {entry['model'][:50]}")

    print()
    print(f"Productos procesados: {len(catalog)}")
    print(f"Paginas de busqueda ignoradas: {skipped}")

    # Guardar
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"\nCatalogo guardado en: {output}")
    print(f"   {len(catalog)} productos listos para ingestion en el RAG.")
    return catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline de ingestión Weber")
    parser.add_argument(
        "--weber_data",
        default="weber_data",
        help="Ruta a la carpeta weber_data (default: ./weber_data)"
    )
    parser.add_argument(
        "--output",
        default="data/weber_catalog.json",
        help="Ruta de salida del catálogo (default: data/weber_catalog.json)"
    )
    args = parser.parse_args()
    build_catalog(args.weber_data, args.output)
