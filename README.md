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
├─ requirements.txt               # Locked dependencies
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

Troubleshooting
---------------

- “No such command 'db'”
	- Ensure `Flask-Migrate` is installed and `Migrate(app, db)` (or `migrate.init_app`) is called in `create_app()`
- `ModuleNotFoundError: No module named 'backend'`
	- Run via Flask CLI or module mode: `set FLASK_APP=backend.app:create_app && flask run` (or `python -m backend.app`)
- SQLite path mismatch
	- Config uses an absolute path under `instance/`. Verify the printed `DB URL:` on startup
- Migration warnings about FKs on SQLite
	- SQLite is limited with altering FKs; warnings are expected in dev. Use Postgres in production
- Chart not rendering
	- Ensure Chart.js is loaded before your page JS and call the render function after injecting the HTML

Security notes
--------------

- Never commit real secrets. Set `SECRET_KEY` and DB URLs via environment variables in production
- Avoid hardcoding credentials in JS/HTML

Roadmap
-------

- Proper user registration and password reset
- Invite flows and role-based permissions per plan
- Better reimbursement recording and history
- Export/Import (CSV)
- Test suite and CI

Screenshots / Demo (placeholders)
---------------------------------

- Live demo: https://example.com (coming soon)
- Screenshots: 


![Dashboard](docs/dashboard.jpg)
![Plan Details](docs/plan.jpg)
![Expenses Section](docs/expense.jpg)
![Create Expense](docs/create-expense.jpg)
![Reimbursement Section](docs/reimbursement.jpg)
![Statistic Section](docs/statistic.jpg)


License
-------


