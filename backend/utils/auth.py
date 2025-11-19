from flask import session, redirect, url_for, flash
from backend.utils.user import delete_guest_user
from backend.models import User
from datetime import datetime, timezone


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        username = session.get("username")
        if not username:
            return redirect(url_for("auth.login"))
        user = User.query.filter_by(username=username).first()
        if not user:
            session.pop("username", None)
            return redirect(url_for("auth.login"))

        # Normalize and compare datetimes safely (handle naive and aware datetimes)
        def guest_expired(u: User) -> bool:
            exp = u.guest_expires_at
            if not exp:
                return False
            now = datetime.now(timezone.utc)
            # If stored datetime is naive, treat it as UTC
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            return exp <= now

        if user.is_guest and guest_expired(user):
            delete_guest_user(user)
            session.pop("username", None)
            flash("Guest session has expired", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated
