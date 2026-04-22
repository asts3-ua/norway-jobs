
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
BUILD_TAG = "GH-ACTIONS-TOP15-JUNIOR-V4"

CATEGORY_ES = {
    "💻 IT/Tech": "💻 Tecnología / IT",
    "💹 Finanzas/Fintech": "💹 Finanzas / Fintech",
    "🔬 Investigación": "🔬 Investigación / Universidad",
}

SOURCE_ES = {
    "arbeidsplassen.nav.no": "Arbeidsplassen NAV",
    "finn.no": "Finn.no",
}


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

PROFILE_ROLE_KEYWORDS = [
    "backend", "frontend", "fullstack", "developer", "utvikler", "analyst", "qa", "test", "support", "data scientist", "data engineer", "business intelligence", "power bi"
]
PROFILE_STACK_KEYWORDS = [
    "python", "javascript", "typescript", "sql", "power bi", "aws", "azure", "java", "php"
]
PROFILE_BONUS_KEYWORDS = [
    "genai", "llm", "agent", "ai agent", "agents", "trading", "markets", "stock", "stocks", "fintech", "finance", "financial", "investment", "quant", "portfolio", "equity", "macro", "bank"
]
PROFILE_AI_KEYWORDS = [
    "genai", "llm", "agent", "agentic", "machine learning", "deep learning", "prompt", "rag", "nlp", "artificial intelligence", "kunstig intelligens"
]
PROFILE_DATA_KEYWORDS = [
    "data scientist", "data science", "data engineer", "data analyst", "analytics", "business intelligence", "bi", "power bi", "sql", "databricks", "fabric"
]
PROFILE_FINANCE_KEYWORDS = [
    "fintech", "finance", "financial", "investment", "trading", "markets", "stock", "stocks", "equity", "portfolio", "bank", "quant"
]
CORE_TECH_ROLE_KEYWORDS = [
    "developer", "engineer", "data scientist", "data engineer", "data analyst", "analyst", "qa", "test", "support", "backend", "frontend", "fullstack", "software"
]
PROFILE_RESEARCH_KEYWORDS = [
    "research", "researcher", "forsker", "forskning", "phd", "postdoc", "university", "universitet", "institute", "institutt", "laboratory", "laboratorium", "computer science", "informatikk", "academic", "research assistant", "junior researcher"
]
NON_TARGET_RESEARCH_KEYWORDS = [
    "biology", "biologi", "biomedical", "medisin", "medicine", "medical", "nursing", "nurse", "veterinary", "music", "musikk", "pedagog", "pedagogikk", "paleoklim", "geology", "marine", "law", "juridisk", "history", "linguistics", "psychology", "pharmacy"
]
HARD_EXCLUDE_RESEARCH_DOMAINS = [
    "biostatistics", "computational biology", "seabirds", "forest mapping", "precision forestry", "plant", "soil", "dairy", "hydrodynamic water quality", "coastal ecology", "ocean colour", "marine systems", "agriculture"
]
JUNIOR_POSITIVE_KEYWORDS = ["junior", "graduate", "entry", "entry-level", "trainee", "intern", "nyutdannet", "beginner", "associate"]
SENIOR_NEGATIVE_KEYWORDS = ["senior", "lead", "principal", "staff", "architect", "manager", "head of", "director"]


def has_sector_signal(text):
    sector_keywords = set(
        PROFILE_ROLE_KEYWORDS
        + PROFILE_STACK_KEYWORDS
        + PROFILE_AI_KEYWORDS
        + PROFILE_DATA_KEYWORDS
        + PROFILE_FINANCE_KEYWORDS
        + ["software", "teknologi", "technology", "computer science", "informatikk", "cyber", "analytics", "artificial intelligence", "machine learning"]
    )
    return any(kw in text for kw in sector_keywords)


def has_core_tech_role_signal(text):
    return any(kw in text for kw in CORE_TECH_ROLE_KEYWORDS)


def is_target_sector_job(title, description):
    text = f"{title} {description}".lower()
    research_hit = any(kw in text for kw in PROFILE_RESEARCH_KEYWORDS)
    non_target_research_hit = any(kw in text for kw in NON_TARGET_RESEARCH_KEYWORDS)
    hard_exclude_hit = any(kw in text for kw in HARD_EXCLUDE_RESEARCH_DOMAINS)
    sector_hit = has_sector_signal(text)
    core_role_hit = has_core_tech_role_signal(text)

    # Excluir investigación de dominios no objetivo salvo que sea rol técnico claro.
    if (non_target_research_hit or hard_exclude_hit) and not core_role_hit:
        return False

    # Priorizamos empleos técnicos/IA/datos/finanzas directamente.
    if sector_hit:
        return True

    # Investigación solo si parece del sector objetivo (no biología/medicina/etc.).
    if research_hit and not non_target_research_hit and any(kw in text for kw in ["computer science", "informatikk", "ai", "data", "technology", "teknologi"]):
        return True

    return False


def translate_title_to_spanish(title):
    translated = title.lower()
    replacements = [
        ("ai agent", "agente de ia"),
        ("agentops engineer", "ingeniero de operaciones de agentes"),
        ("genai", "ia generativa"),
        ("machine learning engineer", "ingeniero de aprendizaje automático"),
        ("data scientist", "científico de datos"),
        ("data engineer", "ingeniero de datos"),
        ("qa engineer", "ingeniero de qa"),
        ("test engineer", "ingeniero de pruebas"),
        ("software engineer", "ingeniero de software"),
        ("software developer", "desarrollador de software"),
        ("backend / fullstack developer", "desarrollador backend / fullstack"),
        ("backend developer", "desarrollador backend"),
        ("frontend developer", "desarrollador frontend"),
        ("fullstack developer", "desarrollador fullstack"),
        ("full-stack developer", "desarrollador fullstack"),
        ("data analyst", "analista de datos"),
        ("business analyst", "analista de negocio"),
        ("business developer", "desarrollador de negocio"),
        ("machine learning", "aprendizaje automatico"),
        ("artificial intelligence", "inteligencia artificial"),
        ("developer", "desarrollador"),
        ("engineer", "ingeniero"),
        ("analyst", "analista"),
        ("advisor", "asesor"),
        ("consultant", "consultor"),
        ("specialist", "especialista"),
        ("research assistant", "asistente de investigación"),
        ("junior researcher", "investigador junior"),
        ("student", "estudiante"),
        ("intern", "prácticas"),
        ("trainee", "becario"),
        ("artificial intelligence", "inteligencia artificial"),
        ("full stack", "fullstack"),
        ("utvikler", "desarrollador"),
        ("analytiker", "analista"),
        ("forsker", "investigador"),
        ("ingenior", "ingeniero"),
    ]
    for old, new in replacements:
        translated = translated.replace(old, new)
    translated = " ".join(translated.split())
    if not translated:
        return title
    return translated[:1].upper() + translated[1:]


def score_job_for_profile(job):
    text = f"{job.get('title', '')} {job.get('description', '')} {job.get('employer', '')}".lower()
    reasons = []
    score = 0

    ai_hits = [kw for kw in PROFILE_AI_KEYWORDS if kw in text]
    if ai_hits:
        score += 52 + min(16, len(ai_hits) * 3)
        reasons.append((52, f"Muy alineada con IA, GenAI o agentes ({', '.join(ai_hits[:4])})"))

    data_hits = [kw for kw in PROFILE_DATA_KEYWORDS if kw in text]
    if data_hits:
        score += 45 + min(14, len(data_hits) * 3)
        reasons.append((45, f"Muy alineada con ciencia y analítica de datos ({', '.join(data_hits[:4])})"))

    finance_hits = [kw for kw in PROFILE_FINANCE_KEYWORDS if kw in text]
    if finance_hits:
        score += 35 + min(12, len(finance_hits) * 2)
        reasons.append((35, f"Con componente de finanzas o bolsa ({', '.join(finance_hits[:4])})"))

    role_hits = [kw for kw in PROFILE_ROLE_KEYWORDS if kw in text]
    if role_hits:
        role_weight = 30
        if any(kw in text for kw in ["backend", "fullstack", "frontend"]):
            role_weight += 10
        if any(kw in text for kw in ["analyst", "bi", "data scientist", "data engineer"]):
            role_weight += 12
        if any(kw in text for kw in ["qa", "test", "support"]):
            role_weight += 8
        score += role_weight + min(10, len(role_hits) * 2)
        reasons.append((role_weight, f"Rol alineado con tu perfil ({', '.join(role_hits[:4])})"))

    stack_hits = [kw for kw in PROFILE_STACK_KEYWORDS if kw in text]
    if stack_hits:
        stack_weight = 36
        if any(kw in text for kw in ["python", "sql", "power bi"]):
            stack_weight += 10
        score += stack_weight + min(14, len(stack_hits) * 3)
        reasons.append((stack_weight, f"Pide stack que dominas ({', '.join(stack_hits[:4])})"))

    bonus_hits = [kw for kw in PROFILE_BONUS_KEYWORDS if kw in text]
    if bonus_hits:
        score += 22 + min(10, len(bonus_hits) * 2)
        reasons.append((22, f"Tiene foco en IA o finanzas ({', '.join(bonus_hits[:4])})"))

    research_hits = [kw for kw in PROFILE_RESEARCH_KEYWORDS if kw in text]
    non_target_research_hits = [kw for kw in NON_TARGET_RESEARCH_KEYWORDS if kw in text]
    hard_exclude_hits = [kw for kw in HARD_EXCLUDE_RESEARCH_DOMAINS if kw in text]
    if research_hits:
        if has_sector_signal(text):
            score += 28 + min(10, len(research_hits) * 2)
            reasons.append((28, f"Investigación aplicada a tu sector ({', '.join(research_hits[:4])})"))
        else:
            score -= 26
            reasons.append((-26, "Investigación fuera de tu sector principal"))

    if non_target_research_hits and not has_sector_signal(text):
        score -= 22
        reasons.append((-22, "Área de investigación poco alineada con tu objetivo técnico"))

    if hard_exclude_hits and not has_core_tech_role_signal(text):
        score -= 45
        reasons.append((-45, "Dominio de investigación alejado de tu objetivo profesional"))

    junior_hits = [kw for kw in JUNIOR_POSITIVE_KEYWORDS if kw in text]
    if junior_hits:
        junior_weight = 30
        if any(kw in text for kw in ["intern", "trainee", "graduate", "entry-level", "junior"]):
            junior_weight += 12
        score += junior_weight
        reasons.append((junior_weight, "Menciona nivel junior o de entrada"))

    senior_hits = [kw for kw in SENIOR_NEGATIVE_KEYWORDS if kw in text]
    if senior_hits:
        score -= 10
        reasons.append((-10, "Parece orientada a un nivel senior alto"))
    else:
        score += 12
        reasons.append((12, "No indica un nivel senior alto claramente"))

    if any(kw in text for kw in ["university", "universitet", "institute", "academic", "research"]):
        score += 10
        reasons.append((10, "Vinculada al entorno universitario o de investigación"))

    reasons = [r for _, r in sorted(reasons, key=lambda x: x[0], reverse=True)]
    return score, reasons[:3]


def build_top_jobs(categorized, top_n=15):
    all_jobs = []
    for category, jobs in categorized.items():
        for job in jobs:
            score, reasons = score_job_for_profile(job)
            all_jobs.append({
                **job,
                "category": category,
                "score": score,
                "fit_reason": " | ".join(reasons),
                "title_es": translate_title_to_spanish(job.get("title", "")),
            })

    all_jobs.sort(key=lambda x: (x["score"], x.get("title", "")), reverse=True)
    return all_jobs[:top_n]


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

    # Búsquedas adicionales orientadas a tu perfil (IA, datos, finanzas, investigación técnica)
    extra_queries = [
        "fintech",
        "finance",
        "data analyst",
        "data scientist",
        "machine learning",
        "artificial intelligence",
        "genai",
        "llm",
        "computer science",
        "informatikk",
        "software developer",
    ]
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
        uid = job.get("uuid") or job.get("id") or job.get("adid") or job.get("url", "")
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

        # Filtro único por sector objetivo para ambas fuentes.
        passes = is_target_sector_job(title, description)

        if passes:
            category = categorize_job(title, description)
            matched[category].append(normalized)
            log(f"  [+] {title[:70]} | {source}")
        else:
            log(f"  [-] {title[:70]}")

    return matched

def build_email_html(top_jobs, stats=None):
    today = datetime.now().strftime("%d/%m/%Y")
    total = len(top_jobs)
    stats = stats or {}
    rows = ""
    for idx, j in enumerate(top_jobs, start=1):
        deadline = f"<br><small style='color:#888;'>⏰ Plazo: {j['deadline'][:10]}</small>" if j['deadline'] else ""
        rows += f"""
        <tr>
            <td style="padding:14px; border-bottom:1px solid #f0f0f0;">
                <div style="font-size:12px; color:#777; margin-bottom:4px;">#{idx} · Score {j['score']} · {j['category']}</div>
                <strong><a href="{j['url']}" style="color:#0057b8; text-decoration:none;">{j['title_es']}</a></strong><br>
                <small style="color:#666;">Título original: {j['title']}</small><br>
                <span style="color:#555;">🏢 Empresa: {j['employer']}</span><br>
                <span style="color:#555;">📍 Ubicación: {j['location']}</span>{deadline}<br>
                <small style="color:#1f4f8f;"><strong>Por qué encaja:</strong> {j['fit_reason']}</small><br>
                <small style="color:#666; font-weight:bold;">🔗 {SOURCE_ES.get(j['source'], j['source'])}</small>
            </td>
        </tr>
        """

    sections = f"""
    <div style="margin-bottom:24px;">
        <h3 style="background:#f0f4ff; padding:10px 16px; border-radius:6px; margin:0 0 8px;">
            Top {total} ofertas recomendadas para perfil junior
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
                <h2 style="margin:0; font-size:20px;">🇳🇴 Top ofertas en Noruega — {today}</h2>
                <p style="margin:6px 0 0; opacity:0.85; font-size:14px;">Top {total} ofertas priorizadas para tu perfil junior (IA, finanzas, universidad y tecnología)</p>
            </div>
            <div style="padding:24px 28px;">
                <div style="font-size:12px; color:#666; background:#f7f7f7; border:1px solid #eee; border-radius:8px; padding:8px 10px; margin-bottom:14px;">
                    Build: {BUILD_TAG} · Brutas: {stats.get('raw', 'n/a')} · Únicas: {stats.get('unique', 'n/a')} · Coinciden: {stats.get('matched', 'n/a')} · Top: {total}
                </div>
                {sections}
                <p style="margin-top:24px; color:#aaa; font-size:12px; border-top:1px solid #eee; padding-top:16px;">
                    Fuentes: <a href="https://arbeidsplassen.nav.no" style="color:#0057b8;">Arbeidsplassen NAV</a> · <a href="https://finn.no" style="color:#0057b8;">Finn.no</a> — Ranking junior personalizado para Alejandro Sánchez Tilve
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
    msg["Subject"] = f"[{BUILD_TAG}] 🇳🇴 Top {job_count} ofertas para ti — {datetime.now().strftime('%d/%m/%Y')}"
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
        log(f"   {CATEGORY_ES.get(cat, cat)}: {len(jobs)}")

    top_jobs = build_top_jobs(categorized, top_n=15)
    log(f"\n🏆 Top seleccionadas para perfil junior: {len(top_jobs)}")
    
    print("\n" + "="*70)
    log("=== FIN EJECUCIÓN ===")
    stats = {"raw": len(raw_jobs), "unique": len(unique_jobs), "matched": total}
    html, count = build_email_html(top_jobs, stats=stats)
    try:
        EMAIL_PREVIEW_FILE.write_text(html, encoding="utf-8")
        log(f"📝 Preview email guardada en {EMAIL_PREVIEW_FILE}")
    except Exception as e:
        log(f"⚠️  No se pudo guardar preview email: {str(e)[:120]}")
    send_email(html, count)
if __name__ == "__main__":
    main()