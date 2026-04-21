
import requests
import json
import smtplib
import os
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup
import logging

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
LOG_FILE = Path("job_scraper.log")
EMAIL_PREVIEW_FILE = Path("job_email_preview.html")
BUILD_TAG = "GH-ACTIONS-FINN-V3"


def log(message):
    print(message)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except Exception:
        pass
# --- CONFIGURACIÓN ---
RECIPIENT_EMAIL = "alejandrosancheztilve02@gmail.com"
SENDER_EMAIL = os.environ.get("GMAIL_USER")
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

KEYWORDS_IT = [
    "python", "developer", "utvikler", "automation", "automatisering",
    "software", "backend", "frontend", "fullstack", "data engineer",
    "AI", "artificial intelligence", "machine learning", "integrasjon",
    "integration", "IT support", "tekniker", "technician", "devops",
    "cloud", "azure", "aws", "system administrator", "nettverks",
    "network", "drift", "infrastruktur", "infrastructure", "java",
    "javascript", "php", "sql", "database", "web developer"
]

KEYWORDS_FINANCE = [
    "fintech", "finance", "financial", "økonomi", "analytiker",
    "analyst", "investment", "finans", "regnskap", "accounting",
    "business analyst", "data analyst", "BI", "power BI"
]

KEYWORDS_RESEARCH = [
    "research", "forsker", "forskning", "researcher", "PhD", "postdoc",
    "scientist", "R&D", "innovasjon", "innovation", "university",
    "universitet", "institute", "institutt", "laboratory", "laboratorium",
    "computer science", "informatikk", "teknologi"
]

ALL_KEYWORDS = KEYWORDS_IT + KEYWORDS_FINANCE + KEYWORDS_RESEARCH


def fetch_jobs_nav():
    """Buscar trabajos via la API JSON de arbeidsplassen.nav.no."""
    all_jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    api_url = "https://arbeidsplassen.nav.no/stillinger/api/search"

    # Todas las ofertas de IT por categoría de ocupación (paginado)
    log("  arbeidsplassen.nav.no: obteniendo categoría IT...")
    offset = 0
    page_size = 100
    while True:
        try:
            params = {"size": page_size, "occupationFirstLevels[]": "IT", "from": offset}
            r = requests.get(api_url, params=params, headers=headers, timeout=15)
            if r.status_code != 200:
                log(f"  arbeidsplassen.nav.no: status {r.status_code} en offset {offset}")
                break
            data = r.json()
            hits = data["hits"]["hits"]
            total = data["hits"]["total"]["value"]
            for h in hits:
                src = h["_source"]
                props = src.get("properties", {})
                tags = " ".join(t.get("label", "") for t in props.get("searchtags", []))
                all_jobs.append({
                    "_source": "arbeidsplassen.nav.no",
                    "title": src.get("title", ""),
                    "description": tags,
                    "employer": src.get("employer", {}),
                    "locationList": src.get("locationList", []),
                    "uuid": src.get("uuid", ""),
                    "applicationDue": props.get("applicationdue", ""),
                })
            if len(hits) < page_size or len(all_jobs) >= total:
                break
            offset += page_size
        except Exception as e:
            log(f"  arbeidsplassen.nav.no error (IT, offset={offset}): {str(e)[:120]}")
            break

    log(f"  arbeidsplassen.nav.no IT: {len(all_jobs)} ofertas")

    # Búsquedas adicionales por keywords de finanzas e investigación
    extra_queries = ["fintech", "finance", "data analyst", "machine learning", "forsker", "PhD"]
    for kw in extra_queries:
        try:
            r = requests.get(api_url, params={"q": kw, "size": 100}, headers=headers, timeout=15)
            if r.status_code != 200:
                continue
            hits = r.json()["hits"]["hits"]
            for h in hits:
                src = h["_source"]
                props = src.get("properties", {})
                tags = " ".join(t.get("label", "") for t in props.get("searchtags", []))
                all_jobs.append({
                    "_source": "arbeidsplassen.nav.no",
                    "title": src.get("title", ""),
                    "description": tags,
                    "employer": src.get("employer", {}),
                    "locationList": src.get("locationList", []),
                    "uuid": src.get("uuid", ""),
                    "applicationDue": props.get("applicationdue", ""),
                })
            log(f"  arbeidsplassen.nav.no '{kw}': {len(hits)} ofertas")
        except Exception as e:
            log(f"  arbeidsplassen.nav.no error ('{kw}'): {str(e)[:120]}")

    return all_jobs


def fetch_jobs_finn_with_playwright(keyword):
    """Fallback con navegador real cuando requests no devuelve resultados útiles."""
    extracted = []
    if not HAS_PLAYWRIGHT:
        return extracted

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                locale="nb-NO"
            )
            page.goto(f"https://www.finn.no/job/search?q={keyword}", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(2000)

            cards = page.locator('article[id^="card-"]')
            count = cards.count()
            log(f"    Playwright cards encontrados para '{keyword}': {count}")

            for index in range(count):
                try:
                    card = cards.nth(index)
                    link = card.locator('a[href*="/job/ad/"]').first
                    job_url = link.get_attribute('href') if link.count() > 0 else ""
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.finn.no{job_url}"

                    text = card.inner_text(timeout=5000)
                    lines = [line.strip() for line in text.split('\n') if line.strip()]

                    title = lines[0] if len(lines) > 0 else ""
                    employer = lines[1] if len(lines) > 1 else ""
                    location = lines[2] if len(lines) > 2 else ""

                    if title and len(title) > 3:
                        extracted.append({
                            "title": title,
                            "employer": employer,
                            "location": location,
                            "url": job_url or "https://www.finn.no/job/search",
                            "description": text,
                            "_source": "finn.no"
                        })
                except Exception as inner_error:
                    log(f"    Playwright card error: {str(inner_error)[:100]}")

            browser.close()
    except Exception as e:
        log(f"  Playwright fallback error para '{keyword}': {str(e)[:150]}")

    return extracted

def fetch_jobs_finn():
    """Buscar trabajos en finn.no usando web scraping"""
    all_jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8,en-US;q=0.7,en;q=0.6"
    }
    
    # finn.no tiene todas las ofertas en una sola búsqueda
    search_keywords = ["developer", "python", "IT", "fintech"]
    
    for keyword in search_keywords:
        try:
            url = "https://www.finn.no/job/search"
            params = {"q": keyword}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            log(f"  finn.no '{keyword}': status {response.status_code}, url={response.url}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Encuentra todos los artículos (cada uno es una oferta)
                articles = soup.find_all('article')
                log(f"    articles encontrados: {len(articles)}")
                extracted = []
                
                for article in articles:
                    try:
                        # Obtiene el ID de la oferta
                        card_id = article.get('id', '').replace('card-', '')
                        if not card_id:
                            continue
                        
                        # Busca el enlace a la oferta
                        link = article.find('a', href=True)
                        if not link:
                            continue
                        
                        job_url = link.get('href', '')
                        if not job_url.startswith('http'):
                            job_url = f"https://www.finn.no{job_url}"
                        
                        # Extrae texto completo del artículo
                        text = article.get_text(strip=True)
                        lines = [line.strip() for line in text.split('\n') if line.strip()]
                        
                        # Estructura típica: título, empresa, ubicación, tiempo, ...
                        title = ""
                        employer = ""
                        location = ""
                        
                        # El primer elemento generalmente es el título
                        if len(lines) > 0:
                            title = lines[0]
                        
                        # El segundo generalmente es la empresa
                        if len(lines) > 1:
                            employer = lines[1]
                        
                        # El tercero generalmente es la ubicación
                        if len(lines) > 2:
                            location = lines[2]
                        
                        if title and len(title) > 3:  # Evita títulos muy cortos
                            extracted.append({
                                "title": title,
                                "employer": employer,
                                "location": location,
                                "url": job_url,
                                "description": text,
                                "_source": "finn.no"
                            })
                    except Exception as e:
                        log(f"    error parseando artículo: {str(e)[:120]}")
                
                all_jobs.extend(extracted)
                log(f"  finn.no '{keyword}': {len(extracted)} ofertas")

                if not extracted and HAS_PLAYWRIGHT:
                    log(f"  finn.no '{keyword}': sin resultados con requests, probando Playwright")
                    playwright_jobs = fetch_jobs_finn_with_playwright(keyword)
                    if playwright_jobs:
                        all_jobs.extend(playwright_jobs)
                        log(f"  finn.no '{keyword}': {len(playwright_jobs)} ofertas (Playwright)")
            else:
                log(f"  finn.no '{keyword}': status {response.status_code}")
        except Exception as e:
            log(f"  Error finn.no '{keyword}': {str(e)[:120]}")
    
    return all_jobs

def deduplicate(jobs):
    seen = set()
    unique = []
    for job in jobs:
        source = job.get("_source", "unknown")
        uid = job.get("uuid") or job.get("id") or job.get("adid", "")
        if uid:
            key = f"{source}:{uid}"
        else:
            key = f"{source}:{job.get('title', '')}:{job.get('employer', '')}"
        if key and key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

def categorize_job(title, description):
    text = (title + " " + description).lower()
    if any(kw.lower() in text for kw in ["research", "forsker", "forskning", "PhD", "university", "universitet", "institute"]):
        return "🔬 Investigación"
    if any(kw.lower() in text for kw in KEYWORDS_FINANCE):
        return "💹 Finanzas/Fintech"
    return "💻 IT/Tech"

def normalize_job(job):
    source = job.get("_source", "unknown")
    title = job.get("title", "") or job.get("heading", "") or "Sin título"
    description = job.get("description", "") or job.get("body", "") or ""

    if source == "arbeidsplassen.nav.no":
        location_list = job.get("locationList", [])
        location = (location_list[0].get("city") or "").title() if location_list else ""
        employer_raw = job.get("employer", {})
        employer = (employer_raw.get("name") or "").title() if isinstance(employer_raw, dict) else str(employer_raw)
        url = f"https://arbeidsplassen.nav.no/stillinger/stilling/{job.get('uuid', '')}"
    else:
        location = job.get("location", "") or job.get("region", "") or ""
        employer = job.get("employer", "") or job.get("company", "") or ""
        url = job.get("url", "") or "https://www.finn.no"

    return {
        "title": title[:100],
        "employer": employer or "Empresa no especificada",
        "location": location or "Noruega",
        "deadline": job.get("applicationDue", "") or job.get("deadline", "") or "",
        "url": url,
        "source": source,
        "description": description,
    }

def filter_and_categorize(jobs):
    matched = {"💻 IT/Tech": [], "💹 Finanzas/Fintech": [], "🔬 Investigación": []}

    for job in jobs:
        source = job.get("_source", "unknown")
        normalized = normalize_job(job)
        title = normalized["title"]
        description = normalized["description"]

        # Jobs from the nav.no API are already category-filtered — include all of them.
        # Jobs scraped from finn.no need keyword matching since they come from broad searches.
        if source == "arbeidsplassen.nav.no":
            passes = True
        else:
            text = (title + " " + description).lower()
            passes = any(kw.lower() in text for kw in ALL_KEYWORDS)

        if passes:
            category = categorize_job(title, description)
            matched[category].append(normalized)
            log(f"  [+] {title[:70]} | {source}")
        else:
            log(f"  [-] {title[:70]}")

    return matched

def build_email_html(categorized, stats=None):
    today = datetime.now().strftime("%d/%m/%Y")
    total = sum(len(v) for v in categorized.values())
    stats = stats or {}
    sections = ""
    for category, jobs in categorized.items():
        if not jobs:
            continue
        rows = ""
        for j in jobs:
            deadline = f"<br><small style='color:#888;'>⏰ Plazo: {j['deadline'][:10]}</small>" if j['deadline'] else ""
            source_badge = f"<br><small style='color:#666; font-weight:bold;'>🔗 {j['source']}</small>"
            rows += f"""
            <tr>
                <td style="padding:12px; border-bottom:1px solid #f0f0f0;">
                    <strong><a href="{j['url']}" style="color:#0057b8; text-decoration:none;">{j['title']}</a></strong><br>
                    <span style="color:#555;">🏢 {j['employer']}</span><br>
                    <span style="color:#555;">📍 {j['location']}</span>{deadline}{source_badge}
                </td>
            </tr>
            """
        sections += f"""
        <div style="margin-bottom:24px;">
            <h3 style="background:#f0f4ff; padding:10px 16px; border-radius:6px; margin:0 0 8px;">
                {category} — {len(jobs)} ofertas
            </h3>
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; font-size:14px;">
                {rows}
            </table>
        </div>
        """
    if total == 0:
        sections = "<p style='color:#888;'>No se encontraron ofertas nuevas relevantes hoy. Inténtalo mañana 💪</p>"
    html = f"""
    <html><body style="background:#f4f4f4; padding:20px; font-family:Arial,sans-serif;">
        <div style="max-width:680px; margin:auto; background:white; border-radius:10px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.1);">
            <div style="background:#0057b8; color:white; padding:22px 28px;">
                <h2 style="margin:0; font-size:20px;">🇳🇴 Ofertas en Noruega — {today}</h2>
                <p style="margin:6px 0 0; opacity:0.85; font-size:14px;">{total} ofertas relevantes · IT / Fintech / Investigación</p>
            </div>
            <div style="padding:24px 28px;">
                <div style="font-size:12px; color:#666; background:#f7f7f7; border:1px solid #eee; border-radius:8px; padding:8px 10px; margin-bottom:14px;">
                    Build: {BUILD_TAG} · Raw: {stats.get('raw', 'n/a')} · Unique: {stats.get('unique', 'n/a')} · Matched: {total}
                </div>
                {sections}
                <p style="margin-top:24px; color:#aaa; font-size:12px; border-top:1px solid #eee; padding-top:16px;">
                    Fuentes: <a href="https://arbeidsplassen.nav.no" style="color:#0057b8;">arbeidsplassen.nav.no</a> · <a href="https://finn.no" style="color:#0057b8;">finn.no</a> — Filtrado por keywords IT/Tech/Fintech para el perfil de Alejandro Sánchez Tilve
                </p>
            </div>
        </div>
    </body></html>
    """
    return html, total

def send_email(html_content, job_count):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        log("⚠️  No se puede enviar el email: faltan GMAIL_USER o GMAIL_APP_PASSWORD")
        log("   El scraper sí encontró ofertas; solo se omitió el envío de correo.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{BUILD_TAG}] 🇳🇴 {job_count} ofertas en Noruega — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_content, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print(f"✅ Email enviado con {job_count} ofertas a {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        log(f"❌ Error enviando email: {str(e)[:200]}")
        log("   El scraper sí encontró ofertas; revisa las credenciales SMTP.")
        return False


def main():
    if LOG_FILE.exists():
        try:
            LOG_FILE.unlink()
        except Exception:
            pass
    print("\n" + "="*70)
    print("🇳🇴 SCRAPER DE OFERTAS DE TRABAJO - NORUEGA")
    print("="*70)
    
    print("\n🔍 Buscando ofertas...")
    log("=== INICIO EJECUCIÓN ===")
    
    # Intentar arbeidsplassen
    nav_jobs = fetch_jobs_nav()
    
    # Buscar en finn.no
    print("\n🔍 Buscando en finn.no...")
    finn_jobs = fetch_jobs_finn()
    log(f"📦 {len(finn_jobs)} ofertas obtenidas de finn.no")
    
    raw_jobs = nav_jobs + finn_jobs
    log(f"\n📊 {len(raw_jobs)} ofertas totales obtenidas")
    
    # Debug: mostrar primeras 3 ofertas
    if len(raw_jobs) > 0:
        log("\n📋 Primeras 3 ofertas sin procesar:")
        for i, job in enumerate(raw_jobs[:3]):
            title = job.get("title", "")[:60]
            source = job.get("_source", "unknown")
            desc_len = len(job.get("description", ""))
            log(f"  {i+1}. [{source}] {title} (desc: {desc_len} chars)")
    
    unique_jobs = deduplicate(raw_jobs)
    log(f"\n🔄 {len(unique_jobs)} ofertas únicas tras deduplicar")
    
    log("\n🔍 Filtrando por keywords...")
    categorized = filter_and_categorize(unique_jobs)
    total = sum(len(v) for v in categorized.values())
    log(f"\n✅ {total} ofertas relevantes filtradas")
    for cat, jobs in categorized.items():
        log(f"   {cat}: {len(jobs)}")
    
    print("\n" + "="*70)
    log("=== FIN EJECUCIÓN ===")
    stats = {"raw": len(raw_jobs), "unique": len(unique_jobs)}
    html, count = build_email_html(categorized, stats=stats)
    try:
        EMAIL_PREVIEW_FILE.write_text(html, encoding="utf-8")
        log(f"📝 Preview email guardada en {EMAIL_PREVIEW_FILE}")
    except Exception as e:
        log(f"⚠️  No se pudo guardar preview email: {str(e)[:120]}")
    send_email(html, count)
if __name__ == "__main__":
    main()