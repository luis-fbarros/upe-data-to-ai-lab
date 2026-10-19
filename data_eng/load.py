import logging

import psycopg

log = logging.getLogger(__name__)


def load(connection: psycopg.Connection, tables: dict[str, list[dict]]) -> None:
    """Replaces the student's rows in every table. Does not commit."""
    student_id = tables["student"][0]["student_id"]
    for table_name, rows in tables.items():
        connection.execute(f"DELETE FROM {table_name} WHERE student_id = %s", (student_id,))
        for row in rows:
            row = {"student_id": student_id, **row}
            columns = ", ".join(row.keys())
            placeholders = ", ".join("%s" for _ in row)
            connection.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", list(row.values()))
        log.info(f"  {table_name}: {len(rows)} rows")
