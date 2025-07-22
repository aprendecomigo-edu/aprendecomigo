# Aprende Comigo

A platform for managing classes, teachers and students. This repository contains both the Django backend and the React Native frontend.

## Directory Layout

- `backend/` – Django REST Framework API. See [backend/README.md](backend/README.md) for full setup and usage.
- `frontend-ui/` – Expo based React Native app. See [frontend-ui/README.md](frontend-ui/README.md) for details.
- `docs/` – Additional documentation such as [environment-setup.md](docs/environment-setup.md).

## Quickstart

### Backend
1. `cd backend`
2. `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
4. `pip install -r requirements.txt`
5. Copy `env.example` to `.env` and adjust settings
6. `python manage.py migrate`
7. `python manage.py runserver`
   *(use `python manage.py runsslserver` for HTTPS)*

### Frontend
1. `cd frontend-ui`
2. `npm install --legacy-peer-deps`
3. `npx expo start`

For more extensive instructions see the documentation linked above.
