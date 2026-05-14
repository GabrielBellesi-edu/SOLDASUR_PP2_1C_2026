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
for u in urls:
    segs = [s for s in urlparse(u).path.strip("/").split("/") if s]
    if len(segs) == 3:
        print(u)