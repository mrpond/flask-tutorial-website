import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from sqlalchemy import text

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        message = None

        if not username:
            message = "Username is required."
        elif not password:
            message = "Password is required."

        if message is None:
            db = get_db()
            try:
                result = db.execute(
                    text("SELECT id FROM user WHERE username = :username"),
                    {"username": username},
                ).scalar_one_or_none()
                if result is not None:
                    message = f"User {username} is already registered."
                else:
                    db.execute(
                        text(
                            "INSERT INTO user (username, password) VALUES (:username, :password)"
                        ),
                        {
                            "username": username,
                            "password": generate_password_hash(password),
                        },
                    )
                    db.commit()
                    flash(
                        f"User registration completed, you can now login with {username}"
                    )
                    return redirect(url_for("auth.login"))
            except Exception as e:
                message = f"System error {e}"

        flash(message)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        message = "Incorrect username or password."
        try:
            result = (
                get_db()
                .execute(
                    text("SELECT id, password FROM user WHERE username = :username"),
                    {"username": username},
                )
                .fetchone()
            )
            if result is not None:
                if result.id > 0 and check_password_hash(result.password, password):
                    session.clear()
                    session["id"] = result.id
                    session["username"] = username
                    return redirect(url_for("index"))
                pass
        except Exception as e:
            message = f"System error {e}"

        flash(message)

    return render_template("auth/login.html")


def verify_user(user_id, username):
    if user_id is not None and username is not None:
        try:
            result = (
                get_db()
                .execute(
                    text("SELECT username FROM user WHERE id = :user_id"),
                    {"user_id": user_id},
                )
                .scalar_one_or_none()
            )
            if result is not None and result == username:
                return True
        except Exception:
            pass

    return False


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("id")
    username = session.get("username")
    if verify_user(user_id, username) is True:
        g.user = {"id": user_id, "username": username}
    else:
        g.user = None


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Login required")
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("index"))
