import requests
import json
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# --- CONFIGURACIÓN ---
RECIPIENT_EMAIL = "alejandrosancheztilve02@gmail.com"
SENDER_EMAIL = os.environ.get("GMAIL_USER")
SENDER_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# Palabras clave adaptadas al perfil de Alejandro
KEYWORDS = [
    "python", "developer", "utvikler", "automation", "automatisering",
    "IT", "software", "backend", "data", "AI", "machine learning",
    "integrasjon", "integration", "support", "tekniker", "technician",
    "fintech", "finance", "system", "network", "nettverks", "drift"
]

# Palabras a excluir (evitar ofertas que exijan noruego fluido explícitamente)
EXCLUDE_KEYWORDS = ["kun norsk", "flytende norsk", "morsmål norsk"]

def fetch_jobs():
    """Fetches jobs from arbeidsplassen.nav.no public API"""
    url = "https://arbeidsplassen.nav.no/api/v1/ads"
    params = {
        "size": 100,
        "sort": "published",
        "v": "2"
    }
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return None

def filter_jobs(data):
    """Filters jobs by keywords relevant to Alejandro's profile"""
    if not data or "content" not in data:
        return []
    
    matched = []
    for job in data["content"]:
        title = job.get("title", "").lower()
        description = (job.get("description", "") or "").lower()
        text = title + " " + description

        # Excluir si requiere noruego fluido explícitamente
        if any(excl in text for excl in EXCLUDE_KEYWORDS):
            continue

        # Incluir si contiene alguna keyword relevante
        if any(kw.lower() in text for kw in KEYWORDS):
            matched.append({
                "title": job.get("title", "Sin título"),
                "employer": job.get("employer", {}).get("name", "Empresa desconocida"),
                "location": job.get("location", ""),
                "deadline": job.get("applicationDue", ""),
                "url": f"https://arbeidsplassen.nav.no/stillinger/stilling/{job.get('uuid', '')}",
                "published": job.get("published", "")
            })
    
    return matched

def build_email_html(jobs):
    """Builds a clean HTML email with the job listings"""
    today = datetime.now().strftime("%d/%m/%Y")
    count = len(jobs)
    
    if count == 0:
        body = "<p>No se encontraron ofertas nuevas relevantes hoy. Inténtalo mañana 💪</p>"
    else:
        rows = ""
        for j in jobs:
            deadline = f"<br><small>⏰ Plazo: {j['deadline'][:10]}</small>" if j['deadline'] else ""
            rows += f"""
            <tr>
                <td style="padding:12px; border-bottom:1px solid #eee;">
                    <strong><a href="{j['url']}" style="color:#0057b8; text-decoration:none;">{j['title']}</a></strong><br>
                    🏢 {j['employer']}<br>
                    📍 {j['location']}{deadline}
                </td>
            </tr>
            """
        body = f"""
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse; font-family:Arial,sans-serif; font-size:14px;">
            {rows}
        </table>
        """

    html = f"""
    <html>
    <body style="background:#f4f4f4; padding:20px;">
        <div style="max-width:650px; margin:auto; background:white; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.1);">
            <div style="background:#0057b8; color:white; padding:20px 24px;">
                <h2 style="margin:0;">🇳🇴 Ofertas en Noruega — {today}</h2>
                <p style="margin:4px 0 0; opacity:0.85;">{count} ofertas relevantes encontradas en arbeidsplassen.nav.no</p>
            </div>
            <div style="padding:20px 24px;">
                {body}
                <p style="margin-top:24px; color:#888; font-size:12px;">
                    Fuente: <a href="https://arbeidsplassen.nav.no">arbeidsplassen.nav.no</a> — 
                    Filtrado por keywords IT/Tech/Fintech para el perfil de Alejandro Sánchez Tilve
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_email(html_content, job_count):
    """Sends the email via Gmail SMTP"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🇳🇴 {job_count} ofertas en Noruega hoy — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    
    msg.attach(MIMEText(html_content, "html"))
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    
    print(f"✅ Email enviado con {job_count} ofertas a {RECIPIENT_EMAIL}")

def main():
    print("🔍 Buscando ofertas en arbeidsplassen.nav.no...")
    data = fetch_jobs()
    jobs = filter_jobs(data)
    print(f"✅ {len(jobs)} ofertas relevantes encontradas")
    
    html = build_email_html(jobs)
    send_email(html, len(jobs))

if __name__ == "__main__":
    main()
