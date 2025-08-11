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

        flash("Invalid email or password", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("auth.register"))
        if email in USERS:
            flash("Email already registered", "error")
            return redirect(url_for("auth.register"))
        USERS[email] = {"password": password}  # In a real app, hash the password here
        #hashed_password = generate_password_hash(password)
        #db = get_db()
        #db.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        #db.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()  # remove all session data
    return redirect(url_for("auth.login"))
    