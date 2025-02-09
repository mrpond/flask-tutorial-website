import click
from flask import current_app, g
from sqlalchemy import Connection, NullPool, create_engine, text


def get_db() -> Connection:
    if "db" not in g:
        g.db = current_app.db_pool.connect()
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def executescript(schema_sql):
    db = get_db()
    sql_command = schema_sql.split(";")
    for statement in sql_command:
        # Strip any whitespace or newlines at the end
        statement = statement.strip()
        if statement:  # Avoid executing empty statements
            db.execute(text(statement))
    db.commit()


def init_db():
    db = get_db()
    driver_name = db.engine.url.drivername
    # this gives 'sqlite', 'mysql', 'postgresql', etc.
    db_type = driver_name.split("+")[0]
    match db_type:
        case "sqlite":
            sql_file = "schema_sqlite.sql"
        case "mysql" | "mariadb":  # treat mariadb as mysql for schema purposes
            sql_file = "schema_mariadb.sql"
        case _:
            raise ValueError(f"Unsupported DB type: {db_type}")

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
    db_uri = app.config.get(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{app.config['SQLITE_PATH']}"
    )
    if db_uri.startswith("sqlite"):
        app.db_pool = create_engine(db_uri, poolclass=NullPool)  # No pooling for SQLite
    else:
        app.db_pool = create_engine(
            app.config.get(
                "SQLALCHEMY_DATABASE_URI",
                f"sqlite:///{app.config['SQLITE_PATH']}",
            ),
            pool_size=5,  # Number of connections to keep open
            max_overflow=5,  # Number of extra connections to open if needed
            pool_pre_ping=True,  # Check connection before using it
        )
