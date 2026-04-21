import requests
from bs4 import BeautifulSoup
import json

print("🔍 Buscando JSON de ofertas en arbeidsplassen\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

url = "https://arbeidsplassen.nav.no/stillinger"
params = {"q": "developer"}

try:
    response = requests.get(url, params=params, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Busca scripts con JSON
    scripts = soup.find_all('script', type='application/ld+json')
    print(f"Scripts JSON-LD: {len(scripts)}")
    
    scripts_json = soup.find_all('script', type='application/json')
    print(f"Scripts JSON: {len(scripts_json)}\n")
    
    # Busca cualquier script con "jobPosting" o similar
    all_scripts = soup.find_all('script')
    print(f"Total scripts: {len(all_scripts)}\n")
    
    for i, script in enumerate(all_scripts[:10]):
        script_type = script.get('type', 'no-type')
        content_len = len(script.string) if script.string else 0
        print(f"Script {i+1}: type='{script_type}', length={content_len}")
        
        if content_len > 0 and content_len < 500:
            print(f"  Content: {script.string[:200]}...")
        elif content_len > 500 and content_len < 2000:
            # Try to parse as JSON
            try:
                data = json.loads(script.string)
                print(f"  ✓ Valid JSON: {list(data.keys())[:3] if isinstance(data, dict) else type(data)}")
            except:
                print(f"  ✗ Invalid JSON")
                print(f"    {script.string[:100]}...")
    
except Exception as e:
    print(f"Error: {e}")
