#!/usr/bin/env bash
set -o errexit

cd backend
python manage.py migrate --no-input

if [ "${LOAD_FIXTURES_ON_DEPLOY,,}" = "true" ] || [ "$LOAD_FIXTURES_ON_DEPLOY" = "1" ]; then
  echo "Loading fixture data from backend/fixtures/db_fixture.json"
  python manage.py loaddata fixtures/db_fixture.json
else
  echo "Skipping fixture load. Set LOAD_FIXTURES_ON_DEPLOY=true to enable it."
fi
