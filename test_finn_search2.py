import requests
from bs4 import BeautifulSoup

print("🔍 Probando /job/search\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

urls = [
    "https://www.finn.no/job/search",
    "https://www.finn.no/job/search?q=developer",
    "https://www.finn.no/jobb/stilling?q=developer",
]

for url in urls:
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}, Size: {len(response.text)} bytes")
        
        if response.status_code == 200 and len(response.text) > 5000:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Busca cualquier elemento que pueda contener ofertas
            articles = soup.find_all('article')
            divs = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['item', 'card', 'result', 'listing', 'job']))
            links = soup.find_all('a', href=lambda x: x and ('job' in x.lower() or 'stilling' in x.lower()))
            
            print(f"Articles: {len(articles)}")
            print(f"Divs especializados: {len(divs)}")
            print(f"Links de trabajo: {len(links)}")
            
            if links:
                print(f"\nPrimeros 3 links:")
                for i, link in enumerate(links[:3]):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)[:60]
                    print(f"  {i+1}. {href}")
                    if text:
                        print(f"     {text}")
            
            # Busca cualquier script con datos JSON
            scripts = soup.find_all('script', type='application/json')
            print(f"\nScripts JSON: {len(scripts)}")
            
    except Exception as e:
        print(f"Error: {e}")
