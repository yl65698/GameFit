# GameFit Render Deploy Guide

## Render Blueprint

1. Push this repository to GitHub.
2. In Render, create a new Blueprint from this repository.
3. Render reads `render.yaml`, creates the `gamefit` web service, and provisions `gamefit-db`.
4. In the `gamefit` web service environment, fill these secret values:
   - `GMS_API_KEY`
   - `IS_THERE_ANY_DEAL_API_KEY`
   - `STEAM_WEB_API_KEY`
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`

## Build, Pre-Deploy, and Start

Render builds with:

```bash
bash build.sh
```

The build script installs Python dependencies, builds the Vue frontend, and collects static files.

Before each deploy, Render runs:

```bash
bash predeploy.sh
```

The pre-deploy script runs migrations and optionally loads fixture data.

The service starts with:

```bash
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

## Initial Fixture Data

The production PostgreSQL database starts empty. To seed fixture data without using Render Shell, temporarily set this environment variable in the Render `gamefit` web service:

```bash
LOAD_FIXTURES_ON_DEPLOY=true
```

Then redeploy once. During deploy, check the Render logs for:

```bash
Loading fixture data from backend/fixtures/db_fixture.json
Installed 70445 object(s) from 1 fixture(s)
```

After the fixture data is loaded, set it back to:

```bash
LOAD_FIXTURES_ON_DEPLOY=false
```

This prevents fixture data from being refreshed on every deploy.

## Local Production Check

```bash
cd frontend
npm run build
cd ..
venv\Scripts\python.exe backend\manage.py check
venv\Scripts\python.exe backend\manage.py collectstatic --no-input
```
