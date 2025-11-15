import os
import tempfile
import pytest
from backend.app import create_app
from backend.models import db, User, Plan, PlanParticipant, Expense, ExpenseShare


@pytest.fixture(scope="function")
def app():
    # Temporary SQLite file DB (file avoids in-memory multi-connection issues)
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["FLASK_ENV"] = "testing"

    test_app = create_app()
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()
    try:
        os.remove(db_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


# Factories -------------------------------------------------


@pytest.fixture(scope="function")
def user_factory(app):
    created = []

    def _create(username="user", email=None, password="pass"):
        if email is None:
            email = f"{username}@test.local"

        u = User(username=username, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        created.append(u)
        return u

    return _create


@pytest.fixture(scope="function")
def plan_factory(app, user_factory):
    def _create(owner=None, name="Trip", participants=None):
        if owner is None:
            owner = user_factory("owner")
        if participants is None:
            participants = ["Alice", "Bob"]

        plan = Plan(name=name, hash_id="TESTHASH", created_by=owner.id)
        db.session.add(plan)
        db.session.flush()
        # owner as participant
        db.session.add(
            PlanParticipant(user_id=owner.id, plan_id=plan.id, role="owner", name=owner.username)
        )
        for p in participants:
            if isinstance(p, str):
                db.session.add(
                    PlanParticipant(user_id=None, plan_id=plan.id, role="member", name=p)
                )
            else:
                db.session.add(
                    PlanParticipant(user_id=p.id, plan_id=plan.id, role="member", name=p.username)
                )
        db.session.commit()
        return plan

    return _create


@pytest.fixture(scope="function")
def expense_factory(app, plan_factory):
    def _create(plan=None, description="Dinner", amount=60.0, payer_name="Alice", shares=None):
        if plan is None:
            plan = plan_factory()
        if shares is None:
            shares = {"Alice": 30.0, "Bob": 30.0}

        expense = Expense(
            description=description,
            amount=amount,
            payer_name=payer_name,
            plan_id=plan.id,
        )
        db.session.add(expense)
        db.session.flush()
        for name, share_amount in shares.items():
            db.session.add(ExpenseShare(expense_id=expense.id, name=name, amount=share_amount))
        db.session.commit()
        return expense

    return _create
