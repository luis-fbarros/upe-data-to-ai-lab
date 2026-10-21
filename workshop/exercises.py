import unicodedata

from agent.tools import cr_by_term, schedule, transcript

WEEKDAYS = ("SEG", "TER", "QUA", "QUI", "SEX", "SAB")
DAY_START = "07:00"
DAY_END = "22:00"
PASSED_WORDS = ("APROVADO", "DISPENSADO", "APROVEITADO")


def normalize_weekday(value: str) -> str | None:
    text = unicodedata.normalize("NFD", value).encode("ascii", "ignore").decode().upper().strip()
    raise NotImplementedError


def gaps(classes: list[dict]) -> list[dict]:
    free = []
    cursor = DAY_START
    for item in classes:
        raise NotImplementedError
    return free


def passed_course(student_id: str, course: str) -> dict:
    """Informa se o aluno foi aprovado em uma disciplina, pelo código ou pelo nome."""
    wanted = course.upper()
    rows = [row for row in transcript(student_id)
            if wanted == row["course_code"] or wanted in row["course_name"].upper()]
    if not rows:
        return {"error": f"course '{course}' not found"}
    row = rows[-1]
    raise NotImplementedError
    return {"course": row["course_name"], "status": row["status"], "passed": passed}


def best_term(student_id: str) -> dict:
    """Período em que o aluno teve o melhor CR."""
    history = cr_by_term(student_id)
    if not history:
        return {"error": "no graded terms"}
    raise NotImplementedError


def free_time(student_id: str, weekday: str) -> dict:
    """Intervalos livres entre as aulas do aluno em um dia da semana (segunda, terça, sexta...)."""
    day = normalize_weekday(weekday)
    if day is None:
        return {"error": f"unknown weekday '{weekday}'"}
    classes = schedule(student_id, day)
    return {"weekday": day, "free": gaps(classes)}


TOOLS = [passed_course, best_term, free_time]
