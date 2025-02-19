from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from sqlalchemy import text

from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.blog import get_post
from flaskr.turnstile import cf_turnstile_required

bp = Blueprint("manage", __name__, url_prefix="/manage")


def is_admin() -> bool:
    if g.user["id"] == 1:
        return True
    return False


@bp.route("/")
@login_required
def index():
    if is_admin() is False:
        flash(f"You don't had permission to access {request.path}")
        return redirect(url_for("index"))
    try:
        db = get_db()
        posts = db.execute(
            text(
                "SELECT p.id, title, body, created, author_id, username "
                "FROM post p JOIN user u ON p.author_id = u.id "
                "ORDER BY created DESC"
            )
        ).fetchall()

        return render_template("manage/index.html", posts=posts)
    except Exception as e:
        flash(f"System error {e}")

    return redirect(url_for("manage.index"))


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
@cf_turnstile_required
def update(id):
    if is_admin() is False:
        flash("You don't had permission todo this operation")
        return redirect(url_for("index"))

    post = get_post(id, False)
    if post is None:
        return redirect(url_for("manage.index"))

    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")

        if not title:
            flash("Title is required.")
        else:
            try:
                db = get_db()
                db.execute(
                    text("UPDATE post SET title = :title, body = :body WHERE id = :id"),
                    {"title": title, "body": body, "id": id},
                )
                db.commit()
                return redirect(url_for("manage.index"))
            except Exception as e:
                flash(f"System error {e}")

    return render_template("manage/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
@cf_turnstile_required
def delete(id):
    if is_admin() is False:
        flash("You don't had permission todo this operation")
        return redirect(url_for("index"))

    post = get_post(id, False)
    if post is None:
        return redirect(url_for("manage.index"))

    try:
        db = get_db()
        db.execute(text("DELETE FROM post WHERE id = :id"), {"id": id})
        db.commit()
        return redirect(url_for("manage.index"))
    except Exception as e:
        flash(f"System error {e}")

    return redirect(url_for("manage.index"))
