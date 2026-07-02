from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user

from app.services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_for_role(current_user.role))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = auth_service.authenticate(email, password)
        if user is None:
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        auth_service.login(user, remember=request.form.get("remember") == "on")
        flash(f"Welcome, {user.full_name}.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(_dashboard_for_role(user.role))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    auth_service.logout()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


def _dashboard_for_role(role: str) -> str:
    if role == "admin":
        return url_for("admin.patients_list")
    if role == "doctor":
        return url_for("doctor.dashboard")
    if role == "pharmacist":
        return url_for("pharmacist.search")
    return url_for("auth.welcome")


@auth_bp.route("/welcome")
@login_required
def welcome():
    if current_user.role == "admin":
        return redirect(url_for("admin.patients_list"))
    if current_user.role == "doctor":
        return redirect(url_for("doctor.dashboard"))
    if current_user.role == "pharmacist":
        return redirect(url_for("pharmacist.search"))
    return render_template("auth/welcome.html")
