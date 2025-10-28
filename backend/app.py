from flask import Flask, jsonify, render_template, session
from flask_cors import CORS
from backend.routes.plans import plans_bp
from backend.routes.auth import auth_bp
from backend.models import db, User, Plan, PlanParticipant, Expense
from backend.utils.auth import login_required
from flask_migrate import Migrate
from sqlalchemy.engine.url import make_url
from pathlib import Path

# Initialize Flask-Migrate (database migrations)
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('backend.config.Config')
    db.init_app(app)
    # Wire migrations to the app and SQLAlchemy
    with app.app_context():
        # Ensure the SQLite directory exists if using sqlite
        db_url = make_url(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
        if db_url.drivername == 'sqlite' and db_url.database:
            Path(db_url.database).parent.mkdir(parents=True, exist_ok=True)
        print(f"DB URL: {db.engine.url}")
    migrate.init_app(app, db)
    app.secret_key = "your-very-secret-key"
    CORS(app)
    # Note: Rely on Flask-Migrate for schema changes (flask db init/migrate/upgrade)
    # Avoid db.create_all() in production as it won't apply schema changes to existing tables.
    app.register_blueprint(plans_bp)    
    app.register_blueprint(auth_bp)
    return app

app = create_app()

expenses = [
    {
        "id": 1,
        "description": "Lunch",
        "amount": 120.0,
        "payer": "Alice",
        "participants": ["Alice", "Bob", "Charlie"]
    },
    {
        "id": 2,
        "description": "Taxi",
        "amount": 60.0,
        "payer": "Bob",
        "participants": ["Bob", "Charlie"]
    }
]

reimbursements = [
    {
        "from": "Charlie",
        "to": "Alice",
        "amount": 40.0
    },
    {
        "from": "Charlie",
        "to": "Bob",
        "amount": 20.0
    }
]


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/expenses")
@login_required
def get_expenses():
    return jsonify(expenses)

@app.route("/api/reimbursements")
@login_required
def get_reimbursements():
    return jsonify(reimbursements)

if __name__ == "__main__":
    app.run(debug=True)
