import requests
import json
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from bs4 import BeautifulSoup

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
    """Buscar trabajos en arbeidsplassen.nav.no"""
    all_jobs = []
    search_queries = [
        "developer", "python", "IT", "automation",
        "research informatikk", "fintech", "software engineer"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for query in search_queries:
        try:
            url = "https://arbeidsplassen.nav.no/stillinger"
            params = {"q": query, "sort": "0"}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Los artículos están en <article> sin data-testid específico
                articles = soup.find_all('article')
                extracted = []
                
                for article in articles:
                    try:
                        # Busca el enlace dentro del artículo
                        link = article.find('a', href=True)
                        if link and '/stillinger/stilling/' in link.get('href', ''):
                            title_elem = link.find('h2') or link.find('span', class_=lambda x: x and 'title' in x.lower())
                            if not title_elem:
                                title_elem = link
                            
                            title = title_elem.get_text(strip=True)
                            url_href = link.get('href', '')
                            if not url_href.startswith('http'):
                                url_href = f"https://arbeidsplassen.nav.no{url_href}"
                            
                            # Busca empleador y ubicación
                            employer = ""
                            location = ""
                            text_parts = article.get_text(strip=True).split('\n')
                            
                            extracted.append({
                                "title": title,
                                "url": url_href,
                                "employer": employer,
                                "location": location,
                                "description": article.get_text(strip=True),
                                "_source": "arbeidsplassen.nav.no"
                            })
                    except Exception as e:
                        pass
                
                all_jobs.extend(extracted)
                print(f"  arbeidsplassen '{query}': {len(extracted)} ofertas")
            else:
                print(f"  arbeidsplassen '{query}': status {response.status_code}")
        except Exception as e:
            print(f"  Error arbeidsplassen '{query}': {str(e)[:50]}")
    
    return all_jobs

def fetch_jobs_finn():
    """Buscar trabajos en finn.no usando web scraping"""
    all_jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # finn.no tiene todas las ofertas en una sola búsqueda
    search_keywords = ["developer", "python", "IT", "fintech"]
    
    for keyword in search_keywords:
        try:
            url = "https://www.finn.no/job/search"
            params = {"q": keyword}
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Encuentra todos los artículos (cada uno es una oferta)
                articles = soup.find_all('article')
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
                        pass
                
                all_jobs.extend(extracted)
                print(f"  finn.no '{keyword}': {len(extracted)} ofertas")
            else:
                print(f"  finn.no '{keyword}': status {response.status_code}")
        except Exception as e:
            print(f"  Error finn.no '{keyword}': {str(e)[:50]}")
    
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

def filter_and_categorize(jobs):
    matched = {"💻 IT/Tech": [], "💹 Finanzas/Fintech": [], "🔬 Investigación": []}
    for job in jobs:
        source = job.get("_source", "unknown")
        title = job.get("title", "") or job.get("heading", "")
        description = (job.get("description", "") or job.get("body", "")) or ""
        text = (title + " " + description).lower()
        if any(kw.lower() in text for kw in ALL_KEYWORDS):
            category = categorize_job(title, description)
            
            # Manejo de ubicación
            location = ""
            if source == "arbeidsplassen.nav.no":
                location_list = job.get("locationList", [])
                location = location_list[0].get("city", "") if location_list else job.get("location", "")
            else:  # finn.no
                location = job.get("location", "") or job.get("region", "")
            
            # Manejo del empleador
            employer = ""
            if source == "arbeidsplassen.nav.no":
                if isinstance(job.get("employer"), dict):
                    employer = job["employer"].get("name", "")
                elif isinstance(job.get("employer"), str):
                    employer = job["employer"]
            else:  # finn.no
                employer = job.get("company", "") or job.get("organisation", "")
            
            # Construcción de URL
            url = job.get("url", "")
            if not url or url == "":
                if source == "arbeidsplassen.nav.no":
                    url = f"https://arbeidsplassen.nav.no/stillinger/stilling/{job.get('uuid', '')}"
                else:  # finn.no
                    job_id = job.get("adid") or job.get("id", "")
                    url = f"https://www.finn.no/job/listing/{job_id}" if job_id else "https://www.finn.no"
            
            matched[category].append({
                "title": title[:100] if title else "Sin título",
                "employer": employer or "Empresa no especificada",
                "location": location or "Noruega",
                "deadline": job.get("applicationDue", "") or job.get("deadline", ""),
                "url": url,
                "source": source
            })
    return matched

def build_email_html(categorized):
    today = datetime.now().strftime("%d/%m/%Y")
    total = sum(len(v) for v in categorized.values())
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
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🇳🇴 {job_count} ofertas en Noruega — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_content, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"✅ Email enviado con {job_count} ofertas a {RECIPIENT_EMAIL}")

def main():
    print("🔍 Buscando ofertas en arbeidsplassen.nav.no...")
    nav_jobs = fetch_jobs_nav()
    print(f"📦 {len(nav_jobs)} ofertas obtenidas de arbeidsplassen")
    
    print("🔍 Buscando ofertas en finn.no...")
    finn_jobs = fetch_jobs_finn()
    print(f"📦 {len(finn_jobs)} ofertas obtenidas de finn.no")
    
    raw_jobs = nav_jobs + finn_jobs
    print(f"📦 {len(raw_jobs)} ofertas totales obtenidas")
    
    unique_jobs = deduplicate(raw_jobs)
    print(f"🔄 {len(unique_jobs)} ofertas únicas tras deduplicar")
    
    categorized = filter_and_categorize(unique_jobs)
    total = sum(len(v) for v in categorized.values())
    print(f"✅ {total} ofertas relevantes filtradas")
    for cat, jobs in categorized.items():
        print(f"   {cat}: {len(jobs)}")
    
    html, count = build_email_html(categorized)
    send_email(html, count)

if __name__ == "__main__":
    main()