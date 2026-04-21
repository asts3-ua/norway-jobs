import requests
from bs4 import BeautifulSoup

print("="*60)
print("🔍 DEBUGGING DE ENDPOINTS")
print("="*60)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ===== PRUEBA 1: arbeidsplassen.nav.no =====
print("\n🏢 ARBEIDSPLASSEN.NAV.NO")
print("-" * 60)

query = "developer"
url = "https://arbeidsplassen.nav.no/stillinger"
params = {"q": query, "sort": "0"}

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"Tamaño respuesta: {len(response.text)} bytes")
    
    # Intenta parsear como JSON
    try:
        data = response.json()
        print(f"✅ Es JSON válido")
        print(f"   Keys: {list(data.keys())[:5]}")
        if "content" in data:
            print(f"   Ofertas en 'content': {len(data['content'])}")
    except:
        print(f"❌ No es JSON")
        
    # Parsea como HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Busca diferentes selectores
    print("\n📍 Buscando elementos HTML:")
    
    selectors = [
        ('article[data-testid="search-result-item"]', "Articles con data-testid"),
        ('article', "Articles generales"),
        ('div[class*="job"]', "Divs con 'job'"),
        ('a[href*="/stillinger/stilling/"]', "Links a ofertas"),
        ('[data-testid*="result"]', "Elementos con 'result'"),
    ]
    
    for selector, desc in selectors:
        elements = soup.select(selector) if '[' in selector else soup.find_all(selector.split('[')[0])
        print(f"   {desc}: {len(elements)}")
        if elements and len(elements) > 0:
            print(f"      Primer elemento: {str(elements[0])[:100]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")

# ===== PRUEBA 2: finn.no =====
print("\n\n🏢 FINN.NO")
print("-" * 60)

url = "https://www.finn.no/job/listing"
params = {"q": "developer"}

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    print(f"URL: {response.url}")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
    print(f"Tamaño respuesta: {len(response.text)} bytes")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("\n📍 Buscando elementos HTML:")
    
    selectors = [
        ('article', "Articles"),
        ('a[href*="/job/listing/"]', "Links a ofertas"),
        ('div[class*="job"]', "Divs con 'job'"),
        ('[data-testid*="result"]', "Elementos con 'result'"),
        ('li', "Items de lista"),
    ]
    
    for selector, desc in selectors:
        if '[' in selector:
            elements = soup.select(selector)
        else:
            elements = soup.find_all(selector.split('[')[0])
        print(f"   {desc}: {len(elements)}")
        if elements and len(elements) > 0:
            elem_text = str(elements[0])
            if len(elem_text) > 150:
                elem_text = elem_text[:150] + "..."
            print(f"      Primer elemento: {elem_text}")
    
    # Busca cualquier enlace que mencione "job" o "listing"
    all_links = soup.find_all('a', href=True)
    job_links = [a for a in all_links if 'job' in a.get('href', '') or 'listing' in a.get('href', '')]
    print(f"\n   Enlaces relacionados con jobs: {len(job_links)}")
    if job_links:
        print(f"      Primer link: {job_links[0].get('href')}")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
