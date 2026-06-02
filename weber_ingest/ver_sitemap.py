import requests
import xml.etree.ElementTree as ET

r = requests.get("https://www.ar.weber/sitemap.xml?page=1", timeout=30)
root = ET.fromstring(r.content)
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
urls = [t.text.strip() for t in root.findall(f".//{NS}loc")]
print(f"Total URLs: {len(urls)}")
print("\n--- PRIMERAS 30 ---")
for u in urls[:30]:
    print(u)
print("\n--- URLs CON 3 SEGMENTOS ---")
from urllib.parse import urlparse
import json
from pathlib import Path

valid_urls = []
for u in urls:
    segs = [s for s in urlparse(u).path.strip("/").split("/") if s]
    if len(segs) == 3:
        print(u)
        valid_urls.append(u)

# Guardar resultado en data/valid_url.json
output_dir = Path("data")
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "valid_url.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(valid_urls, f, ensure_ascii=False, indent=2)

print(f"\n💾 Guardado exitoso de {len(valid_urls)} URLs válidas en: {output_file}")