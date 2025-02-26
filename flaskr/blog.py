from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from sqlalchemy import text

from flaskr.auth import login_required
from flaskr.db import get_db
from .flask_cf_turnstile import cf_turnstile_required

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    try:
        db = get_db()
        posts = db.execute(
            text(
                "SELECT p.id, title, body, created, author_id, username "
                "FROM post p JOIN user u ON p.author_id = u.id "
                "ORDER BY created DESC"
            )
        ).fetchall()

        return render_template("blog/index.html", posts=posts)
    except Exception as e:
        flash(f"System error {e}")

    return redirect(url_for("blog.index"))


@bp.route("/create", methods=("GET", "POST"))
@login_required
@cf_turnstile_required()
def create():
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")

        if not title:
            flash("Title is required.")
        else:
            try:
                db = get_db()
                db.execute(
                    text(
                        "INSERT INTO post (title, body, author_id) VALUES (:title, :body, :author_id)"
                    ),
                    {"title": title, "body": body, "author_id": g.user["id"]},
                )
                db.commit()
                return redirect(url_for("blog.index"))
            except Exception as e:
                flash(f"System error {e}")

    return render_template("blog/create.html")


def get_post(id, check_author=True):
    error = None
    post = None
    try:
        db = get_db()
        post = db.execute(
            text(
                "SELECT p.id, title, body, created, author_id, username "
                "FROM post p JOIN user u ON p.author_id = u.id "
                "WHERE p.id = :id"
            ),
            {"id": id},
        ).fetchone()
    except Exception as e:
        flash(f"System error {e}")
        return None

    if post is not None:
        if check_author and post.author_id != g.user["id"]:
            error = f"You don't had permission to modify this post id {id}"
            post = None
    else:
        error = f"Post id {id} doesn't exist."

    if error is not None:
        flash(error)

    return post


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
@cf_turnstile_required()
def update(id):
    post = get_post(id)
    if post is None:
        return redirect(url_for("blog.index"))

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
                return redirect(url_for("blog.index"))
            except Exception as e:
                flash(f"System error {e}")

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
@cf_turnstile_required()
def delete(id):
    post = get_post(id)
    if post is None:
        return redirect(url_for("blog.index"))

    try:
        db = get_db()
        db.execute(text("DELETE FROM post WHERE id = :id"), {"id": id})
        db.commit()
    except Exception as e:
        flash(f"System error {e}")

    return redirect(url_for("blog.index"))
