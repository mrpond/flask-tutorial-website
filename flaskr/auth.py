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
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        message = None

        if not username or not password:
            message = "Username and password is required."

        if message is None:
            try:
                db = get_db()
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
        return redirect(url_for("auth.register"))

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        message = None

        if not username or not password:
            message = "Username and password is required."

        if message is None:
            try:
                db = get_db()
                result = db.execute(
                    text("SELECT id, password FROM user WHERE username = :username"),
                    {"username": username},
                ).fetchone()
                if result is not None:
                    if result.id > 0 and check_password_hash(result.password, password):
                        session.clear()
                        session["id"] = result.id
                        session["username"] = username
                        return redirect(url_for("index"))
                    else:
                        pass
                message = "Incorrect username or password."
            except Exception as e:
                message = f"System error {e}"

        flash(message)
        return redirect(url_for("auth.login"))

    return render_template("auth/login.html")


def verify_user(user_id, username):
    if user_id is not None and username is not None:
        try:
            db = get_db()
            result = db.execute(
                text("SELECT username FROM user WHERE id = :user_id"),
                {"user_id": user_id},
            ).scalar_one_or_none()
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


@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("auth/dashboard.html")


@bp.route("/change_password", methods=("GET", "POST"))
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_new_password = request.form.get("confirm_new_password")
        message = None

        if not current_password:
            message = "Current password is required."
        elif not new_password:
            message = "New password is required."
        elif not confirm_new_password:
            message = "Confirm new password is required."
        elif new_password != confirm_new_password:
            message = "New passwords do not match."
        elif current_password == new_password:
            message = "New passwords is the same as current password."

        if message is None:
            db = get_db()
            try:
                result = db.execute(
                    text("SELECT password FROM user WHERE id = :id"),
                    {"id": g.user["id"]},
                ).scalar_one_or_none()
                if result is not None:
                    if check_password_hash(result, current_password):
                        db.execute(
                            text(
                                "UPDATE user SET password = :new_password WHERE id = :id"
                            ),
                            {
                                "id": g.user["id"],
                                "new_password": generate_password_hash(new_password),
                            },
                        )
                        db.commit()
                        g.user = None
                        session.clear()
                        flash(
                            "Password change completed, you can now login with new password."
                        )
                        return redirect(url_for("auth.login"))
                    else:
                        message = "Current password is incorrect."
                        pass
                else:
                    message = "Unexpected error"
            except Exception as e:
                message = f"System error {e}"

        flash(message)
        return redirect(url_for("auth.change_password"))

    return render_template("auth/change_password.html")
