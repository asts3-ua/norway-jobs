import requests
from bs4 import BeautifulSoup

print("="*80)
print("🔍 DEBUG DETALLADO - Analizando estructura de datos")
print("="*80)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Test arbeidsplassen
print("\n📌 TRABAJOS en ARBEIDSPLASSEN.NAV.NO")
print("-" * 80)

url = "https://arbeidsplassen.nav.no/stillinger"
params = {"q": "developer", "sort": "0"}

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    articles = soup.find_all('article')
    print(f"Total artículos encontrados: {len(articles)}")
    
    if len(articles) > 0:
        print(f"\n🔎 Analizando primer artículo en detalle:")
        article = articles[0]
        
        # Todo el contenido
        full_text = article.get_text(strip=True)
        print(f"  Texto completo ({len(full_text)} chars): {full_text[:200]}...")
        
        # Busca links
        links = article.find_all('a', href=True)
        print(f"  Links encontrados: {len(links)}")
        for i, link in enumerate(links[:2]):
            print(f"    {i+1}. {link.get('href', '')[:80]}")
        
        # Busca elementos de texto
        h2 = article.find('h2')
        h3 = article.find('h3')
        spans = article.find_all('span')
        divs = article.find_all('div')
        
        print(f"  H2 tags: {len(article.find_all('h2'))}")
        print(f"  H3 tags: {len(article.find_all('h3'))}")
        print(f"  Spans: {len(spans)}")
        print(f"  Divs: {len(divs)}")
        
        if h2:
            print(f"  H2 content: {h2.get_text(strip=True)[:80]}")
        if h3:
            print(f"  H3 content: {h3.get_text(strip=True)[:80]}")
        
        # Estructura HTML simplificada
        print(f"\n  Estructura HTML:")
        print(f"  {str(article)[:300]}...")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Test finn.no
print("\n\n📌 TRABAJOS en FINN.NO")
print("-" * 80)

url = "https://www.finn.no/job/search"
params = {"q": "developer"}

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    articles = soup.find_all('article')
    print(f"Total artículos encontrados: {len(articles)}")
    
    if len(articles) > 0:
        print(f"\n🔎 Analizando primer artículo en detalle:")
        article = articles[0]
        
        # Todo el contenido
        full_text = article.get_text(strip=True)
        print(f"  Texto completo ({len(full_text)} chars): {full_text[:200]}...")
        
        # ID
        card_id = article.get('id', '')
        print(f"  ID: {card_id}")
        
        # Busca links
        links = article.find_all('a', href=True)
        print(f"  Links encontrados: {len(links)}")
        for i, link in enumerate(links[:2]):
            print(f"    {i+1}. {link.get('href', '')}")
        
        # Estructura de líneas
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        print(f"\n  Estructura por líneas ({len(lines)} líneas):")
        for i, line in enumerate(lines[:6]):
            print(f"    {i+1}. {line[:70]}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)
