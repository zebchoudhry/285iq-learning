# 285IQ Platform – Deployment

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
