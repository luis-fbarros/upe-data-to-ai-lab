-- gpa = SIGA's "CR" (coeficiente de rendimento), a 0-10 weighted grade average.

CREATE TABLE IF NOT EXISTS student (
    student_id        TEXT PRIMARY KEY,
    name              TEXT,
    program           TEXT,
    entry_term        TEXT,
    current_term      TEXT,
    status            TEXT,
    shift             TEXT,
    siga_gpa          NUMERIC(4, 2),
    siga_average      NUMERIC(4, 2),
    computed_gpa      NUMERIC(4, 2),
    pending_hours     INTEGER,
    updated_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS transcript (
    student_id      TEXT,
    term            TEXT,
    course_code     TEXT,
    course_name     TEXT,
    absences        INTEGER,
    workload_hours  INTEGER,
    credits         INTEGER,
    final_grade     NUMERIC(4, 2),
    status          TEXT
);

CREATE TABLE IF NOT EXISTS grades (
    student_id   TEXT,
    term         TEXT,
    course_code  TEXT,
    course_name  TEXT,
    class_group  TEXT,
    professor    TEXT,
    status       TEXT,
    absences     INTEGER,
    assessment   TEXT,
    grade        NUMERIC(4, 2)
);

CREATE TABLE IF NOT EXISTS schedule (
    student_id   TEXT,
    course_code  TEXT,
    course_name  TEXT,
    class_group  TEXT,
    room         TEXT,
    weekday      TEXT,
    start_time   TEXT,
    end_time     TEXT
);

CREATE TABLE IF NOT EXISTS pending_courses (
    student_id      TEXT,
    course_code     TEXT,
    course_name     TEXT,
    workload_hours  INTEGER,
    suggested_term  INTEGER,
    credits         INTEGER
);

CREATE TABLE IF NOT EXISTS workload (
    student_id            TEXT,
    category              TEXT,
    required_hours        INTEGER,
    completed_hours       INTEGER,
    waived_hours          INTEGER,
    remaining_hours       INTEGER,
    completed_percentage  NUMERIC(5, 2)
);

CREATE TABLE IF NOT EXISTS curriculum (
    student_id      TEXT,
    block           TEXT,
    course_code     TEXT,
    course_name     TEXT,
    course_type     TEXT,
    term            TEXT,
    workload_hours  INTEGER,
    credits         INTEGER,
    prerequisites   TEXT,
    syllabus        TEXT
);
