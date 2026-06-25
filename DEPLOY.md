# GameFit Deploy Guide

## Render Blueprint

1. Push this repository to GitHub.
2. In Render, create a new Blueprint from this repository.
3. Render reads `render.yaml`, creates the `gamefit` web service, and provisions `gamefit-db`.
4. In the web service environment, fill these secret values:
   - `GMS_API_KEY`
   - `IS_THERE_ANY_DEAL_API_KEY`
   - `STEAM_WEB_API_KEY`
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`

## Build and Start

Render uses:

```bash
bash build.sh
```

The build script installs Python dependencies, builds the Vue frontend, collects static files, and runs migrations.

The service starts with:

```bash
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

## Initial Data

The production PostgreSQL database starts empty. After the first successful deploy, open the Render Shell for the `gamefit` service and run:

```bash
cd backend
python manage.py loaddata fixtures/db_fixture.json
```

Run this only when you intentionally want to seed or refresh fixture data.

## Local Production Check

```bash
cd frontend
npm run build
cd ..
venv\Scripts\python.exe backend\manage.py check
venv\Scripts\python.exe backend\manage.py collectstatic --no-input
```
