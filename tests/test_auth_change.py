from backend.models import User


def test_change_password_success(client, user_factory):
    # Create a normal user and login via session
    user_factory("alice", email="alice@test.local", password="oldpass")
    with client.session_transaction() as sess:
        sess["username"] = "alice"

    resp = client.post(
        "/change-password",
        data={"old_password": "oldpass", "new_password": "newpass", "confirm_password": "newpass"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    u = User.query.filter_by(username="alice").first()
    assert u is not None
    assert u.check_password("newpass") is True


def test_profile_update_success_and_session_change(client, user_factory):
    user_factory("bob", email="bob@test.local", password="pw")
    with client.session_transaction() as sess:
        sess["username"] = "bob"

    resp = client.post(
        "/profile/update",
        data={"username": "bobby", "email": "bobby@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    u = User.query.filter_by(username="bobby").first()
    assert u is not None
    assert u.email == "bobby@example.com"

    # Session should reflect new username
    with client.session_transaction() as sess:
        assert sess.get("username") == "bobby"


def test_profile_update_uniqueness_validation(client, user_factory):
    # Create target and another user
    user_factory("sam", email="sam@test.local", password="pw")
    user_factory("taken", email="taken@example.com", password="pw2")

    with client.session_transaction() as sess:
        sess["username"] = "sam"

    # Attempt to change to an already-taken username
    resp = client.post(
        "/profile/update",
        data={"username": "taken", "email": "sam_new@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Sam should remain unchanged
    s = User.query.filter_by(email="sam@test.local").first()
    assert s is not None
    assert s.username == "sam"
