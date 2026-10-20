import sys
from collections import deque
from decimal import Decimal

from psycopg.rows import dict_row

from data_eng import db
from data_eng.transform import compute_cr

PASSED_STATUSES = ("APROVADO", "DISPENSADO", "APROVEITADO")
IN_PROGRESS_STATUS = "CURSANDO"

PASSING_AVERAGE = 7.0
FINAL_EXAM_MIN_AVERAGE = 3.0
FINAL_PASSING_AVERAGE = 5.0
MAX_ABSENCE_RATE = 0.25


def query(sql, params=()):
    with db.connect() as connection:
        connection.row_factory = dict_row
        rows = connection.execute(sql, params).fetchall()
    for row in rows:
        for column, value in row.items():
            if isinstance(value, Decimal):
                row[column] = float(value)
    return rows


def passed(status):
    return any(word in (status or "") for word in PASSED_STATUSES)


def prerequisites_of(course):
    return [code for code in (course["prerequisites"] or "").split(", ") if code]


def curriculum_by_code(student_id):
    return {course["course_code"]: course for course in
            query("SELECT * FROM curriculum WHERE student_id = %s", (student_id,))}


def passed_and_in_progress(student_id):
    passed_codes, in_progress_codes = set(), set()
    for row in transcript(student_id):
        if passed(row["status"]):
            passed_codes.add(row["course_code"])
        elif row["status"] == IN_PROGRESS_STATUS:
            in_progress_codes.add(row["course_code"])
    return passed_codes, in_progress_codes


def progress(student_id: str) -> dict:
    """Perfil do aluno, CR e progresso no curso: carga horária exigida, concluída e restante por categoria."""
    student = query("SELECT * FROM student WHERE student_id = %s", (student_id,))
    categories = query("SELECT category, required_hours, completed_hours, remaining_hours, completed_percentage "
                       "FROM workload WHERE student_id = %s", (student_id,))
    result = student[0] if student else {}
    result["workload"] = categories
    total = next((c for c in categories if c["category"] == "Total"), None)
    if total:
        result["completed_percentage"] = total["completed_percentage"]
        result["remaining_hours"] = total["remaining_hours"]
    return result


def transcript(student_id: str, term: str | None = None) -> list[dict]:
    """Disciplinas cursadas, com nota final e situação. `term` opcional, ex: '2025.1'."""
    if term:
        return query("SELECT * FROM transcript WHERE student_id = %s AND term = %s", (student_id, term))
    return query("SELECT * FROM transcript WHERE student_id = %s ORDER BY term", (student_id,))


def schedule(student_id: str, weekday: str | None = None) -> list[dict]:
    """Aulas da semana. `weekday` opcional: SEG, TER, QUA, QUI, SEX ou SAB."""
    if weekday:
        return query("SELECT * FROM schedule WHERE student_id = %s AND weekday = %s ORDER BY start_time",
                     (student_id, weekday.upper()))
    return query("SELECT * FROM schedule WHERE student_id = %s "
                 "ORDER BY array_position(ARRAY['SEG','TER','QUA','QUI','SEX','SAB'], weekday), start_time",
                 (student_id,))


def pending_courses(student_id: str) -> list[dict]:
    """Disciplinas obrigatórias que ainda faltam, com o período sugerido."""
    return query("SELECT * FROM pending_courses WHERE student_id = %s ORDER BY suggested_term", (student_id,))


def search_curriculum(student_id: str, text: str) -> list[dict]:
    """Busca disciplinas do curso por nome ou código, com tipo, período, pré-requisitos e ementa."""
    return query("SELECT * FROM curriculum WHERE student_id = %s AND (course_name ILIKE %s OR course_code ILIKE %s)",
                 (student_id, f"%{text}%", f"%{text}%"))


def cr_by_term(student_id: str) -> list[dict]:
    """CR (coeficiente de rendimento) de cada período já cursado."""
    rows = transcript(student_id)
    history = []
    for term in sorted({row["term"] for row in rows}):
        cr = compute_cr(rows, term)
        if cr is not None:
            history.append({"term": term, "cr": cr})
    return history


def simulate_cr(student_id: str, expected_grades: dict[str, float]) -> dict:
    """Simula o CR se as disciplinas em curso fecharem com as notas esperadas. Ex: {'BCC00003': 8.0}."""
    rows = transcript(student_id)
    used = []
    for row in rows:
        if row["status"] != IN_PROGRESS_STATUS:
            continue
        for course, grade in expected_grades.items():
            wanted = course.upper()
            if wanted == row["course_code"] or wanted in row["course_name"]:
                row["final_grade"] = float(grade)
                used.append(row["course_name"])
    return {
        "current_cr": compute_cr(transcript(student_id)),
        "simulated_cr": compute_cr(rows),
        "courses_considered": used,
    }


def grade_situation(va1, va2, va3):
    grades = [grade for grade in (va1, va2) if grade is not None]
    if va3 is not None and grades:
        grades.remove(min(grades))
        grades.append(va3)

    if not grades:
        return {"situation": "no grades yet"}
    if len(grades) == 1:
        needed = max(0.0, 2 * PASSING_AVERAGE - grades[0])
        return {"situation": "in progress", "needed_on_next_va_to_pass": round(needed, 2)}

    average = sum(grades) / 2
    if average >= PASSING_AVERAGE:
        return {"situation": "passing", "average": average}
    if average >= FINAL_EXAM_MIN_AVERAGE:
        needed = 2 * FINAL_PASSING_AVERAGE - average
        return {"situation": "final exam", "average": average, "needed_on_final_exam": round(needed, 2)}
    return {"situation": "failing", "average": average}


def term_status(student_id: str) -> list[dict]:
    """Situação de cada disciplina em curso: notas VA1/VA2/VA3, nota necessária, faltas restantes."""
    current = query("SELECT * FROM transcript WHERE student_id = %s AND status = %s", (student_id, IN_PROGRESS_STATUS))
    released = query("SELECT * FROM grades WHERE student_id = %s", (student_id,))

    report = []
    for course in current:
        grades = {row["assessment"]: row for row in released
                  if row["course_code"] == course["course_code"] and row["term"] == course["term"]}
        va1, va2, va3 = (grades[name]["grade"] if name in grades else None for name in ("VA1", "VA2", "VA3"))
        absences = next(iter(grades.values()))["absences"] if grades else course["absences"]
        max_absences = int(course["workload_hours"] * MAX_ABSENCE_RATE)

        item = {"course_code": course["course_code"], "course_name": course["course_name"],
                "VA1": va1, "VA2": va2, "VA3": va3, "absences": absences, "max_absences": max_absences}
        item.update(grade_situation(item["VA1"], item["VA2"], item["VA3"]))
        if absences is not None:
            item["absences_left"] = max_absences - absences
            if absences > max_absences:
                item["situation"] = "failed by absences"
        report.append(item)
    return report


def failure_impact(student_id: str, course: str) -> dict:
    """Disciplinas que ficam bloqueadas se o aluno reprovar na disciplina informada (código ou nome)."""
    curriculum = curriculum_by_code(student_id)
    wanted = course.upper()
    target = next((c for code, c in curriculum.items() if wanted == code or wanted in c["course_name"]), None)
    if target is None:
        return {"error": f"course '{course}' not found in the curriculum"}

    dependents = {code: [] for code in curriculum}
    for code, item in curriculum.items():
        for prerequisite in prerequisites_of(item):
            dependents.setdefault(prerequisite, []).append(code)

    passed_codes, _ = passed_and_in_progress(student_id)
    blocked, depth = [], {target["course_code"]: 0}
    queue = deque([target["course_code"]])
    while queue:
        code = queue.popleft()
        for dependent in dependents.get(code, []):
            if dependent in depth or dependent in passed_codes:
                continue
            depth[dependent] = depth[code] + 1
            queue.append(dependent)
            item = curriculum[dependent]
            blocked.append({"course_code": dependent, "course_name": item["course_name"],
                            "term": item["term"], "level": depth[dependent]})

    return {"course": target["course_name"], "blocked_courses": blocked,
            "chain_length": max(depth.values())}


def next_enrollment(student_id: str) -> dict:
    """Disciplinas que o aluno pode cursar agora, ou se passar nas atuais, respeitando pré-requisitos."""
    curriculum = curriculum_by_code(student_id)
    passed_codes, in_progress_codes = passed_and_in_progress(student_id)

    available_now, after_current_term = [], []
    for code, course in curriculum.items():
        if code in passed_codes or code in in_progress_codes:
            continue
        prerequisites = set(prerequisites_of(course))
        item = {"course_code": code, "course_name": course["course_name"], "course_type": course["course_type"],
                "term": course["term"], "workload_hours": course["workload_hours"]}
        if prerequisites <= passed_codes:
            available_now.append(item)
        elif prerequisites <= passed_codes | in_progress_codes:
            after_current_term.append(item)

    def order(item):
        mandatory = (item["course_type"] or "").startswith("OBRIGAT")
        term = int(item["term"]) if (item["term"] or "").isdigit() else 99
        return (not mandatory, term, item["course_name"])

    return {"available_now": sorted(available_now, key=order),
            "available_if_current_courses_pass": sorted(after_current_term, key=order)}


def graduation_forecast(student_id: str) -> dict:
    """Estimativa de períodos restantes para a formatura, pela carga horária média por período."""
    total = query("SELECT remaining_hours FROM workload WHERE student_id = %s AND category = 'Total'", (student_id,))
    graded = [row for row in transcript(student_id) if row["final_grade"] is not None]
    terms = {row["term"] for row in graded}
    if not total or not terms:
        return {"error": "not enough data"}
    hours_per_term = sum(row["workload_hours"] for row in graded) / len(terms)
    return {
        "remaining_hours": total[0]["remaining_hours"],
        "average_hours_per_term": round(hours_per_term),
        "estimated_terms_left": round(total[0]["remaining_hours"] / hours_per_term, 1),
    }


TOOLS = [
    progress, transcript, schedule, pending_courses, search_curriculum,
    cr_by_term, simulate_cr, term_status, failure_impact, next_enrollment, graduation_forecast,
]


if __name__ == "__main__":
    student_id = sys.argv[1]
    print(progress(student_id))
    print(term_status(student_id))
    print(next_enrollment(student_id))
