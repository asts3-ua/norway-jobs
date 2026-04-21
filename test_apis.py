import requests
import json

print("=== Probando arbeidsplassen.nav.no ===")
headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Intento 1: Endpoint original
try:
    url = "https://arbeidsplassen.nav.no/stillinger/api/v1/ads/search"
    response = requests.get(url, params={"q": "developer", "size": 5}, headers=headers, timeout=10)
    print(f"Endpoint v1/ads/search: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# Intento 2: Verificar base URL
try:
    url = "https://arbeidsplassen.nav.no/api/v1/ads/search"
    response = requests.get(url, params={"q": "developer", "size": 5}, headers=headers, timeout=10)
    print(f"Endpoint /api/v1/ads/search: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Probando finn.no ===")
# Intento 1: Buscar HTML (web scraping)
try:
    url = "https://www.finn.no/job/listing"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Página HTML finn.no: {response.status_code}")
    if "developer" in response.text.lower()[:1000]:
        print("Página cargada exitosamente")
except Exception as e:
    print(f"Error: {e}")

# Intento 2: API de finn
try:
    url = "https://www.finn.no/api/v1/search"
    response = requests.get(url, params={"q": "developer"}, headers=headers, timeout=10)
    print(f"API finn.no v1/search: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

# Intento 3: XML feed (common en job sites)
try:
    url = "https://www.finn.no/feed.rss"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"RSS feed finn.no: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
