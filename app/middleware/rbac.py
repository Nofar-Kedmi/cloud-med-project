from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def _dashboard_for_role(role: str) -> str:
    role = (role or "").strip().lower()
    if role == "admin":
        return url_for("admin.patients_list")
    if role == "doctor":
        return url_for("doctor.dashboard")
    if role == "pharmacist":
        return url_for("pharmacist.search")
    return url_for("auth.welcome")


def role_required(*roles):
    allowed_roles = {role.strip().lower() for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            user_role = (current_user.role or "").strip().lower()
            if user_role not in allowed_roles:
                flash(
                    f"Access denied. This area is for {', '.join(sorted(allowed_roles))} "
                    f"accounts only (you are signed in as {current_user.role}).",
                    "warning",
                )
                return redirect(_dashboard_for_role(user_role))

            return view_func(*args, **kwargs)

        return wrapped

    return decorator
