import requests
from bs4 import BeautifulSoup
import json

print("🔍 Extrayendo detalles de ofertas en finn.no\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

url = "https://www.finn.no/job/search?q=developer"

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}\n")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extrae artículos
    articles = soup.find_all('article')
    print(f"Found {len(articles)} articles\n")
    
    print("=" * 80)
    print("PRIMEROS 5 ARTÍCULOS:")
    print("=" * 80)
    
    for i, article in enumerate(articles[:5]):
        print(f"\n📌 Artículo {i+1}:")
        print("-" * 80)
        
        # Busca todos los links dentro del artículo
        links = article.find_all('a', href=True)
        print(f"Links: {len(links)}")
        
        # Busca títulos
        h2 = article.find('h2')
        h3 = article.find('h3')
        h4 = article.find('h4')
        
        if h2:
            print(f"h2: {h2.get_text(strip=True)[:80]}")
        if h3:
            print(f"h3: {h3.get_text(strip=True)[:80]}")
        if h4:
            print(f"h4: {h4.get_text(strip=True)[:80]}")
        
        # Busca todo el texto
        text = article.get_text(strip=True)
        print(f"\nTexto completo ({len(text)} chars):")
        print(text[:300] + "..." if len(text) > 300 else text)
        
        # Busca atributos útiles
        attrs_to_check = ['id', 'data-id', 'data-listing-id', 'data-job-id', 'href']
        for attr in attrs_to_check:
            value = article.get(attr)
            if value:
                print(f"{attr}: {value}")
        
        # Busca links a ofertas
        job_links = [a.get('href', '') for a in links if '/job/' in a.get('href', '') and 'search' not in a.get('href', '')]
        if job_links:
            print(f"Ofertas links: {job_links[:2]}")
    
    # Extrae scripts JSON
    print("\n\n" + "=" * 80)
    print("SCRIPTS JSON:")
    print("=" * 80)
    
    scripts = soup.find_all('script', type='application/json')
    print(f"Found {len(scripts)} JSON scripts\n")
    
    for i, script in enumerate(scripts[:2]):
        try:
            data = json.loads(script.string)
            print(f"\nScript {i+1} keys: {list(data.keys())}")
            
            # Intenta encontrar data de ofertas
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"  {key}: lista con {len(value)} items")
                    if len(value) > 0 and isinstance(value[0], dict):
                        print(f"    Primer item keys: {list(value[0].keys())[:5]}")
        except Exception as e:
            print(f"Error parsing script {i+1}: {e}")
    
except Exception as e:
    print(f"Error: {e}")
