# Task Manager

A simple task management web app built with FastAPI and plain HTML/JS. Users can register, log in, and manage their own tasks — create, view, complete, and delete them. Authentication is handled with JWT tokens and passwords are stored as bcrypt hashes.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite (easily swappable to PostgreSQL)
- **Auth**: JWT via `python-jose`, password hashing via `passlib[bcrypt]`
- **Frontend**: Plain HTML + CSS + JavaScript (no build step needed)
- **Tests**: pytest + FastAPI's TestClient

---

## Project Structure

```
taskmanager/
├── backend/
│   ├── app/
│   │   ├── core/          # config, security utils, auth dependency
│   │   ├── db/            # SQLAlchemy engine + session
│   │   ├── models/        # ORM models (User, Task)
│   │   ├── routers/       # route handlers (auth, tasks)
│   │   ├── schemas/       # Pydantic request/response models
│   │   └── main.py        # app factory + CORS + table init
│   ├── tests/
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   └── index.html         # self-contained SPA (no framework)
├── docker-compose.yml
└── README.md
```

---

## Environment Variables

Copy `.env.example` to `.env` inside the `backend/` folder and fill in your values:

```
SECRET_KEY=<a long random string — use `openssl rand -hex 32`>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./taskmanager.db
```

Never commit `.env` — it's in `.gitignore`.

---

## Running Locally

### Option 1 — Plain Python (quickest)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # then edit .env

uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.  
The frontend is served at `http://localhost:8000/` (FastAPI mounts the `frontend/` folder automatically).  
Interactive API docs: `http://localhost:8000/docs`

### Option 2 — Docker Compose

```bash
cp backend/.env.example backend/.env   # edit .env first
docker compose up --build
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

All tests use an isolated SQLite database that's created and torn down automatically per test.

---

## API Overview

| Method | Endpoint | Auth required | Description |
|--------|----------|:---:|-------------|
| POST | `/register` | — | Create a new user account |
| POST | `/login` | — | Returns a JWT access token |
| POST | `/tasks` | ✓ | Create a task |
| GET | `/tasks` | ✓ | List tasks (paginated, filterable) |
| GET | `/tasks/{id}` | ✓ | Get a specific task |
| PUT | `/tasks/{id}` | ✓ | Update title / description / completion |
| DELETE | `/tasks/{id}` | ✓ | Delete a task |
| GET | `/health` | — | Health check |

### Query params for `GET /tasks`
- `?completed=true` — only completed tasks
- `?completed=false` — only pending tasks
- `?page=1&page_size=10` — pagination (default page_size is 10, max 100)

---

## Deployment (Render)

1. Push to a public GitHub repo.
2. Create a new **Web Service** on [Render](https://render.com), pointing to the `backend/` directory.
3. Set the build command:
   ```
   pip install -r requirements.txt
   ```
4. Set the start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Add environment variables (`SECRET_KEY`, `DATABASE_URL`, etc.) in the Render dashboard.

> **Tip**: For a persistent database on Render's free tier, set `DATABASE_URL` to a PostgreSQL connection string (Render provides a free Postgres instance). SQLAlchemy will handle the rest without code changes.

---

## Live Demo

https://task-manager-24v6.onrender.com
