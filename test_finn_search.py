import requests
from bs4 import BeautifulSoup

print("🔍 Probando búsquedas en URLs válidas\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# URLs que devuelven 200
urls = [
    "https://www.finn.no/job",
    "https://www.finn.no/jobb",
]

for base_url in urls:
    print(f"\n{'='*60}")
    print(f"Probando: {base_url}")
    print('='*60)
    
    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca links a ofertas
        all_links = soup.find_all('a', href=True)
        job_links = [a for a in all_links if '/job' in a.get('href', '') or '/jobb' in a.get('href', '')]
        print(f"Links encontrados: {len(job_links)}")
        
        if job_links:
            print(f"\nPrimeros 3 links:")
            for i, link in enumerate(job_links[:3]):
                href = link.get('href', '')
                text = link.get_text(strip=True)[:50]
                print(f"  {i+1}. {href}")
                print(f"     Texto: {text}")
        
        # Busca artículos/divs
        articles = soup.find_all('article')
        divs_with_job = soup.select('div[class*="job"], div[class*="offer"]')
        
        print(f"\nArticles: {len(articles)}")
        print(f"Divs con 'job': {len(divs_with_job)}")
        
    except Exception as e:
        print(f"Error: {e}")
