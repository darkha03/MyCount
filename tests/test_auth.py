from backend.models import User


def test_register_and_login_flow(client):
    # Register
    resp = client.post(
        "/register",
        data={
            "username": "steve",
            "email": "steve@example.com",
            "password": "secret",
            "confirm_password": "secret",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Ensure user created and password hashed
    u = User.query.filter_by(username="steve").first()
    assert u is not None
    assert u.password_hash != "secret"

    # Login
    resp = client.post(
        "/login",
        data={
            "username": "steve",
            "password": "secret",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    # Session should be set
    with client.session_transaction() as sess:
        assert sess.get("username") == "steve"


def test_login_wrong_password(client, user_factory):
    user_factory("john", email="john@example.com", password="right")

    client.post(
        "/login",
        data={
            "username": "john",
            "password": "wrong",
        },
        follow_redirects=True,
    )

    # Should not create a session for wrong password
    with client.session_transaction() as sess:
        assert sess.get("username") is None
