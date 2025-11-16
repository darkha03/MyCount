MyCount
=======

A simple, learning-focused expense sharing app built with Flask. Create shared plans, add expenses, split costs between participants, see who owes whom, and visualize balances with charts.

Note: This is a work-in-progress learning project. The codebase demonstrates Flask blueprints, authentication, SQLAlchemy models and migrations, a responsive Bootstrap UI, and basic data visualization with Chart.js.

Tech stack
----------

- Backend
	- Python 3.x, Flask 3.x
	- Flask-Migrate (Alembic) for schema migrations
	- SQLAlchemy 2.x ORM (SQLite by default)
	- Jinja2 templating
- Frontend
	- Bootstrap 5.3 (responsive layout and components)
	- Chart.js (bar charts for statistics)
	- Vanilla JavaScript (global scripts in `backend/static/js/app.js`)
- Tooling
	- `pip` with a pinned `requirements.txt`

Project structure
-----------------

```
mycount/
├─ backend/
│  ├─ app.py                      # Flask app factory (create_app), blueprints registration
│  ├─ config.py                   # Centralized Flask/DB configuration
│  ├─ models.py                   # SQLAlchemy models: User, Plan, PlanParticipant, Expense, ExpenseShare
│  ├─ routes/
│  │  ├─ auth/                    # Auth blueprint (login/logout)
│  │  └─ plans/                   # Plans blueprint (CRUD, sections)
│  ├─ templates/
│  │  ├─ layout.html              # Base layout (Bootstrap, nav, global JS/CSS)
│  │  ├─ index.html               # Dashboard (recent plans + reimbursements)
│  │  ├─ auth/                    # Login/Register views
│  │  └─ plans/                   # Plan pages (dashboard, expenses, statistics, reimbursements, view)
│  ├─ static/
│  │  ├─ css/style.css            # Global styling
│  │  └─ js/app.js                # Global JS (page-specific hooks)
│  └─ utils/auth.py               # @login_required decorator
│
├─ migrations/                    # Alembic migrations (checked-in)
│  ├─ env.py
│  ├─ alembic.ini
│  ├─ script.py.mako
│  └─ versions/                   # Auto-generated migration scripts
│
├─ instance/                      # SQLite DB lives here (created at runtime)
├─ tests/                         # Pytest suite (fixtures + unit/feature tests)
│  ├─ conftest.py                 # App/test client + factory fixtures
│  ├─ test_auth.py                # Auth flow tests (register/login)
│  ├─ test_plans.py               # Plan creation & retrieval tests
│  └─ test_statistics.py          # Pure logic tests (balance/expense calculations)
│
├─ scripts/
│  └─ pull_and_reload.sh          # PythonAnywhere scheduled deployment script
├─ start.sh                       # Render start script (migrations + gunicorn)
├─ wsgi.py                        # PythonAnywhere WSGI entrypoint
├─ docs/                          # Screenshots and documentation assets
├─ requirements.txt               # Locked dependencies
├─ requirements-dev.txt           # Dev/test tooling (pytest, ruff, coverage, Flask-Testing)
├─ .github/
│  └─ workflows/
│     └─ ci.yml                   # GitHub Actions (lint + tests + optional deploy)
└─ README.md                      # This file
```

Features (current)
------------------

- Authentication and session handling (simple username/password)
- Plans
	- Create, view, modify, delete (leave) plans
	- Share a plan via hash ID (copy from modal)
	- Dashboard shows recent plans (cards, responsive grid)
- Expenses
	- Add, view, group by date (section header per day)
	- Split evenly or custom amounts per participant
	- Edit/delete expense; live recalculation in the form
- Reimbursements
	- Compute who owes whom using a greedy settle-up
	- “Mark as Paid” posts a reimbursement as an expense
- Statistics
	- Bar chart of participant balances (Chart.js)
	- Optional datasets for total vs real expenses
	- Reads labels/data from rendered HTML and builds the chart dynamically
- UI/UX
	- Bootstrap 5 responsive layout
	- Mobile-friendly navbar (toggler)
	- Cards and list groups for clean lists

Recent changes (security, exports, and refactors)
-----------------------------------------------

- Export improvements:
	- Added CSV and XLSX export endpoints for plans: `GET /plans/<hash_id>/export.csv` and `GET /plans/<hash_id>/export.xlsx`. Both exports include one column per plan participant	containing the participant's share for each expense. The XLSX exporter uses `openpyxl`.

- Security & sanitization:
	- Frontend sanitization now prefers a local `DOMPurify` copy served from
	`backend/static/js/dompurify.min.js` and `layout.html` includes that script directly.
	- Templates and scripts were refactored so inline scripts were moved to external JS files (e.g. `backend/static/js/app.js`, `plans_dashboard.js` `view_plan.js`) to better support a strict Content Security Policy (CSP).
	- `setContentFromHtml` and related helpers use `DOMPurify` when available and fall back to a safe sanitizer if not — reducing the app's XSS surface.

- CSP and CDN handling:
	- CSP headers are configurable via `backend/config.py` so you can allow required CDN hosts (Bootstrap, Chart.js, fonts) in non-strict deployments. For local-only setups `script-src 'self'` is sufficient because `dompurify.min.js` is served locally.

- Code organization / helpers:
	- Export builders were moved into `backend/routes/plans/helpers.py`:
		- `_build_plan_xlsx_stream(plan, expenses)` returns an in-memory XLSX BytesIO stream.
		- `build_plan_csv(plan, expenses)` returns CSV text matching the XLSX layout.
	- Keeping these builders in `helpers.py` makes them easier to test and reuse.


What’s implemented and what I learned
-------------------------------------

- Structured a Flask application with an app factory and blueprints (auth, plans)
- Session-based auth with a custom `@login_required` decorator
- SQLAlchemy model design with relationships (Plan ↔ Participants, Expenses ↔ Shares)
- Introduced Alembic/Flask-Migrate for evolving schema reliably (vs `db.create_all()`)
- Handled SQLite path pitfalls by using absolute `instance/` DB path and ensuring the directory exists
- Built responsive UI using Bootstrap (grid, cards, list groups, navbar toggler)
- Wrote modular JS to:
	- Load plan sections via fetch and inject HTML
	- Manage form logic (even split vs manual amounts, enabling/disabling inputs)
	- Avoid duplicate event listeners when reloading sections
	- Render charts with Chart.js from DOM-extracted data
- Jinja2 templates: grouping expenses by date, safe iteration over dicts (`.items()`), formatting dates
- Implement a CI/CD pipeline for automated testing and deployment

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


CI/CD (GitHub Actions + deployment)
-----------------------------------

This project is set up to run fast checks in CI and supports two deployment paths: Render (optional push-to-deploy) and PythonAnywhere (pull-based via a scheduled task).

Continuous Integration (CI)
---------------------------

Recommended CI stages:

- Lint: ruff
- Test: pytest (uses a temporary SQLite file DB via test fixtures)

Ruff configuration and PR‑based workflow
---------------------------------------

This project uses ruff for fast linting and formatting. Configuration is kept in `pyproject.toml` so both local tooling and CI use the same rules. The repository ships a `pyproject.toml` with `line-length = 100` to match our style guide.

Local checks vs CI checks
-------------------------

- Local pre-commit: Developers are encouraged to install `pre-commit` and enable hooks (the repo includes `.pre-commit-config.yaml`) so `ruff format` and `ruff check` run before commits. This improves developer feedback but is not a substitute for CI.
- CI on Pull Requests (recommended): The authoritative checks run in CI on pull requests. Open a PR and let the CI run linting and tests; require those checks to pass via branch protection before merging.

Example `pyproject.toml` snippet (already in the project):

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "C", "B"]
ignore = ["E203"]
exclude = ["migrations", "instance", "docs", ".venv", "backend/static"]
```

Example workflow file (create at `.github/workflows/ci.yml`):

```yaml
name: CI

on:
	push:
		branches: [ main ]
	pull_request:
		branches: [ main ]

jobs:
	build-and-test:
		runs-on: ubuntu-latest
		steps:
			- uses: actions/checkout@v4
			- uses: actions/setup-python@v5
				with:
					python-version: '3.11'
			- name: Install dependencies
				run: |
					python -m pip install --upgrade pip
					pip install -r requirements.txt
					pip install -r requirements-dev.txt
			- name: Lint (ruff)
				run: ruff check .
			- name: Tests (pytest)
				run: pytest -q
```

Notes:

- Dev dependencies are in `requirements-dev.txt` (ruff, pytest, coverage, Flask-Testing, pre-commit).
- Tests rely on `tests/conftest.py`, which creates a temporary SQLite database per test. No external DB needed in CI.

Recommended PR workflow
-----------------------

1. Create a feature branch and make your changes.
2. Run local checks:

```powershell
ruff format .
ruff check .
pre-commit run --all-files
pytest -q
```

3. Push your branch and open a pull request against `main`. The CI runs lint and tests on the PR. Configure GitHub branch protection to require the CI job (`CI / CD`) to pass before merging.

4. When the CI checks are green and reviews are complete, merge via the PR UI.

This approach prevents broken code from reaching `main` and keeps the main branch stable.

Optional: Deploy to Render
--------------------------

If you deploy on Render, use `start.sh` as the Start Command. It runs database migrations and then launches Gunicorn. In your Render service settings:

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


