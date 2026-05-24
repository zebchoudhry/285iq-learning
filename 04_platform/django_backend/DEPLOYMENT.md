# 285IQ Platform – Deployment

## Deploy on Vercel

This Django app can run on Vercel as a serverless function. **SQLite does not work on Vercel** — you must use PostgreSQL (Vercel Postgres, Neon, or Supabase).

### 1. Vercel project settings (critical)

In the Vercel dashboard → your project → **Settings → General**:

| Setting | Value |
|---------|--------|
| **Root Directory** | *(empty / repository root)* **or** `04_platform/django_backend` |
| **Framework Preset** | **Django** (or Auto) |
| **Build Command** | *(leave empty)* |
| **Install Command** | *(leave empty)* |

The repo includes a **root `manage.py` and `wsgi.py`** so Vercel detects Django even when Root Directory is the whole repository (fixes ~100ms empty builds).

If a build log shows **“Build Completed in ~100ms”** with no `pip install`, Root Directory was wrong and Django was not detected — redeploy after pulling the latest `main`.

**Private GitHub repo:** In GitHub → Settings → Applications → Vercel → configure access to private repositories. In Vercel → Project → Settings → Git, confirm the repo is connected and redeploy.

### 2. Environment variables (Vercel → Settings → Environment Variables)

| Variable | Required | Example |
|----------|----------|---------|
| `SECRET_KEY` | Yes | long random string |
| `DEBUG` | Yes | `False` |
| `DATABASE_URL` | **Yes** | `postgres://...` (Vercel Postgres sets this automatically) |
| `ALLOWED_HOSTS` | Yes | `your-app.vercel.app,285iq.com,www.285iq.com` |
| `CSRF_TRUSTED_ORIGINS` | Yes | `https://your-app.vercel.app,https://285iq.com` |

Vercel Postgres also provides `POSTGRES_URL` — either works.

**500 FUNCTION_INVOCATION_FAILED** almost always means missing `DATABASE_URL` or migrations not applied. Check `https://your-app.vercel.app/api/health/` after deploy (should return `"database": true`).

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

### Why you see `404: NOT_FOUND` (Vercel white error page)

That is Vercel’s edge saying **no deployment is serving this URL** — not Django. Check:

1. **Deployments** tab — latest build must be **Ready** (green), not Error or Canceled
2. **Root Directory** = `04_platform/django_backend`
3. **Do not** set Framework to “Other” with a blank app — use **Django** or Auto
4. **Remove** custom `vercel.json` with `"framework": null` (disabled in this repo)
5. **Private repo** — Vercel must have GitHub access (see above)

### Other common failures

- **No `DATABASE_URL`** — use Vercel Postgres or Neon; set `DATABASE_URL` in env vars
- **Missing `CSRF_TRUSTED_ORIGINS`** — include `https://your-project.vercel.app`
- **Build timeout** — `.vercelignore` excludes venv and large assets

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
