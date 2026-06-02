"""
Gscraper.py - Scraper interactivo para RAG (Buscador Weber)
===========================================================
Navega a través de la página del catálogo de productos de Weber Argentina
(search-content/content_type/product) y extrae de forma robusta y paginada
los 108 productos reales disponibles sin depender del Sitemap.xml.

Uso:
    python Gscraper.py --max-productos 5   # prueba rápida
    python Gscraper.py                     # scraping completo
    python Gscraper.py --sin-pdfs          # sin descargar PDFs
"""

import asyncio
import json
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_URL   = "https://www.ar.weber"
OUTPUT_DIR = Path("weber_data")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# URLs de páginas que NO son productos individuales → las filtramos
URLS_BASURA = [
    "/blog/", "/notas-weber/", "/obras-",
    "/innovacion-y-tecnologias/", "/servicios", "/contacto",
    "/nuestras-unidades-de-negocio", "/distribuidores",
    "/puntos-de-venta", "/calculador", "/search-", "/files/",
    "/casos-de-obra", "/sostenibilidad", "/saint-gobain",
    "/materiales-para-profesionales", "/store-locator",
    "/preguntas-y-respuestas", "/bim", "/guia-weber",
    "/escalera-de-pegamento", "/texturas-y-colores",
    "/asistencia-tecnica", "/especificacion-de-obra",
]

DELAY = 1.5       # segundos entre páginas
REINTENTOS = 3


# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────
def crear_directorios():
    for sub in ["productos", "documentos", "chunks", "raw"]:
        (OUTPUT_DIR / sub).mkdir(parents=True, exist_ok=True)

def limpiar(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()

def guardar_json(datos, ruta: Path):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def slugify(texto: str) -> str:
    texto = texto.lower()
    texto = re.sub(r"[^\w\s-]", "", texto)
    texto = re.sub(r"[\s_-]+", "_", texto)
    return texto[:60]


# ─────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────
class WeberScraper:
    def __init__(self, max_productos=None):
        self.max_productos = max_productos
        self.documentos_encontrados = []   # PDFs hallados en páginas de producto

    async def iniciar(self):
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            "./user_data",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0]

    async def cerrar(self):
        if hasattr(self, "context"):
            await self.context.close()
        await self.playwright.stop()

    async def ir_a(self, url: str, retries=3) -> bool:
        """Navega a una URL con reintentos para evitar errores de cierre y maneja Cloudflare."""
        import asyncio
        for i in range(retries):
            try:
                # Si la página se cerró, intentamos recuperarla
                if self.page.is_closed():
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        "./user_data",
                        headless=False,
                        args=["--disable-blink-features=AutomationControlled"],
                    )
                    self.page = self.context.pages[0]

                # Navegamos con un tiempo de espera prudente
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(2)  # Pausa amigable para el procesador

                # ── Detección y evasión de Cloudflare (Turnstile) ──
                title = await self.page.title()
                if "momento" in title.lower() or "checking" in title.lower() or "cloudflare" in title.lower():
                    log("⚠️ Desafío de Cloudflare detectado. Por favor, resolvé el captcha en la ventana del navegador...")
                    start_time = time.time()
                    resolved = False
                    while time.time() - start_time < 60:
                        await asyncio.sleep(1.5)
                        current_title = await self.page.title()
                        if "momento" not in current_title.lower() and "checking" not in current_title.lower() and "cloudflare" not in current_title.lower():
                            resolved = True
                            break
                    if resolved:
                        log("✅ Desafío de Cloudflare resuelto. Continuando...")
                        await asyncio.sleep(2)  # Esperar a que renderice la página
                    else:
                        log("❌ Excedido el tiempo de espera (60s) para resolver el desafío. Intentando continuar...")

                return True
            except Exception as e:
                log(f"  ⚠️ Reintento {i+1}/{retries} para {url}...")
                await asyncio.sleep(3)
        return False

    # ──────────────────────────────────────────
    # 1. LISTAR TODOS LOS PRODUCTOS DESDE EL BUSCADOR DRUPAL
    # ──────────────────────────────────────────
    async def obtener_lista_productos(self) -> list[dict]:
        """Extrae la lista de productos recorriendo las páginas del buscador de Weber."""
        todos = []
        page_num = 0
        
        log("📦 Iniciando extracción desde el catálogo de búsqueda de Weber...")
        
        # Lista de palabras clave para identificar URLs de productos reales
        categorias_filtradas = [
            "mezclas-adhesivas", "pastinas", "revoques", "impermeabiliz", 
            "pinturas", "pisos", "aislacion", "aditivos", "hormigon",
            "revestimiento", "revestimientos", "fijacion", "fijaciones",
            "anclaje", "anclajes", "sellado", "selladores", "espuma",
            "revocar", "revoque", "colocacion-ceramicas", "revocar-paredes", 
            "soluciones-para-pisos", "impermeabilizantes", "aislacion-termica", 
            "preparacion-de-superficies", "soluciones-para-fijaciones-anclajes-y-sellados", 
            "revestimientos-decorativos", "revestimiento-de-paredes", "revestimientos-plasticos", 
            "revestimientos-cementicios"
        ]
        
        while True:
            url = f"https://www.ar.weber/search-content/content_type/product?page={page_num}"
            log(f"🔍 Buscando productos en la página {page_num + 1}... ({url})")
            
            ok = await self.ir_a(url)
            if not ok:
                log(f"❌ No se pudo cargar la página {page_num + 1}. Finalizando recolección.")
                break
                
            html = await self.page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            productos_pagina = []
            
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith(("#", "javascript:")):
                    continue
                    
                full_url = href if href.startswith("http") else f"https://www.ar.weber{href}"
                path = urlparse(full_url).path
                partes = [p for p in path.split("/") if p]
                
                # Drupal de Weber usa URLs de 3 o más segmentos para los productos
                if len(partes) >= 3:
                    # Evitar la página de búsqueda misma u otras basuras
                    if "search-content" in path or any(b in path for b in URLS_BASURA):
                        continue
                    
                    coincide = any(cat in href.lower() for cat in categorias_filtradas)
                    if coincide:
                        nombre = partes[-1].replace("-", " ").title()
                        if not any(p["url"] == full_url for p in todos) and not any(p["url"] == full_url for p in productos_pagina):
                            productos_pagina.append({"nombre": nombre, "url": full_url})
                            
            if not productos_pagina:
                log("ℹ️ No se encontraron nuevos productos en esta página. Fin de la paginación.")
                break
                
            todos.extend(productos_pagina)
            log(f"  ✅ Se agregaron {len(productos_pagina)} productos de la página {page_num + 1}. Total acumulado: {len(todos)}")
            page_num += 1
            await asyncio.sleep(1.5) # pausa amigable para el servidor
            
        log(f"📦 Recolección finalizada. Total de productos reales detectados: {len(todos)}")
        if self.max_productos and len(todos) > self.max_productos:
            todos = todos[:self.max_productos]
            
        return todos

    # ──────────────────────────────────────────
    # 2. SCRAPE DE UN PRODUCTO INDIVIDUAL
    # ──────────────────────────────────────────
    async def scrape_producto(self, producto: dict) -> dict:
        """Enfoque de extracción total: Captura todo el texto relevante de la página."""
        ok = await self.ir_a(producto["url"])
        if not ok:
            return {**producto, "error": "No se pudo cargar"}

        try:
            html = await self.page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Eliminamos lo que NO es contenido (Scripts, Estilos, Nav, Footer)
            for elemento in soup(["script", "style", "nav", "footer", "header", "aside"]):
                elemento.decompose()
 
            datos = {
                "nombre": producto["nombre"],
                "url": producto["url"],
                "descripcion": "",
                "datos_tecnicos": "", 
                "documentos": [],
                "scrapeado_en": datetime.now().isoformat(),
            }

            # 1. Extraemos el título real
            h1 = soup.find("h1")
            if h1: datos["nombre"] = h1.get_text().strip()

            # 2. ENFOQUE TOTAL: Capturamos el contenedor principal de Drupal
            cuerpo = soup.find("main") or soup.find("article") or soup.find("div", {"id": "main-content"})
            
            if cuerpo:
                texto_sucio = cuerpo.get_text(separator="\n", strip=True)
                lineas = [l.strip() for l in texto_sucio.split('\n') if len(l.strip()) > 3]
                datos["descripcion"] = " ".join(lineas[:3]) # Primeras líneas como intro
                datos["datos_tecnicos"] = "\n".join(lineas) # Todo el resto

            # 3. Captura de PDFs
            for a in soup.find_all("a", href=True):
                if ".pdf" in a["href"].lower():
                    link = urljoin(BASE_URL, a["href"])
                    if not any(d["url"] == link for d in datos["documentos"]):
                        datos["documentos"].append({"nombre": a.get_text().strip() or "PDF Técnico", "url": link})

            return datos
        except Exception as e:
            log(f"  ❌ Fallo crítico en {producto['url']}: {e}")
            return producto

    # ──────────────────────────────────────────
    # 3. DESCARGAR PDF VIA NAVEGADOR INYECCIÓN JS
    # ──────────────────────────────────────────
    async def descargar_pdf(self, doc: dict) -> str | None:
        url = doc["url"]
        nombre_archivo = Path(urlparse(url).path).name
        if not nombre_archivo.lower().endswith(".pdf"):
            nombre_archivo += ".pdf"
        
        ruta_local = OUTPUT_DIR / "documentos" / nombre_archivo

        if ruta_local.exists() and ruta_local.stat().st_size > 1000:
            return str(ruta_local)

        try:
            log(f"  📥 Descargando vía inyección: {nombre_archivo}")

            b64_data = await self.page.evaluate(f"""
                async () => {{
                    const response = await fetch('{url}');
                    const buffer = await response.arrayBuffer();
                    const base64 = btoa(
                        new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
                    );
                    return base64;
                }}
            """)

            import base64
            pdf_bytes = base64.b64decode(b64_data)

            if len(pdf_bytes) > 1000:
                ruta_local.write_bytes(pdf_bytes)
                tamanio = len(pdf_bytes) // 1024
                log(f"  ✅ {nombre_archivo} ({tamanio} KB) [OK]")
                return str(ruta_local)
            
            return None

        except Exception as e:
            log(f"  ❌ Falló inyección en {nombre_archivo}: {e}")
            return None

    # ──────────────────────────────────────────
    # 4. GENERAR CHUNKS PARA RAG
    # ──────────────────────────────────────────
    def a_chunks(self, prod: dict) -> list[dict]:
        chunks = []
        nombre = prod.get("nombre", "")
        url    = prod.get("url", "")
        cat    = prod.get("categoria", "")
        subcat = prod.get("subcategoria", "")
        cat_full = f"{cat} > {subcat}" if subcat else cat

        def chunk(tipo: str, texto: str):
            if not texto.strip():
                return
            header = f"Producto: {nombre}\nCategoría: {cat_full}\nURL: {url}\n\n"
            chunks.append({
                "id":       f"{slugify(nombre)}_{tipo}",
                "producto": nombre,
                "categoria": cat_full,
                "url":      url,
                "tipo":     tipo,
                "texto":    header + texto,
                "metadata": {
                    "fuente":   "ar.weber",
                    "tipo":     tipo,
                    "producto": nombre,
                    "categoria": cat,
                    "url":      url,
                },
            })

        # Chunk 1 — Descripción
        if prod.get("descripcion"):
            chunk("descripcion", f"Descripción: {prod['descripcion']}")

        # Chunk 2 — Resumen completo
        partes = [f"# {nombre}"]
        if cat_full:                partes.append(f"Categoría: {cat_full}")
        if prod.get("descripcion"): partes.append(prod["descripcion"])
        chunk("resumen", "\n".join(partes))

        return chunks


# ─────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────
async def main(solo_productos=False, max_productos=None, descargar_pdfs=True):
    crear_directorios()
    scraper = WeberScraper(max_productos=max_productos)

    log("🚀 Weber RAG Gscraper (Buscador)")
    log(f"   Destino: {OUTPUT_DIR.absolute()}")
    log("=" * 50)

    await scraper.iniciar()
    try:
        # ── Paso 1: Obtener lista recorriendo el buscador ──
        lista = await scraper.obtener_lista_productos()
        guardar_json(lista, OUTPUT_DIR / "lista_productos.json")

        log(f"\n🔍 Procesando {len(lista)} productos...")
        todos_chunks = []
        documentos_totales = []

        # ── Paso 2: Procesar cada producto ──
        for i, prod in enumerate(tqdm(lista, desc="Progreso")):
            detalle = await scraper.scrape_producto(prod)
            
            nombre_archivo = slugify(detalle['nombre'])
            guardar_json(detalle, OUTPUT_DIR / "productos" / f"{nombre_archivo}.json")
            
            chunks_web = scraper.a_chunks(detalle)
            todos_chunks.extend(chunks_web)

            if descargar_pdfs and detalle.get("documentos"):
                for doc in detalle["documentos"]:
                    if not any(d['url'] == doc['url'] for d in documentos_totales):
                        ruta_pdf = await scraper.descargar_pdf(doc)
                        if ruta_pdf:
                            documentos_totales.append(doc)

            if (i + 1) % 5 == 0:
                log(f"   {i+1}/{len(lista)} procesados | {len(todos_chunks)} chunks acumulados")

        # ── Paso 3: Guardar Chunks y Resúmenes ──
        log(f"\n💾 Guardando {len(todos_chunks)} chunks...")
        guardar_json(todos_chunks, OUTPUT_DIR / "chunks" / "todos_los_chunks.json")
        guardar_json(documentos_totales, OUTPUT_DIR / "documentos.json")

        # ── Paso 4: Índice Final ──
        guardar_json({
            "fecha_scraping": datetime.now().isoformat(),
            "total_productos": len(lista),
            "total_documentos": len(documentos_totales),
            "total_chunks": len(todos_chunks),
        }, OUTPUT_DIR / "indice.json")

        log("\n" + "=" * 50)
        log("✅ COMPLETADO")
        log(f"   Productos:   {len(lista)}")
        log(f"   PDFs bajados: {len(documentos_totales)}")
        log(f"   Chunks RAG:  {len(todos_chunks)}")

    finally:
        await scraper.cerrar()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weber RAG Gscraper (Buscador)")
    parser.add_argument("--solo-productos",  action="store_true", help="Sin descargar PDFs")
    parser.add_argument("--max-productos",   type=int, default=None, help="Limitar para prueba")
    parser.add_argument("--sin-pdfs",        action="store_true", help="No descargar PDFs")
    args = parser.parse_args()

    asyncio.run(main(
        solo_productos=args.solo_productos,
        max_productos=args.max_productos,
        descargar_pdfs=not args.sin_pdfs,
    ))
