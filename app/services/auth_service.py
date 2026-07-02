from flask_login import login_user, logout_user

from app.models.user import User


class AuthenticationError(Exception):
    pass


def authenticate(email: str, password: str):
    user = User.find_by_email(email)
    if user is None or not user.check_password(password):
        return None
    return user


def login(user: User, remember: bool = False):
    login_user(user, remember=remember)


def logout():
    logout_user()
