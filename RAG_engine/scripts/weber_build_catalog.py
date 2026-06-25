"""
weber_build_catalog.py  –  Pipeline de ingestión Weber (Paso 1)
=============================================================
Lee los JSONs de productos Weber + los PDFs de la carpeta data_raw/weber
y genera un weber_catalog.json normalizado.
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

# Mapeo de categorías Weber (URL keyword → categoría legible)
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
    """Detecta si la URL es una página de búsqueda/filtro."""
    return "/search-content/" in url

def clean_datos_tecnicos(raw: str, model_name: str = "") -> dict:
    result = {
        "descripcion_corta": "",
        "descripcion_larga": "",
        "beneficios": [],
        "restricciones": [],
        "presentacion": "",
        "soporte": [],
        "productos_relacionados": [],
    }
    if not raw:
        return result

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    nav_keywords = {"inicio", "show gallery", "encontrá un distribuidor",
                    "calculadora de consumo", "documentación del producto",
                    "tutoriales y videos", "comenzar tutorial", "ver video",
                    "descargar", "enviar", "apply", "acerca de este producto"}

    content_lines = [l for l in lines if l.lower() not in nav_keywords
                     and not l.lower().startswith("(pdf")]

    # 1. Buscar descripción corta (evitando breadcrumbs y títulos de categorías/modelos)
    model_lower = model_name.lower()
    model_short = model_lower.replace("weber ", "")
    for line in content_lines:
        ll = line.lower()
        if len(line) <= 30:
            continue
        if any(k in ll for k in ["buscar", "filtrar", "resetear"]):
            continue
        if ll == model_lower or ll == model_short:
            continue
        
        # Ignorar breadcrumbs y nombres de categorías del mapa
        is_breadcrumb = False
        for cat_name in CATEGORY_MAP.values():
            if ll == cat_name.lower() or cat_name.lower() in ll:
                is_breadcrumb = True
                break
        for cat_key in CATEGORY_MAP.keys():
            clean_key = cat_key.replace("-", " ")
            if ll == clean_key or clean_key in ll:
                is_breadcrumb = True
                break
        if "soluciones para" in ll or "colocación cerámicas" in ll or "revestimiento de paredes" in ll:
            is_breadcrumb = True
            
        if not is_breadcrumb:
            result["descripcion_corta"] = line
            break

    # 2. Buscar descripción larga ("Acerca de este producto")
    in_about = False
    about_lines = []
    for line in lines:
        ll = line.lower()
        if "acerca de este producto" in ll:
            in_about = True
            continue
        if in_about:
            headers = ["características y beneficios", "beneficios", "restricciones", 
                       "productos relacionados", "documentación del producto", "presentación", "soporte"]
            if any(h in ll for h in headers) or (len(line) < 30 and not line.endswith(".")):
                in_about = False
            else:
                about_lines.append(line)

    if about_lines:
        result["descripcion_larga"] = " ".join(about_lines).strip()

    # 3. Beneficios y restricciones
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

    # 4. Presentación
    for line in content_lines:
        if re.search(r'\d+\s*kg', line.lower()) or "presentación" in line.lower():
            pres = re.search(r'(\d+\s*kg)', line, re.IGNORECASE)
            if pres:
                result["presentacion"] = pres.group(1)
                break

    # 5. Soporte
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
    match = re.search(r'tiempo de secado[:\s]+([^\n]{3,40})', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def extract_presentacion_pdf(texto: str) -> str:
    match = re.search(r'presentaci[oó]n[:\s]+([^\n]{3,40})', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""

def build_product_entry(json_path: Path, docs_dir: Path) -> dict | None:
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    url = raw.get("url", "")
    if is_search_page(url):
        return None

    nombre = raw.get("nombre", "").strip()
    datos = clean_datos_tecnicos(raw.get("datos_tecnicos", ""), nombre)
    categoria = get_category(url)
    tipo = url.rstrip("/").split("/")[-2].replace("-", " ").title() if "/" in url else "Weber"

    descripcion = datos["descripcion_corta"]
    if not descripcion:
        descripcion = raw.get("descripcion", "").strip()

    pdf_text = ""
    documentos_raw = raw.get("documentos", [])
    for doc in documentos_raw:
        doc_url = doc.get("url", "")
        pdf_filename = doc_url.split("/")[-1]
        pdf_path = docs_dir / pdf_filename
        if pdf_path.exists():
            extracted = extract_pdf_text(pdf_path)
            if extracted:
                pdf_text += extracted + "\n"
                break

    if not pdf_text:
        nombre_slug = nombre.lower().replace(" ", "_").replace("-", "_")
        for pdf_file in docs_dir.glob("*.pdf"):
            if nombre_slug[:10] in pdf_file.stem.lower():
                extracted = extract_pdf_text(pdf_file)
                if extracted:
                    pdf_text = extracted
                    break

    rendimiento = extract_rendimiento(pdf_text) if pdf_text else ""
    
    # --- Enriquecimiento estructurado v4.3.0 ---
    atributos = raw.get("atributos_tecnicos", {})
    filtros = raw.get("filtros", {})
    
    # 1. Soporte
    if "Soporte" in atributos:
        soporte_list = [s.strip() for s in atributos["Soporte"].split(",") if s.strip()]
        if soporte_list:
            datos["soporte"] = soporte_list
            
    # 2. Presentación
    presentacion_val = atributos.get("Presentación") or atributos.get("Presentacion") or atributos.get("Packaging")
    if presentacion_val:
        presentacion = presentacion_val.strip()
    else:
        presentacion = extract_presentacion_pdf(pdf_text) if pdf_text else datos["presentacion"]
        
    # 3. Colores
    colores_val = atributos.get("Colores") or atributos.get("Color")
    colores_list = []
    if colores_val:
        colores_list = [c.strip() for c in colores_val.split(",") if c.strip()]
    colores_filtro = filtros.get("colores", [])
    if colores_filtro:
        colores_list = list(set(colores_list + [c["nombre"] for c in colores_filtro]))
        
    # 4. Beneficios
    beneficios_filtro = filtros.get("beneficios", [])
    if beneficios_filtro:
        for b in beneficios_filtro:
            if b["nombre"] not in datos["beneficios"]:
                datos["beneficios"].append(b["nombre"])
                
    # 5. Tiempo de secado
    secado_val = atributos.get("Tiempo de secado") or atributos.get("Secado")
    if secado_val:
        tiempo_secado = secado_val.strip()
    else:
        tiempo_secado = extract_tiempo_secado(pdf_text) if pdf_text else ""
    # -------------------------------------------

    entry = {
        "model": nombre,
        "description": descripcion,
        "descripcion_larga": datos["descripcion_larga"],
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
        "colores": colores_list,
        "filtros": filtros,
        "atributos_tecnicos": atributos,
        "pdf_text": pdf_text[:3000] if pdf_text else "",
        "tiene_pdf": bool(pdf_text),
        "documentos": documentos_raw,
        "imagen_url": raw.get("imagen_url", ""),
        "imagen_local": raw.get("imagen_local", ""),
    }

    if pdf_text:
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

def build_catalog(weber_data_dir: str, output_path: str):
    base = Path(weber_data_dir)
    productos_dir = base / "productos"
    docs_dir = base / "documentos"
    if not docs_dir.exists() and (base / "documents").exists():
        docs_dir = base / "documents"

    if not productos_dir.exists():
        print(f"[ERROR] No existe la subcarpeta 'productos' en {base}")
        return []

    print(f"[Weber Ingest] Leyendo JSONs desde: {productos_dir}")
    if docs_dir.exists():
        print(f"[Weber Ingest] Buscando PDFs en:    {docs_dir}")
    else:
        print("[Weber Ingest] AVISO: Carpeta de documentos PDF no encontrada.")

    catalog = []
    skipped = 0
    json_files = sorted(productos_dir.glob("*.json"))
    
    for json_file in json_files:
        entry = build_product_entry(json_file, docs_dir)
        if entry is None:
            skipped += 1
            continue
        catalog.append(entry)

    # Guardar catálogo consolidado
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print(f"[OK] [Weber Ingest] Catálogo consolidado guardado en: {output}")
    print(f"  • {len(catalog)} productos consolidados (ignorados: {skipped})")
    return catalog

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--weber_data", default="scraping/data_raw/weber")
    parser.add_argument("--output", default="web_app/data/weber_catalog.json")
    args = parser.parse_args()
    build_catalog(args.weber_data, args.output)
