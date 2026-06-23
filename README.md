# GameFit

Vue + Pinia frontend and Django Rest Framework backend prototype based on the wireframe.

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r ..\requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## AI Search Server

```bash
uvicorn ai_service.main:app --host 127.0.0.1 --port 8002 --reload
```

The game explore page supports both title search and FastAPI-based natural-language AI search.

Main API endpoints:

- `POST /api/accounts/signup/`
- `POST /api/accounts/login/`
- `POST /api/accounts/logout/`
- `GET/PATCH /api/accounts/profile/`
- `GET /api/catalog/games/`
- `GET /api/catalog/equipment/`
- `GET /api/catalog/recommendations/`
- `GET /api/catalog/calendar/`

Login and signup return:

```json
{
  "token": "drf-token",
  "user": {
    "username": "player",
    "nickname": "player",
    "pc_specs": {},
    "owned_games": [],
    "interested_games": []
  }
}
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend stores the DRF token in `localStorage.authToken` through the Pinia auth store. Axios attaches it to API calls as:

```http
Authorization: Token <token>
```

For a single-port local check, build the Vue app and run Django:

```bash
cd frontend
npm run build
cd ..\backend
python manage.py runserver 127.0.0.1:8000
```

Then open `http://127.0.0.1:8000`.

## Pages

The frontend pages are laid out as Figma-style wireframe frames: centered `681px` screens, low-fidelity boxed sections, side tabs for profile edit, horizontal game/equipment tiles, and detail pages split into main content plus right-side compatibility/group panels.

- `frontend/src/pages/welcome`: Welcome with login/signup popup modals
- `frontend/src/pages/profile`: Profile, Profile Edit
- `frontend/src/pages/games`: Game Explore, Game Detail
- `frontend/src/pages/community`: Community
- `frontend/src/pages/equipment`: Equipment Explore, Equipment Detail
- `frontend/src/pages/analysis`: Taste Analysis
- `frontend/src/pages/calendar`: Calendar

## Backend Structure

- `backend/account`: signup, login, logout, profile token auth
- `backend/catalog/game_views.py`: game explore and game detail APIs
- `backend/catalog/equipment_views.py`: equipment explore and equipment detail APIs
- `backend/catalog/community_views.py`: game community posts
- `backend/catalog/analysis_views.py`: game taste analysis and recommendations
- `backend/catalog/calendar_views.py`: sale, release, and alert calendar
- `backend/catalog/data.py`: temporary sample data for wireframe development
