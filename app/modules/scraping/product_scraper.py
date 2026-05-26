# app/product_scraper.py - Scraper y catálogo de productos PEISA
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
import time

def scrape_peisa_products() -> List[Dict]:
    """
    Realiza scraping REAL del sitio web de PEISA para obtener productos actualizados.
    URL: https://peisa.com.ar/productos
    
    Extrae:
    - Categoría (h1): ej. "Calderas centrales"
    - Subcategoría (texto rojo): ej. "De potencia"
    - Productos con nombre, tipo y descripción
    - Ficha técnica completa de cada producto
    
    Returns:
        Lista de productos extraídos del sitio web
    """
    print("🌐 Iniciando scraping de PEISA...")
    products = []
    
    try:
        # URL base de productos PEISA
        base_url = "https://peisa.com.ar"
        products_url = f"{base_url}/productos"
        
        # Headers para simular navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"  📡 Conectando a {products_url}...")
        response = requests.get(products_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print("  ✅ Página cargada correctamente")
        
        # Buscar todos los productos en la página
        # Estructura: <a href="/productos/[nombre]"><article>...</article></a>
        all_product_links = soup.find_all('a', href=re.compile(r'/productos/[^/]+$'))
        all_product_cards = [link for link in all_product_links if link.find('article')]
        
        print(f"  🔍 Total de productos encontrados en la página: {len(all_product_cards)}")
        
        # Extraer categorías para organizar
        categories = soup.find_all('h1')
        current_category = "Sin categoría"
        current_subcategory = ""
        
        for category_elem in categories:
            category_name = category_elem.get_text(strip=True)
            
            # Buscar subcategoría (texto rojo después del h1)
            subcategory_elem = category_elem.find_next_sibling()
            subcategory = ""
            if subcategory_elem and 'text-peisared' in str(subcategory_elem.get('class', [])):
                subcategory = subcategory_elem.get_text(strip=True)
            
            print(f"\n  📂 Categoría: {category_name}")
            if subcategory:
                print(f"     └─ Subcategoría: {subcategory}")
        
        # Procesar todos los productos encontrados
        print(f"\n  📦 Procesando {len(all_product_cards)} productos...")
        
        for idx, card in enumerate(all_product_cards, 1):
            try:
                # Intentar determinar categoría del producto buscando el h1 más cercano antes del producto
                product_category = "Sin categoría"
                product_subcategory = ""
                
                # Buscar hacia atrás en el HTML para encontrar el h1 más cercano
                prev_elem = card
                while prev_elem:
                    prev_elem = prev_elem.find_previous(['h1', 'p'])
                    if prev_elem and prev_elem.name == 'h1':
                        product_category = prev_elem.get_text(strip=True)
                        # Buscar subcategoría después del h1
                        next_elem = prev_elem.find_next_sibling()
                        if next_elem and 'text-peisared' in str(next_elem.get('class', [])):
                            product_subcategory = next_elem.get_text(strip=True)
                        break
                
                # Extraer información básica del producto
                product = extract_product_info(card, base_url, product_category, product_subcategory)
                
                if product and product.get('model'):
                    # Extraer características técnicas y ventajas de la página de detalle
                    product_url = product.get('url')
                    if product_url:
                        technical_data = scrape_product_detail(product_url, headers)
                        product.update(technical_data)
                    
                    products.append(product)
                    print(f"  ✓ [{idx}/{len(all_product_cards)}] {product['model']} - {product_category}")
                    
                # Pequeña pausa para no sobrecargar el servidor
                time.sleep(0.3)
                    
            except Exception as e:
                print(f"  ⚠️  Error procesando producto {idx}: {e}")
                continue
        
        print(f"\n✅ Scraping completado: {len(products)} productos extraídos")
        
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("⚠️  No se pudo conectar al sitio web de PEISA")
        return []
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    # Si no se encontraron productos, retornar lista vacía
    if not products:
        print("⚠️  No se encontraron productos en el sitio web")
        return []
    
    return products

def extract_product_info(card, base_url: str, category: str = "", subcategory: str = "") -> Dict:
    """
    Extrae información de un elemento HTML de producto de PEISA.
    
    Estructura esperada:
    <a href="/productos/[nombre]">
        <article>
            <div class="text-peisared-600">TIPO DE PRODUCTO</div>
            <h4>NOMBRE PRODUCTO</h4>
            <p>Descripción</p>
        </article>
    </a>
    
    Args:
        card: Elemento <a> que contiene el producto
        base_url: URL base del sitio
        category: Categoría principal (h1) ej. "Calderas centrales"
        subcategory: Subcategoría (texto rojo) ej. "De potencia"
        
    Returns:
        Diccionario con información del producto
    """
    product = {}
    
    try:
        article = card.find('article')
        if not article:
            return product
        
        # Extraer tipo de producto (texto en rojo dentro del article)
        # Ej: "CALDERA DE POTENCIA"
        type_elem = article.find('div', class_=re.compile(r'peisared|uppercase'))
        product_type = type_elem.get_text(strip=True) if type_elem else ""
        
        # Extraer nombre/modelo (h4)
        title_elem = article.find(['h4', 'h3', 'h2'])
        if title_elem:
            product['model'] = title_elem.get_text(strip=True)
        else:
            return product  # Sin nombre, no es válido
        
        # Extraer descripción (párrafo)
        desc_elem = article.find('p')
        if desc_elem:
            product['description'] = desc_elem.get_text(strip=True)
        else:
            product['description'] = f"{product_type} - {product['model']}"
        
        # Asignar categoría y tipo
        product['category'] = category if category else "Sin categoría"
        product['subcategory'] = subcategory if subcategory else ""
        product['type'] = product_type if product_type else determine_type(product.get('model', ''))
        
        # Determinar familia basada en categoría principal
        if category:
            product['family'] = map_category_to_family(category)
        else:
            product['family'] = determine_family(product.get('model', ''))
        
        # URL del producto
        product_url = card.get('href', '')
        if product_url and not product_url.startswith('http'):
            product['url'] = base_url + product_url
        else:
            product['url'] = product_url
        
    except Exception as e:
        print(f"    Error extrayendo info: {e}")
    
    return product


def scrape_product_detail(product_url: str, headers: dict) -> Dict:
    """
    Extrae la ficha técnica completa de un producto individual.
    
    Extrae:
    - Descripción completa del producto
    - Características técnicas (lista de bullets)
    - Ventajas (lista de bullets)
    - Potencia, dimensiones, etc.
    
    Args:
        product_url: URL completa del producto
        headers: Headers HTTP para la petición
        
    Returns:
        Diccionario con datos técnicos adicionales
    """
    technical_data = {
        'technical_features': [],
        'advantages': [],
        'specifications': {}
    }
    
    try:
        response = requests.get(product_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer descripción completa del producto
        # La descripción está en el primer párrafo después del subtítulo (h2)
        # Buscar el h2 con el subtítulo y luego el párrafo siguiente
        subtitle = soup.find('h2')
        if subtitle:
            # Buscar el siguiente párrafo después del h2
            next_p = subtitle.find_next('p')
            if next_p:
                desc_text = next_p.get_text(strip=True)
                # Separar la descripción de las ventajas si están juntas
                # Buscar donde empieza "Ventajas" o "VentajasX" (sin espacio)
                if 'Ventajas' in desc_text:
                    # Dividir en la palabra "Ventajas"
                    desc_text = desc_text.split('Ventajas')[0].strip()
                
                # Verificar que sea una descripción válida (más de 50 caracteres)
                if len(desc_text) > 50:
                    technical_data['description'] = desc_text
        
        # Si no se encontró con el método anterior, buscar en todo el contenido
        if 'description' not in technical_data:
            # Buscar todos los párrafos en el área principal
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                
                # Separar la descripción de las ventajas si están juntas
                if 'Ventajas' in text:
                    text = text.split('Ventajas')[0].strip()
                
                # La descripción es un párrafo largo que no contiene palabras clave de secciones
                if (len(text) > 80 and 
                    'Características' not in text and
                    'garantía' not in text and
                    'PUNTOS DE VENTA' not in text):
                    technical_data['description'] = text
                    break
        
        # Extraer ventajas (sección "Ventajas")
        # Primero intentar extraer de una lista <ul> después de un <h3>Ventajas</h3>
        ventajas_section = soup.find('h3', string=re.compile(r'Ventajas', re.I))
        if ventajas_section:
            ventajas_list = ventajas_section.find_next('ul')
            if ventajas_list:
                technical_data['advantages'] = [
                    li.get_text(strip=True) for li in ventajas_list.find_all('li')
                ]
        
        # Si no se encontraron ventajas en una lista <ul>, buscar en el texto del párrafo
        if not technical_data['advantages']:
            # Buscar el párrafo que contiene "Ventajas"
            subtitle = soup.find('h2')
            if subtitle:
                next_p = subtitle.find_next('p')
                if next_p:
                    full_text = next_p.get_text(strip=True)
                    # Si el párrafo contiene "Ventajas", extraer la parte de ventajas
                    if 'Ventajas' in full_text:
                        ventajas_text = full_text.split('Ventajas', 1)[1] if 'Ventajas' in full_text else ''
                        if ventajas_text:
                            # Dividir por puntos seguidos de mayúscula o por saltos de línea
                            ventajas_items = []
                            # Dividir por punto seguido de mayúscula
                            parts = re.split(r'\.(?=[A-Z])', ventajas_text)
                            for part in parts:
                                part = part.strip()
                                if len(part) > 10:  # Filtrar fragmentos muy cortos
                                    # Agregar el punto final si no lo tiene
                                    if not part.endswith('.'):
                                        part += '.'
                                    ventajas_items.append(part)
                            
                            if ventajas_items:
                                technical_data['advantages'] = ventajas_items
        
        # Extraer características técnicas (sección "Características Técnicas" o "Características técnicas")
        # Buscar cualquier encabezado que contenga "características" y "técnicas"
        caracteristicas_section = soup.find(['h2', 'h3', 'h4'], string=re.compile(r'Características\s+técnicas', re.I))
        if caracteristicas_section:
            caracteristicas_list = caracteristicas_section.find_next('ul')
            if caracteristicas_list:
                technical_data['technical_features'] = [
                    li.get_text(strip=True) for li in caracteristicas_list.find_all('li')
                ]
        
        # Extraer especificaciones de cualquier lista de bullets visible
        all_lists = soup.find_all('ul')
        for ul in all_lists:
            items = [li.get_text(strip=True) for li in ul.find_all('li')]
            # Buscar especificaciones técnicas en formato "Clave: Valor"
            for item in items:
                if ':' in item:
                    key, value = item.split(':', 1)
                    technical_data['specifications'][key.strip()] = value.strip()
        
        # Extraer potencia si está en especificaciones
        for key, value in technical_data['specifications'].items():
            if 'potencia' in key.lower():
                power_match = re.search(r'(\d+)\s*(w|kw|kcal)', value, re.I)
                if power_match:
                    power_value = int(power_match.group(1))
                    unit = power_match.group(2).lower()
                    if unit == 'kw':
                        power_value *= 1000
                    elif unit == 'kcal':
                        power_value = int(power_value * 1.163)
                    technical_data['power_w'] = power_value
        
        # Pequeña pausa
        time.sleep(0.2)
        
    except Exception as e:
        print(f"         ⚠️  Error obteniendo ficha técnica: {e}")
    
    return technical_data


def map_category_to_family(category: str) -> str:
    """Mapea la categoría de PEISA a nuestra familia de productos"""
    category_lower = category.lower()
    
    if 'caldera' in category_lower:
        return "Calderas"
    elif 'radiador' in category_lower or 'toallero' in category_lower:
        return "Radiadores"
    elif 'termotanque' in category_lower or 'tanque' in category_lower:
        return "Termotanques"
    elif 'calefon' in category_lower:
        return "Calefones"
    elif 'termostato' in category_lower:
        return "Termostatos"
    elif 'piscina' in category_lower or 'climatizador' in category_lower:
        return "Climatización Piscinas"
    elif 'detector' in category_lower:
        return "Seguridad"
    else:
        return "Otros"


def determine_family(model_name: str) -> str:
    """Determina la familia del producto según su nombre"""
    model_lower = model_name.lower()
    
    if any(word in model_lower for word in ['radiador', 'broen', 'panel', 'toallero']):
        return "Radiadores"
    elif any(word in model_lower for word in ['caldera', 'boiler', 'prima', 'diva', 'summa']):
        return "Calderas"
    elif any(word in model_lower for word in ['piso', 'radiante', 'suelo']):
        return "Piso Radiante"
    elif any(word in model_lower for word in ['termotanque', 'tanque', 'agua caliente']):
        return "Termotanques"
    elif any(word in model_lower for word in ['bomba', 'circulador']):
        return "Accesorios"
    else:
        return "Otros"


def determine_type(model_name: str) -> str:
    """Determina el tipo específico del producto"""
    model_lower = model_name.lower()
    
    if 'panel' in model_lower:
        return "Radiador de panel"
    elif 'toallero' in model_lower:
        return "Radiador toallero"
    elif 'caldera' in model_lower:
        return "Caldera mural"
    elif 'piso' in model_lower or 'radiante' in model_lower:
        return "Sistema completo"
    elif 'termotanque' in model_lower:
        return "Termotanque eléctrico"
    elif 'bomba' in model_lower:
        return "Bomba circuladora"
    else:
        return "Producto de calefacción"

def get_products_catalog(use_scraping: bool = True) -> List[Dict]:
    """
    Retorna el catálogo de productos PEISA mediante scraping.
    
    Args:
        use_scraping: Si True, intenta hacer scraping real del sitio web.
        
    Returns:
        Lista de productos extraídos del sitio web
    """
    if use_scraping:
        return scrape_peisa_products()
    else:
        # Si no se quiere scraping, cargar desde archivo existente
        try:
            with open("data/products_catalog.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Archivo products_catalog.json no encontrado. Ejecutando scraping...")
            return scrape_peisa_products()


def save_catalog(filename: str = "data/products_catalog.json", use_scraping: bool = True):
    """
    Guarda el catálogo en un archivo JSON, actualizando productos existentes.
    
    Args:
        filename: Ruta donde guardar el archivo
        use_scraping: Si True, intenta scraping real de PEISA
        
    Returns:
        Lista de productos guardados
    """
    import os
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"🚀 SCRAPER DE PRODUCTOS PEISA")
    print(f"{'='*60}\n")
    
    # Cargar catálogo existente si existe
    existing_products = {}
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_list = json.load(f)
                # Indexar por URL para búsqueda rápida
                existing_products = {p.get('url'): p for p in existing_list if p.get('url')}
                print(f"📂 Catálogo existente cargado: {len(existing_products)} productos")
        except Exception as e:
            print(f"⚠️  Error cargando catálogo existente: {e}")
    
    # Obtener productos del scraping
    new_products = get_products_catalog(use_scraping=use_scraping)
    
    # Actualizar o agregar productos
    updated_count = 0
    added_count = 0
    
    for product in new_products:
        product_url = product.get('url')
        if product_url in existing_products:
            # Actualizar producto existente
            existing_products[product_url].update(product)
            updated_count += 1
        else:
            # Agregar nuevo producto
            existing_products[product_url] = product
            added_count += 1
    
    # Convertir diccionario de vuelta a lista
    final_products = list(existing_products.values())
    
    # Guardar en JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(final_products, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Catálogo guardado exitosamente")
    print(f"📁 Archivo: {filename}")
    print(f"📦 Total productos: {len(final_products)}")
    print(f"   ├─ ✨ Nuevos: {added_count}")
    print(f"   └─ 🔄 Actualizados: {updated_count}")
    print(f"{'='*60}\n")
    
    return final_products


if __name__ == "__main__":
    import sys
    
    # Verificar si se pasa argumento --no-scraping
    use_scraping = "--no-scraping" not in sys.argv
    
    if use_scraping:
        print("🌐 Modo: SCRAPING REAL de https://peisa.com.ar/productos")
        print("   - Actualiza productos existentes")
        print("   - Agrega productos nuevos")
    else:
        print("📋 Modo: Cargar desde archivo existente (sin scraping)")
    
    # Ejecutar scraping y guardar
    products = save_catalog(use_scraping=use_scraping)
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DEL CATÁLOGO:")
    print(f"{'='*60}")
    
    # Agrupar por familia
    families = {}
    for p in products:
        family = p.get('family', 'Otros')
        families[family] = families.get(family, 0) + 1
    
    for family, count in sorted(families.items()):
        print(f"  • {family}: {count} productos")
    
    print(f"\n📋 PRODUCTOS EXTRAÍDOS:")
    print(f"{'='*60}")
    for idx, p in enumerate(products, 1):
        category = p.get('category', 'N/A')
        print(f"  {idx:2d}. {p['model']:<40} ({p['family']}) - {category}")
