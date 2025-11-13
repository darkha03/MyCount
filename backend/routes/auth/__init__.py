from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from backend.models import db, User

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
    session.clear()  # remove all session data
    return redirect(url_for("auth.login"))
