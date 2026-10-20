from agent.tools import transcript


def course_result(student_id: str, course: str) -> dict:
    """Resultado do aluno em uma disciplina (código ou nome): nota final, situação e se foi aprovado."""
    wanted = course.upper()
    for row in transcript(student_id):
        if wanted == row["course_code"] or wanted in row["course_name"].upper():
            return {"course": row["course_name"], "term": row["term"],
                    "final_grade": row["final_grade"], "status": row["status"]}
    return {"error": f"course '{course}' not found"}


TOOLS = [course_result]
