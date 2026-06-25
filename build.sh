#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

cd frontend
npm ci
npm run build

cd ../backend
python manage.py collectstatic --no-input
python manage.py migrate --no-input

if [ "$LOAD_FIXTURES_ON_DEPLOY" = "true" ]; then
  python manage.py loaddata fixtures/db_fixture.json
fi
