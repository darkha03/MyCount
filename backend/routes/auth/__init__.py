from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from backend.models import db, User
from datetime import datetime, timedelta, timezone
import secrets
from backend.utils.auth import login_required
from backend.utils.user import delete_guest_user

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            flash("Username is required", "error")
            return redirect(url_for("auth.login"))
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))

        if user.check_password(password):
            session["username"] = username
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        if not username:
            flash("Username is required", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(username=username).first():
            flash("Username already taken", "error")
            return redirect(url_for("auth.register"))
        email = request.form["email"]
        if not email:
            flash("Email is required", "error")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return redirect(url_for("auth.register"))
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    username = session.get("username")
    user = None
    if username:
        user = User.query.filter_by(username=username).first()
    # Perform guest cleanup before clearing session
    if user and user.is_guest:
        delete_guest_user(user)
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/guestlogin", methods=["GET"])
def guestlogin():
    # Prune expired guest users first
    now = datetime.now(timezone.utc)
    expired_guests = User.query.filter(User.is_guest.is_(True), User.guest_expires_at < now).all()
    for g in expired_guests:
        delete_guest_user(g)
    if expired_guests:
        db.session.commit()

    active_guest_count = User.query.filter(
        User.is_guest.is_(True), User.guest_expires_at > now
    ).count()
    if active_guest_count >= 10:
        flash("Guest capacity reached (10 active). Try again later.", "danger")
        return redirect(url_for("auth.login"))

    # Generate unique guest username
    for _ in range(5):  # few attempts
        noun = secrets.token_hex(3)
        candidate = f"guest-{noun}"
        if not User.query.filter_by(username=candidate).first():
            username_val = candidate
            break
    else:
        flash("Could not allocate guest username", "danger")
        return redirect(url_for("auth.login"))

    guest = User(
        username=username_val,
        email=f"{username_val}@example.invalid",
        is_guest=True,
        guest_expires_at=now + timedelta(hours=2),
    )
    # Set a random password so auth methods remain consistent
    guest.set_password(secrets.token_urlsafe(16))
    db.session.add(guest)
    db.session.commit()
    session["username"] = guest.username
    flash("Guest login successful. Account expires in 2 hours.", "success")
    return redirect(url_for("index"))


@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    return render_template("profile.html", user=user)


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def profile_update():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()

    new_username = (request.form.get("username") or "").strip()
    new_email = (request.form.get("email") or "").strip()
    if not new_username or not new_email:
        flash("Username and email are required", "danger")
        return redirect(url_for("auth.profile"))

    # check uniqueness
    if new_username != user.username and User.query.filter_by(username=new_username).first():
        flash("Username already taken", "danger")
        return redirect(url_for("auth.profile"))
    if new_email != user.email and User.query.filter_by(email=new_email).first():
        flash("Email already registered", "danger")
        return redirect(url_for("auth.profile"))

    user.username = new_username
    user.email = new_email
    db.session.commit()
    # update session username if changed
    session["username"] = new_username
    flash("Profile updated", "success")
    return redirect(url_for("auth.profile"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
    if user.is_guest:
        flash("Guest users cannot change password", "danger")
        return redirect(url_for("auth.profile"))

    if request.method == "GET":
        # redirect to profile and instruct it to open the password modal
        return redirect(url_for("auth.profile", open="password"))

    # POST: perform password change
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")
    if not old_password or not new_password or not confirm_password:
        flash("All password fields are required", "danger")
        return redirect(url_for("auth.profile"))
    if new_password != confirm_password:
        flash("New passwords do not match", "danger")
        return redirect(url_for("auth.profile"))
    if not user.check_password(old_password):
        flash("Current password is incorrect", "danger")
        return redirect(url_for("auth.profile"))

    user.set_password(new_password)
    db.session.commit()
    flash("Password changed successfully", "success")
    return redirect(url_for("auth.profile"))
