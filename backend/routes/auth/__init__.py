from flask import Blueprint

auth_bp = Blueprint("auth", __name__, template_folder="templates")

from flask import render_template, request, redirect, url_for, session, flash

# Fake user DB for now
USERS = {
    "admin@example.com": {"password": "admin123"}  # Password should be hashed later
}

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":    
        email = request.form.get("email")
        password = request.form.get("password")

        user = USERS.get(email)
        if user and user["password"] == password:
            session["user_email"] = email
            flash("Logged in successfully!", "success")
            return redirect(url_for("plans.get_plans"))

        flash("Invalid credentials", "danger")

    return render_template("auth/login.html")