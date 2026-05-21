"""Script para inspeccionar la estructura HTML de PEISA"""
import requests
from bs4 import BeautifulSoup

url = "https://peisa.com.ar/productos"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"🔍 Inspeccionando {url}...\n")

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Guardar HTML para inspección
    with open('data/peisa_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("✅ HTML guardado en data/peisa_page.html")
    
    # Buscar diferentes tipos de elementos
    print("\n📋 Análisis de estructura:\n")
    
    # Buscar divs con clases comunes
    divs_with_class = soup.find_all('div', class_=True)
    classes = set()
    for div in divs_with_class[:100]:
        if div.get('class'):
            classes.update(div['class'])
    
    print(f"Clases encontradas (primeras 20):")
    for cls in sorted(list(classes))[:20]:
        print(f"  - {cls}")
    
    # Buscar enlaces
    links = soup.find_all('a', href=True)
    print(f"\n🔗 Total enlaces: {len(links)}")
    
    product_links = [a for a in links if 'producto' in a.get('href', '').lower()]
    print(f"   Enlaces con 'producto': {len(product_links)}")
    
    # Mostrar algunos enlaces
    print("\n📌 Primeros 10 enlaces:")
    for a in links[:10]:
        href = a.get('href', '')
        text = a.get_text(strip=True)[:50]
        print(f"  - {text} → {href}")
    
except Exception as e:
    print(f"❌ Error: {e}")
