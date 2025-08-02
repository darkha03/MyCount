from flask import session, redirect, url_for

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated