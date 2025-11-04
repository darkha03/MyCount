from flask import Flask, jsonify, render_template, session
from flask_cors import CORS
from backend.routes.plans import plans_bp, calculate_balance, calculate_reimbursements, get_plan_expenses_api
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
    
    @app.route("/")
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
            if plan:
                participant = PlanParticipant.query.filter_by(plan_id=plan.id).all()
                expenses = Expense.query.filter_by(plan_id=plan.id).all()
                user_plans.append({
                    "id": plan.id,
                    "name": plan.name,
                    "hash_id": plan.hash_id,
                    "created_at": plan.created_at.isoformat(),
                    "participants": [p.name for p in participant],
                    "total_expenses": sum(e.amount for e in expenses if e.description != "Reimbursement")
                })
            # Limit to 4 most recent plans
            user_plans = sorted(user_plans, key=lambda p: p["created_at"], reverse=True)[:4]  
            # Calculate reimbursements for this plan
            expenses = get_plan_expenses_api(participation.plan.hash_id).get_json()
            balances = calculate_balance(expenses)
            reimbursements = calculate_reimbursements(balances)
            for r in reimbursements:
                r["plan_hash_id"] = participation.plan.hash_id
                if r["from"] == participation.name:
                    r["from"] = "You (" + r["from"] + ")"
                    user_reimbursements.append(r)
                elif r["to"] == participation.name:
                    r["to"] = "You (" + r["to"] + ")"
                    user_reimbursements.append(r) 
        return render_template("index.html", plans=user_plans, reimbursments=user_reimbursements)
    return app

app = create_app()



if __name__ == "__main__":
    app.run(debug=True)
