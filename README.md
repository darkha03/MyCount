MyCount
=======

A simple, learning-focused expense sharing app built with Flask. Create shared plans, add expenses, split costs between participants, see who owes whom, and visualize balances with charts.

Note: This is a work-in-progress learning project. The codebase demonstrates Flask blueprints, authentication, SQLAlchemy models and migrations, a responsive Bootstrap UI, and basic data visualization with Chart.js.

Tech stack
----------

- Backend: Python 3.13, Flask 3, Gunicorn, SQLAlchemy 2, Flask-Migrate (Alembic)
- Frontend: Bootstrap 5.3, Chart.js, vanilla JS modules in `backend/static/js`
- Database: PostgreSQL (default in Docker), SQLite fallback for local CLI use
- Ops: Docker Compose (published image `darkha03/mycount:latest`), Nginx reverse proxy
- Tooling: Ruff, Pytest, multi-stage Dockerfile (test, lint, dev, prod)

Project structure (high level)
------------------------------

- backend/: app factory, blueprints (auth, plans), models, templates, static assets, utilities
- migrations/: Alembic migrations (checked in)
- tests/: Pytest suite (fixtures + feature/unit coverage)
- Dockerfile: multi-stage (test, lint, dev, prod)
- docker-compose.yml: prod-ish stack (app, nginx, Postgres, volume)
- docker-compose.override.yml: dev profile (bind mount, reload on code change)
- entrypoint.sh: waits for Postgres, applies migrations, starts Gunicorn

Features (high level)
---------------------

- Auth and profiles: session auth, profile edit/change password
- Plans: create/view/edit/delete or leave; shareable hash IDs; responsive cards on dashboard
- Expenses: add/edit/delete, per-participant splits (even/custom), grouped by day
- Reimbursements: greedy settle-up, “Mark as Paid” posts an expense
- Statistics: Chart.js balances per participant; totals vs real expenses datasets
- Exports: CSV/XLSX per plan with participant columns (openpyxl)
- Security: local DOMPurify, CSP-friendly external scripts, safe fallbacks in helpers
- DX: blueprints, helpers for exports, strict CSP defaults in config


What’s implemented and learned
------------------------------

- Flask app factory + blueprints with auth and plans separation
- SQLAlchemy models with relationships and Alembic migrations (checked in)
- DOMPurify + CSP-friendly layout and externalized JS to reduce XSS surface
- Responsive Bootstrap UI, Chart.js integration, modular JS with reload-safe handlers
- Multi-stage Docker build (test, lint, dev, prod) and Compose wiring (nginx, Postgres, app)
- CI pipeline with ruff and pytest; migrations auto-run on container start

How to use (quick tour)
-----------------------

- Create or join a plan from the Plans page
- Add expenses, select payer, split amounts (evenly or manually)
- View reimbursements and optionally “Mark as Paid” to settle
- See statistics (balances, totals) and a bar chart summarizing the plan

API/Routes (selected)
---------------------

- `GET /` → Dashboard (recent plans, reimbursements)
- `GET /plans` → Plans dashboard (cards)
- `GET /plans/<hash_id>` → View plan with sections (expenses, reimbursements, statistics)
- `GET /plans/api/plans` → JSON list of user’s plans
- `POST /plans/api/plans` → Create a new plan
- `PUT /plans/api/plans/<plan_id>` → Modify plan
- `DELETE /plans/api/plans/<plan_id>` → Leave/delete plan

Note: Most plan actions are under the `plans` blueprint and require login.

Screenshots / Demo
---------------------------------

- Live demo: https://darkha03.pythonanywhere.com/

- Screenshots: 

![Dashboard](docs/dashboard.jpg)
![Plan Details](docs/plan.jpg)
![Expenses Section](docs/expense.jpg)
![Create Expense](docs/create-expense.jpg)
![Reimbursement Section](docs/reimbursement.jpg)
![Statistic Section](docs/statistic.jpg)


Install and deploy (Docker)
---------------------------

- Services: `db` (PostgreSQL 16, volume `postgres_data`), `app` (Gunicorn + Flask), `nginx` (proxy). Entrypoint waits for Postgres and runs `flask db upgrade` before Gunicorn.
- Env file consumed by `app` (example):

```
SECRET_KEY=change-me
DATABASE_URL=postgresql+psycopg://postgres:password@db:5432/mydb
SESSION_COOKIE_SECURE=false
```

Install (prod-like)
-------------------

- Run: `docker compose up -d`
- Visit: http://localhost:8080 (nginx → app on 8000). Port 443 is exposed for custom TLS if you mount your own certs in nginx.
- Stop: `docker compose down`
- Reset data: `docker compose down -v` (drops `postgres_data`).

Develop (hot reload)
--------------------

- Run dev profile with bind mount and Flask reload:

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Access: http://localhost:5000
- Stop: `docker compose --profile dev down`

Environment variables (containers)
----------------------------------

- `SECRET_KEY` (required) – session signing key
- `DATABASE_URL` (required) – e.g., `postgresql+psycopg://postgres:password@db:5432/mydb`
- `SESSION_COOKIE_SECURE` (optional) – `true` when served over HTTPS

Getting started
---------------

Prerequisites
-------------

- Python 3.10+ (recommended)
- Works on Windows, Linux, and macOS

Setup
-----

**Windows (Command Prompt):**
```cmd
:: from project root
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
# from project root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure environment (optional)
--------------------------------

- App reads settings from `backend/config.py`. You can override via environment variables:
	- `SECRET_KEY` (session signing)
	- `DATABASE_URL` (e.g., `sqlite:///C:\\path\\to\\mycount.db` or Postgres URL)
- Default SQLite DB is created at `<project_root>\instance\mycount.db` (auto-created).

Initialize the database
-----------------------

Using Flask-Migrate (Alembic):

Important: This repo already includes a populated `migrations/` folder. On a fresh clone, you typically do NOT run `flask db init` or `flask db migrate`. Just run `flask db upgrade` to create the database and tables.

**Windows (Command Prompt):**
```cmd
:: tell Flask where the app factory is
set FLASK_APP=backend.app:create_app

:: apply migrations
flask db upgrade
```

**Linux / macOS:**
```bash
# tell Flask where the app factory is
export FLASK_APP=backend.app:create_app

# apply migrations
flask db upgrade
```

If you already have a `migrations/` folder in the repo (this project does), skip `flask db init` and `flask db migrate` and run only `flask db upgrade`.

Run the app (development)
-------------------------

**Windows (Command Prompt):**
```cmd
set FLASK_APP=backend.app:create_app
set FLASK_DEBUG=1
flask run
```

**Windows (PowerShell):**
```powershell
$env:FLASK_APP="backend.app:create_app"
$env:FLASK_DEBUG="1"
flask run
```

**Linux / macOS:**
```bash
export FLASK_APP=backend.app:create_app
export FLASK_DEBUG=1
flask run
```

- Now open http://127.0.0.1:5000/
- If you hit a login page, create or seed a user as needed.

Common migration commands (cross-platform)
-------------------------------------------

```bash
# Create a new migration after model changes
flask db migrate -m "describe your changes"

# Apply pending migrations
flask db upgrade

# Show current migration version
flask db current

# Show migration history
flask db history

# Rollback one migration
flask db downgrade
```

Local test
-----

Run the local test with docker
```bash
docker build --target test -t mycount-test .
docker run --rm mycount-test
docker build --target lint -t mycount-lint .
docker run --rm mycount-lint
```

CI/CD
-----

- Tests + lint: multi-stage Dockerfile targets `test` (pytest -q) and `lint` (ruff check .).
- GitHub Actions (example `.github/workflows/ci.yml`): checkout → setup Python 3.11 → install `requirements.txt` + `requirements-dev.txt` → run ruff → run pytest.
- Pre-commit friendly: repo includes ruff/pytest configs; enable hooks locally for parity.
- Deploy: container-first. Use the published image (`darkha03/mycount:latest`) with the prod Compose stack; entrypoint auto-applies migrations. Render/PythonAnywhere remain possible but Docker is the primary path.

- Build Command: `pip install -r requirements.txt`
- Start Command: `bash start.sh`

Environment variables on Render (Dashboard → Environment):

- `SECRET_KEY` (required)
- `DATABASE_URL` (required; e.g., `postgresql+psycopg://user:pass@host:6543/dbname`)

Optional GitHub Actions deploy step (requires secrets):

- `RENDER_API_KEY`: a Render API key
- `RENDER_SERVICE_ID`: the service ID to deploy

Deploy job example (add to the same workflow and gate on `main`):

```yaml
	deploy-render:
		if: github.ref == 'refs/heads/main'
		needs: build-and-test
		runs-on: ubuntu-latest
		steps:
			- uses: actions/checkout@v4
			- name: Trigger Render deploy
				env:
					RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
					RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
				run: |
					curl -s -X POST \
						-H "Authorization: Bearer $RENDER_API_KEY" \
						-H "Content-Type: application/json" \
						https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys
```

PythonAnywhere deployment (pull-based)
--------------------------------------

For PythonAnywhere, deployments are handled by a scheduled task that pulls the latest code, installs dependencies, applies migrations, and reloads the app. Use the provided script:

- `scripts/pull_and_reload.sh` — set it as a Scheduled Task in PythonAnywhere.
- Create an `env.sh` (not committed) alongside it to export secrets before running:

```bash
export SECRET_KEY="your-prod-secret"
export DATABASE_URL="mysql+mysqldb://user:pass@host/dbname"
```

Then schedule the task to run the script, e.g.:

```bash
bash ~/mycount/scripts/pull_and_reload.sh
```

WSGI entry point for PythonAnywhere is `wsgi.py`, which imports `create_app()` from `backend.app`.

Environment & security recap
----------------------------

- Never commit real secrets; set them via your hosting provider or `env.sh` (PythonAnywhere).
- `DATABASE_URL` is normalized automatically: `postgres` → `postgresql+psycopg`, `mysql` → `mysql+mysqldb`.
- Default dev DB is SQLite stored under `instance/mycount.db` and created automatically.


