from flask import Flask, jsonify, render_template, session, redirect
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
from flask_migrate import Migrate
from sqlalchemy.engine.url import make_url
from pathlib import Path
from datetime import timezone

# Initialize Flask-Migrate (database migrations)
migrate = Migrate()


def index():
    username = session.get("username")
    if not username:
        return redirect("/home")
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


def landing():
    if session.get("username"):
        return redirect("/")
    return render_template("landing.html", show_header=False)


def create_app():
    # Keep create_app small and delegate initialization to helpers
    app = Flask(__name__)
    app.config.from_object("backend.config.Config")

    _init_extensions(app)
    _register_blueprints(app)
    _register_context_processors(app)
    _configure_csp(app)

    # Register top-level views
    app.add_url_rule("/", "index", index)
    app.add_url_rule("/home", "landing", landing)
    app.add_url_rule("/landing", "landing_alias", landing)

    return app


def _init_extensions(app: Flask):
    """Initialize extensions and ensure DB path for sqlite."""
    db.init_app(app)
    # Wire migrations to the app and SQLAlchemy and ensure sqlite dir
    with app.app_context():
        db_url = make_url(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
        if db_url.drivername == "sqlite" and db_url.database:
            Path(db_url.database).parent.mkdir(parents=True, exist_ok=True)
        if app.debug or os.environ.get("PRINT_DB_URL"):
            try:
                print(f"DB URL: {db.engine.url}")
            except Exception:
                pass
    migrate.init_app(app, db)
    app.secret_key = app.config.get("SECRET_KEY")
    CORS(app)


def _register_blueprints(app: Flask):
    app.register_blueprint(plans_bp)
    app.register_blueprint(auth_bp)


def _register_context_processors(app: Flask):
    @app.context_processor
    def inject_current_user():
        # Provide minimal current user info to templates to support UI (guest timer)
        username = session.get("username")
        if not username:
            return {}
        user = None
        try:
            user = User.query.filter_by(username=username).first()
        except Exception:
            return {}
        if not user:
            return {}
        info = {
            "username": user.username,
            "is_guest": bool(getattr(user, "is_guest", False)),
            "guest_expires_at": None,
        }
        if info["is_guest"] and getattr(user, "guest_expires_at", None):
            exp = user.guest_expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            info["guest_expires_at"] = exp.astimezone(timezone.utc).isoformat()
        return {"current_user_info": info}


def _configure_csp(app: Flask):
    @app.after_request
    def _apply_csp(response):
        # Build Content-Security-Policy from config lists. These defaults allow
        # popular CDNs (jsdelivr, cdnjs, unpkg). For production, tighten or
        # override in `backend.config.Config`.
        cfg = app.config

        def join_list(key, default):
            vals = cfg.get(key, default) or default
            # allow specifying comma-separated string in env if desired
            if isinstance(vals, str):
                vals = [v.strip() for v in vals.split(",") if v.strip()]
            return " ".join(vals)

        default_src = join_list("CSP_DEFAULT_SRC", ["'self'"])
        script_src = join_list("CSP_SCRIPT_SRC", ["'self'"])
        style_src = join_list("CSP_STYLE_SRC", ["'self'"])
        img_src = join_list("CSP_IMG_SRC", ["'self'", "data:"])
        font_src = join_list("CSP_FONT_SRC", ["'self'", "data:"])
        connect_src = join_list("CSP_CONNECT_SRC", ["'self'"])

        policy = (
            f"default-src {default_src}; "
            f"script-src {script_src}; "
            f"style-src {style_src}; "
            f"font-src {font_src}; "
            f"img-src {img_src}; "
            f"connect-src {connect_src}; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = policy
        return response


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
