import pytest
from sqlalchemy import text

from flaskr.db import get_db


def test_index(client, auth):
    response = client.get("/")
    assert b"Log In" in response.data
    assert b"Register" in response.data

    auth.login()
    response = client.get("/")
    assert b"Log Out" in response.data
    assert b"test title" in response.data
    assert b"by test on 2018-01-01" in response.data
    assert b"test\nbody" in response.data
    assert b'href="/1/update"' in response.data


@pytest.mark.parametrize(
    "path",
    (
        "/create",
        "/1/update",
        "/1/delete",
    ),
)
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute(
            text("UPDATE post SET author_id = :author_id WHERE id = :id"),
            {"author_id": 2, "id": 1},
        )
        db.commit()
    auth.login()

    # current user can't modify other user's post
    # assert client.post('/1/update').status_code == 403
    # assert client.post('/1/delete').status_code == 403
    message = b"You don&#39;t had permission to modify this post id 1"
    response = client.post(
        "/1/update",
        data={"title": "update", "body": ""},
        follow_redirects=True,
    )
    assert message in response.data

    response = client.post(
        "/1/delete",
        follow_redirects=True,
    )
    assert message in response.data

    # current user doesn't see edit link
    assert b'href="/1/update"' not in client.get("/").data


@pytest.mark.parametrize(
    "path",
    (
        "/2/update",
        "/2/delete",
    ),
)
def test_exists_required(client, auth, path):
    auth.login()
    response = client.post(
        path,
        follow_redirects=True,
    )
    message = b"Post id 2 doesn&#39;t exist."
    assert message in response.data


def test_create(client, auth, app):
    auth.login()
    assert client.get("/create").status_code == 200
    client.post(
        "/create",
        data={"title": "created", "body": ""},
    )

    with app.app_context():
        db = get_db()
        count = db.execute(
            text("SELECT COUNT(id) FROM post"),
        ).scalar_one_or_none()
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get("/1/update").status_code == 200
    client.post(
        "/1/update",
        data={"title": "updated", "body": ""},
    )

    with app.app_context():
        post = (
            get_db()
            .execute(
                text("SELECT * FROM post WHERE id = :id"),
                {"id": 1},
            )
            .fetchone()
        )
        assert post.title == "updated"


@pytest.mark.parametrize(
    "path",
    (
        "/create",
        "/1/update",
    ),
)
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(
        path,
        data={"title": "", "body": ""},
    )
    assert b"Title is required." in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post(
        "/1/delete",
    )
    assert response.headers["Location"] == "/"

    with app.app_context():
        no_result = None
        db = get_db()
        no_result = db.execute(
            text("SELECT * FROM post WHERE id = :id"),
            {"id": 1},
        ).fetchone()
        assert no_result is None
