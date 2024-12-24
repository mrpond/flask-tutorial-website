from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

from pydapper import exceptions

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    posts = get_db().query(
        'SELECT p.id, title, body, created, author_id, username '
        'FROM post p JOIN user u ON p.author_id = u.id '
        'ORDER BY created DESC'
    )
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not title:
            flash('Title is required.')
        else:
            try:
                db = get_db()
                db.execute(
                    'INSERT INTO post (title, body, author_id) VALUES (?title?, ?body?, ?author_id?)',
                    param={'title': title, 'body': body, 'author_id': g.user['id']},
                )
                db.commit()
                return redirect(url_for('blog.index'))
            except Exception as e:
                flash(f"System error {e.args}")
                
    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = None
    try:
        post = get_db().query_single(
            'SELECT p.id, title, body, created, author_id, username '
            'FROM post p JOIN user u ON p.author_id = u.id '
            'WHERE p.id = ?id?',
            param={'id': id},
        )
    except exceptions.NoResultException:
        flash(f"Post id {id} doesn't exist.")
    except Exception as e:
        flash(f"System error {e.args}")
    
    if post is not None and check_author:
        if post['author_id'] != g.user['id']:
            flash(f"You don't had permission to edit this post")
            post = None
        
    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if post is None:
        return redirect(url_for('blog.index'))
    
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not title:
            flash('Title is required.')
        else:
            try:
                db = get_db()
                db.execute(
                    'UPDATE post SET title = ?title?, body = ?body? WHERE id = ?id?',
                    param={'title': title, 'body': body, 'id': id},
                )
                db.commit()
                return redirect(url_for('blog.index'))
            except Exception as e:
                flash(f"System error {e.args}")
                
    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    if post is None:
        return redirect(url_for('blog.index'))
    
    try:
        db = get_db()
        db.execute(
            'DELETE FROM post WHERE id = ?id?', 
            param={'id': id},
        )
        db.commit()
    except Exception as e:
        flash(f"System error {e.args}")
    return redirect(url_for('blog.index'))