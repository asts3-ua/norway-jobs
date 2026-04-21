# 🔧 Scraper de Ofertas de Trabajo - Documentación

## 📋 Portales Buscados

### 1. **arbeidsplassen.nav.no** (Nav - Servicio Estatal Noruego)
- URL de búsqueda: `https://arbeidsplassen.nav.no/stillinger?q={keyword}`
- Método: API JSON + Web Scraping (fallback)
- Keywords: developer, python, IT, automation, research informatikk, fintech, software engineer

### 2. **finn.no** (Sitio Clasificado Noruego)
- URL de búsqueda: `https://www.finn.no/job/listing?q={keyword}`
- Método: Web Scraping HTML
- Keywords: developer, python, IT, automation, research, fintech, software engineer

## 🎯 Filtros Aplicados

### Palabras Clave por Categoría:

**💻 IT/Tech** (47 keywords):
- Lenguajes: python, java, javascript, php, sql
- Roles: developer, backend, frontend, fullstack, devops
- Tecnologías: cloud, azure, aws, database, integration, automation
- Y más...

**💹 Finanzas/Fintech** (14 keywords):
- fintech, finance, financial, BI, business analyst, data analyst
- investment, accounting, economist

**🔬 Investigación** (14 keywords):
- research, PhD, postdoc, university, innovation, R&D, laboratory

## 📧 Configuración del Email

- **Frecuencia**: Diaria a las 7:00 UTC (8:00 CET/CEST)
- **Envío via**: Gmail SMTP (requiere variables de entorno)
- **Variables necesarias**:
  - `GMAIL_USER`: Tu email de Gmail
  - `GMAIL_APP_PASSWORD`: Contraseña de aplicación (no la contraseña normal)

## 🔄 Proceso de Ejecución

1. Busca en ambos portales con diferentes keywords
2. Deduplica resultados entre portales
3. Filtra solo las ofertas relevantes según keywords
4. Categoriza en IT/Tech, Finanzas o Investigación
5. Construye email HTML formateado
6. Envía email

## 🐛 Debugging

Si no encuentras resultados:

1. **Verifica conectividad**:
   ```bash
   python test_apis.py
   ```

2. **Habilita print detallado** en `scraper.py`

3. **Comprueba variables de entorno**:
   ```powershell
   echo $env:GMAIL_USER
   echo $env:GMAIL_APP_PASSWORD
   ```

## 📝 Logs de Ejecución

El script imprime:
- Ofertas encontradas por portal y keyword
- Ofertas únicas después de deduplicar
- Ofertas relevantes por categoría
- Confirmación de email enviado o error

## 🚀 Ejecución Manual

```bash
python scraper.py
```

## 📅 Ejecución Automática (GitHub Actions)

Configurado en `.github/workflows/daily_jobs.yml`
- Ejecuta automáticamente cada día a las 7:00 UTC
- Puede ejecutarse manualmente desde GitHub Actions UI
