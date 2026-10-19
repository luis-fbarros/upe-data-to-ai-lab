import psycopg

from data_eng.config import DATABASE_URL, SCHEMA_FILE


def connect() -> psycopg.Connection:
    try:
        return psycopg.connect(DATABASE_URL, connect_timeout=5)
    except psycopg.OperationalError:
        raise SystemExit("Could not connect to the database. Is it running? Try: docker compose up -d")


def create_tables(connection: psycopg.Connection) -> None:
    connection.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
