import requests

print("🔍 Probando diferentes URLs de finn.no\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

urls_to_test = [
    "https://www.finn.no/job/listing",
    "https://www.finn.no/job",
    "https://www.finn.no/jobs",
    "https://www.finn.no/search",
    "https://www.finn.no/jobb",
]

for url in urls_to_test:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"{url}")
        print(f"  Status: {response.status_code}, Size: {len(response.text)} bytes")
    except Exception as e:
        print(f"{url}")
        print(f"  Error: {e}")

print("\n🔍 Probando con parámetros de búsqueda:\n")

base_urls = [
    "https://www.finn.no/job/listing?q=developer",
    "https://www.finn.no/jobb?q=developer",
    "https://search.finn.no/?q=developer&category=job",
]

for url in base_urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"{url}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200 and len(response.text) > 1000:
            print(f"  ✅ Parece válido ({len(response.text)} bytes)")
    except Exception as e:
        print(f"{url}")
        print(f"  Error: {e}")
