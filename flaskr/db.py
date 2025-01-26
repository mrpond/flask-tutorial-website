import pydapper
import sqlite3
import mariadb
import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_type = current_app.config.get("DB_TYPE", "sqlite")  # Default to SQLite
        match db_type:
            case "sqlite":
                # Initialize SQLite connection
                g.db = pydapper.using(
                    sqlite3.connect(current_app.config["SQLITE_PATH"])
                )
            case "mariadb":
                # Initialize MariaDB connection
                g.db = pydapper.using(mariadb.connect(**current_app.config["DATABASE"]))
            case _:
                # Handle unsupported database types
                raise ValueError(f"Unsupported DB_TYPE: {db_type}")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        if hasattr(db, "close"):
            db.close()
        else:
            current_app.logger.warning("Attempted to close a non-closable db object.")


def executescript(schema_sql):
    db = get_db()
    sql_command = schema_sql.split(";")
    for statement in sql_command:
        # Strip any whitespace or newlines at the end
        statement = statement.strip()
        if statement:  # Avoid executing empty statements
            try:
                db.execute(statement)
            except Exception as e:
                # Log the error or handle it appropriately
                print(f"Error executing SQL statement: {statement}\nError: {e}")
    db.commit()


def init_db():
    db_type = current_app.config.get("DB_TYPE", "sqlite")  # Default to SQLite
    sql_file = None
    match db_type:
        case "sqlite":
            sql_file = "schema_sqlite.sql"
        case "mariadb":
            sql_file = "schema_mariadb.sql"
        case _:
            # Handle unsupported database types
            raise ValueError(f"Unsupported DB_TYPE: {db_type}")
    with current_app.open_resource(sql_file) as f:
        schema_sql = f.read().decode("utf8")
        executescript(schema_sql)


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
