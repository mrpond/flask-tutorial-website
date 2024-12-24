import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from pydapper import exceptions

bp = Blueprint('auth', __name__, url_prefix='/auth')
    
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        message = None

        if not username:
            message = 'Username is required.'
        elif not password:
            message = 'Password is required.'

        if message is None:
            try:
                db = get_db()
                user_id = get_db().execute_scalar(
                    'SELECT id FROM user WHERE username = ?username?', param={"username": username},
                )
                if user_id > 0:
                    message = f"User {username} is already registered."
                    
            except exceptions.NoResultException:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?username?, ?password?)",
                    param={"username": username, "password" : generate_password_hash(password)},
                )
                db.commit()
                flash(f"User registeration completed, you can now login with {username}")
                return redirect(url_for("auth.login"))
            except Exception as e:
                message = f"System error {e.args}"
                
        flash(message)
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        message = None
        try:
            user = get_db().query_single(
                'SELECT id, password FROM user WHERE username = ?username?', param={"username": username},
            )
            if user['id'] > 0 and check_password_hash(user['password'], password):
                session['id'] = user['id']
                session['username'] = username
                session.modified = True
                g.user = {
                    'id': user['id'],
                    'username': username
                }
                return redirect(url_for('index'))
            else:
                message = 'Incorrect username or password.'
        except exceptions.NoResultException:
            message = 'Incorrect username or password.'
        except Exception as e:
            message = f"System error {e.args}"

        flash(message)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('id')
    username = session.get('username')
    
    if user_id is None or username is None:
        g.user = None
    else:
        g.user = {
            'id': user_id,
            'username': username
        }
#    try:
#        g.user = get_db().execute_scalar(
#            'SELECT id FROM user WHERE id = ?user_id?', param={"user_id": user_id},
#        )
#    except Exception as e:
#        session.clear()
#        g.user = None
            
@bp.route('/logout')
def logout():
    session.clear()
    g.user = None
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view