import logging

import psycopg

log = logging.getLogger(__name__)

# (level, description, query)
# Se level for "error", validate falha e bloqueia a requisição

RULES = [
    ("error", "final grade outside 0-10",
     "SELECT count(*) FROM transcript WHERE student_id = %s AND (final_grade < 0 OR final_grade > 10)"),
    ("error", "assessment grade outside 0-10",
     "SELECT count(*) FROM grades WHERE student_id = %s AND (grade < 0 OR grade > 10)"),
    ("error", "term not in the YYYY.S format",
     "SELECT count(*) FROM transcript WHERE student_id = %s AND term !~ '^[0-9]{4}\\.[0-9]$'"),
    ("error", "course without workload hours",
     "SELECT count(*) FROM transcript WHERE student_id = %s AND (workload_hours IS NULL OR workload_hours <= 0)"),
    ("error", "course repeated in the same term",
     "SELECT count(*) FROM (SELECT term, course_code FROM transcript WHERE student_id = %s "
     "GROUP BY term, course_code HAVING count(*) > 1) AS repeated"),
    ("error", "invalid weekday",
     "SELECT count(*) FROM schedule WHERE student_id = %s AND weekday NOT IN ('SEG','TER','QUA','QUI','SEX','SAB')"),
    ("error", "class ends before it starts",
     "SELECT count(*) FROM schedule WHERE student_id = %s AND end_time <= start_time"),
    ("error", "CPF in a course name",
     "SELECT count(*) FROM transcript WHERE student_id = %s AND course_name ~ '[0-9]{11}'"),
    ("warning", "computed GPA differs from SIGA's",
     "SELECT count(*) FROM student WHERE student_id = %s AND computed_gpa <> siga_gpa"),
    ("warning", "student without name or program",
     "SELECT count(*) FROM student WHERE student_id = %s AND (name IS NULL OR program IS NULL)"),
]

TABLES = ["transcript", "grades", "schedule", "pending_courses", "workload", "curriculum"]


def validate(connection: psycopg.Connection, student_id: str) -> bool:
    errors = 0
    for level, description, sql in RULES:
        problems = connection.execute(sql, (student_id,)).fetchone()[0]
        if problems == 0:
            log.info(f"[ok] {description}")
        else:
            log.warning(f"[{level}] {description}: {problems} row(s)")
            errors += level == "error"

    for table in TABLES:
        rows = connection.execute(f"SELECT count(*) FROM {table} WHERE student_id = %s", (student_id,)).fetchone()[0]
        if rows == 0:
            log.warning(f"[warning] table {table} is empty")

    return errors == 0
