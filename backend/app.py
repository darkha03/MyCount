from flask import Flask, jsonify, render_template, session
import os
from flask_cors import CORS
from backend.routes.plans import (
    plans_bp,
    calculate_balance,
    calculate_reimbursements,
    get_plan_expenses_api,
)
from backend.routes.auth import auth_bp
from backend.models import db, User, Plan, PlanParticipant, Expense
from backend.utils.auth import login_required
from flask_migrate import Migrate
from sqlalchemy.engine.url import make_url
from pathlib import Path

# Initialize Flask-Migrate (database migrations)
migrate = Migrate()


@login_required
def index():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user_plans = []
    user_reimbursements = []
    for participation in user.participations:
        plan = Plan.query.filter_by(id=participation.plan_id).first()
        if not plan:
            continue
        participant_rows = PlanParticipant.query.filter_by(plan_id=plan.id).all()
        expenses_rows = Expense.query.filter_by(plan_id=plan.id).all()
        user_plans.append(
            {
                "id": plan.id,
                "name": plan.name,
                "hash_id": plan.hash_id,
                "created_at": plan.created_at.isoformat(),
                "participants": [p.name for p in participant_rows],
                "total_expenses": sum(
                    e.amount for e in expenses_rows if e.description != "Reimbursement"
                ),
            }
        )
        # Calculate reimbursements for this plan
        expenses_json = get_plan_expenses_api(participation.plan.hash_id).get_json()
        balances = calculate_balance(expenses_json)
        reimbursements = calculate_reimbursements(balances)
        for r in reimbursements:
            r["plan_hash_id"] = participation.plan.hash_id
            if r["from"] == participation.name:
                r["from"] = f"You ({r['from']})"
                user_reimbursements.append(r)
            elif r["to"] == participation.name:
                r["to"] = f"You ({r['to']})"
                user_reimbursements.append(r)
    # Limit after collecting all plans
    user_plans = sorted(user_plans, key=lambda p: p["created_at"], reverse=True)[:4]
    return render_template("index.html", plans=user_plans, reimbursments=user_reimbursements)


def create_app():
    app = Flask(__name__)
    app.config.from_object("backend.config.Config")
    db.init_app(app)
    # Wire migrations to the app and SQLAlchemy
    with app.app_context():
        # Ensure the SQLite directory exists if using sqlite
        db_url = make_url(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
        if db_url.drivername == "sqlite" and db_url.database:
            Path(db_url.database).parent.mkdir(parents=True, exist_ok=True)
        # Only print DB URL when debugging or explicitly requested
        if app.debug or os.environ.get("PRINT_DB_URL"):
            print(f"DB URL: {db.engine.url}")
    migrate.init_app(app, db)
    app.secret_key = app.config["SECRET_KEY"]
    CORS(app)
    app.register_blueprint(plans_bp)
    app.register_blueprint(auth_bp)

    @app.after_request
    def _apply_csp(response):
        # Strict CSP allowing only same-origin resources and scripts
        policy = (
            "default-src 'self'; "
            "script-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = policy
        return response

    # Register top-level views
    app.add_url_rule("/", "index", index)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
