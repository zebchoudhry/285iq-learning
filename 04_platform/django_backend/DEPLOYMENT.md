# 285IQ Platform – Deployment

## Deploy on Vercel

This Django app can run on Vercel as a serverless function. **SQLite does not work on Vercel** — you must use PostgreSQL (Vercel Postgres, Neon, or Supabase).

### 1. Vercel project settings (critical)

In the Vercel dashboard → your project → **Settings → General**:

| Setting | Value |
|---------|--------|
| **Root Directory** | `04_platform/django_backend` |
| **Framework Preset** | Other (or Django if offered) |
| **Build Command** | `python manage.py collectstatic --noinput` (or leave empty to use `pyproject.toml`) |
| **Install Command** | `pip install -r requirements.txt` |

If Root Directory is the repo root, Vercel will not find `manage.py` and the deploy will fail.

### 2. Environment variables (Vercel → Settings → Environment Variables)

| Variable | Required | Example |
|----------|----------|---------|
| `SECRET_KEY` | Yes | long random string |
| `DEBUG` | Yes | `False` |
| `DATABASE_URL` | Yes | `postgres://...` (from Vercel Postgres or Neon) |
| `ALLOWED_HOSTS` | Yes | `your-app.vercel.app,285iq.com,www.285iq.com` |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://your-app.vercel.app,https://285iq.com` |

Optional: `LLM_*`, `STRIPE_*`, `ANTHROPIC_API_KEY` as in `.env.example`.

### 3. Database migrations

After the first successful deploy (or from your machine with env pulled):

```bash
cd 04_platform/django_backend
# Set DATABASE_URL to the same value as on Vercel, then:
python manage.py migrate
python manage.py createsuperuser
```

### 4. Redeploy

Push to GitHub; Vercel rebuilds automatically. Check **Deployments → Build Logs** if it fails.

### Why deploys often fail

- **Wrong root directory** — most common; must be `04_platform/django_backend`
- **No `DATABASE_URL`** — app falls back to SQLite, which is read-only/ephemeral on Vercel
- **Missing `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`** for your `*.vercel.app` URL
- **Build timeout** — large repo; `.vercelignore` excludes venv and heavy assets

For a traditional always-on server, use **Docker** (below) or **Railway / Render** instead of Vercel.

---

## Production with Docker

1. **Copy environment file and set required variables**
   ```bash
   cp .env.example .env
   # Edit .env: set SECRET_KEY and DB_PASSWORD at minimum.
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```
   The web service runs migrations on startup, then starts Gunicorn on port 8000.

3. **Optional: create a superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Optional: collect static files (if serving via same app)**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   ```
   Serve the `staticfiles` directory with your reverse proxy (e.g. nginx) or add WhiteNoise to the app.

## Environment variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret (required in production). |
| `DEBUG` | Set to `False` in production. |
| `DB_ENGINE` | Set to `django.db.backends.postgresql` when using PostgreSQL. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection (used when `DB_ENGINE` is set). |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host names. |
| `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL` | Email for password reset and notifications. |

## Database migration

- **Docker:** Migrations run automatically when the web container starts.
- **Manual:** Run `python manage.py migrate` after setting `DB_ENGINE` and DB_* in `.env`.

## Security checklist

- Use a strong `SECRET_KEY` and keep it secret.
- Set `DEBUG=False` in production.
- Restrict `ALLOWED_HOSTS` to your domain(s).
- Use HTTPS and set `SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` if needed (see Django docs).
- Configure CORS and CSRF (`CSRF_TRUSTED_ORIGINS`) if the frontend is on a different domain.
