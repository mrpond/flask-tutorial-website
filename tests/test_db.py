import sqlite3
import pytest
import mariadb
from flaskr.db import get_db, g


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()
    db_type = app.config.get("DB_TYPE", "sqlite")  # Default to SQLite
    match db_type:
        case "sqlite":
            with pytest.raises(sqlite3.ProgrammingError) as e:
                db.execute_scalar("SELECT 1")
                assert "closed" in str(e.value)
        case "mariadb":
            with pytest.raises(mariadb.ProgrammingError) as e:
                db.execute_scalar("SELECT 1")
                assert "not connected" in str(e.value)


def test_init_db_command(runner, monkeypatch):
    class Recorder(object):
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr("flaskr.db.init_db", fake_init_db)
    result = runner.invoke(args=["init-db"])
    assert "Initialized" in result.output
    assert Recorder.called
