from datetime import datetime, timezone
from backend.utils.user import delete_guest_user
from backend.models import User, Plan, Expense, db


def test_guest_login_creates_guest_and_sets_session(client):
    resp = client.get("/guestlogin", follow_redirects=True)
    assert resp.status_code == 200

    # Session should have username set
    with client.session_transaction() as sess:
        uname = sess.get("username")
        assert uname is not None
        assert uname.startswith("guest-")

    # User should exist in DB and be marked guest
    u = User.query.filter_by(username=uname).first()
    assert u is not None
    assert u.is_guest is True
    assert u.guest_expires_at is not None
    # DB may return naive datetimes even when code writes timezone-aware values
    expires = u.guest_expires_at
    if expires.tzinfo is None:
        # treat naive timestamps as UTC
        expires = expires.replace(tzinfo=timezone.utc)
    assert expires > datetime.now(timezone.utc)


def test_guest_logout_clears_session(client, guest_user_factory):
    guest_user_factory(username="guest-logout", expires_in_hours=1)
    with client.session_transaction() as sess:
        sess["username"] = "guest-logout"
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert "username" not in sess
    user = User.query.filter_by(username="guest-logout").first()
    assert user is None  # Guest user should be deleted


def test_change_password_guest_is_forbidden(client, guest_user_factory):
    # Create a guest user directly in DB
    guest_user_factory(username="guest-test", expires_in_hours=1)
    with client.session_transaction() as sess:
        sess["username"] = "guest-test"

    resp = client.post(
        "/change-password",
        data={"old_password": "guestpass", "new_password": "new", "confirm_password": "new"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Password should remain unchanged
    g = User.query.filter_by(username="guest-test").first()
    assert g is not None
    assert g.check_password("guestpass") is True


def test_delete_guest_user_function(plan_factory, expense_factory, guest_user_factory):
    guest = guest_user_factory(username="guest-to-delete", expires_in_hours=1)
    plan = plan_factory(owner=guest, name="GuestPlan", participants=["Alice", "Bob"])
    expense_factory(
        plan=plan, amount=100.0, description="GuestExpense", payer_name="guest-to-delete", shares={}
    )

    delete_guest_user(guest)

    g = db.session.get(User, guest.id)
    assert g is None
    p = db.session.get(Plan, plan.id)
    assert p is None
    e = Expense.query.filter_by(plan_id=plan.id).all()
    assert len(e) == 0
