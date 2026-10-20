import re


def clean_text(value):
    if value is None:
        return None
    without_cpf = re.sub(r"\b\d{11}\b", "", str(value))
    return " ".join(without_cpf.split())


def to_number(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def split_course_code(name):
    parts = [part.strip() for part in name.split(" - ")]
    code = parts[0]
    if len(parts) >= 3:
        return code, " - ".join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return code, parts[1], None
    return None, name, None


def truncate(value, decimals=2):
    factor = 10 ** decimals
    return int(value * factor) / factor


def compute_cr(transcript, term=None):
    weighted_sum = 0
    total_hours = 0
    for row in transcript:
        if row["final_grade"] is None:
            continue
        if term is not None and row["term"] != term:
            continue
        weighted_sum += row["final_grade"] * row["workload_hours"]
        total_hours += row["workload_hours"]
    if total_hours == 0:
        return None
    return truncate(weighted_sum / total_hours)


def transform_transcript(raw):
    rows = []
    for term in raw["periods"]:
        for course in term["subjects"]:
            if course["code"] is None:
                continue
            rows.append({
                "term": term["period"],
                "course_code": course["code"],
                "course_name": clean_text(course["name"]),
                "absences": to_number(course["absences"]),
                "workload_hours": to_number(course["workload"]),
                "credits": to_number(course["credits"]),
                "final_grade": to_number(course["final_grade"]),
                "status": clean_text(course["status"]),
            })
    return rows


def transform_student(raw_student, raw_transcript, raw_progress, transcript):
    student = {}
    if raw_student:
        student["student_id"] = raw_student.get("registration")
        student["name"] = clean_text(raw_student.get("name"))
        student["program"] = clean_text(raw_student.get("course"))
        student["entry_term"] = raw_student.get("entry_period")
        student["current_term"] = raw_student.get("current_period")
        student["status"] = raw_student.get("situation")
        student["shift"] = raw_student.get("shift")
    if raw_transcript:
        student["siga_gpa"] = to_number(raw_transcript["overall_coefficient"])
        student["siga_average"] = to_number(raw_transcript["overall_average"])
        student["computed_gpa"] = compute_cr(transcript)
    if raw_progress:
        student["pending_hours"] = raw_progress["pending_components"]["total_pending_hours"]
    return [student]


def transform_grades(raw):
    rows = []
    for course in raw["subjects"]:
        code, name, class_group = split_course_code(clean_text(course["name"]))
        absences = to_number(course["grades"].get("Faltas"))
        for assessment, grade in course["grades"].items():
            if assessment == "Faltas":
                continue
            rows.append({
                "term": course["term"],
                "course_code": code,
                "course_name": name,
                "class_group": class_group,
                "professor": clean_text(course["teacher"]),
                "status": clean_text(course["status"]),
                "absences": absences,
                "assessment": assessment,
                "grade": to_number(grade),
            })
    return rows


def transform_schedule(raw):
    rows = []
    for course in raw["subjects"]:
        for slot in course["time_slots"]:
            rows.append({
                "course_code": course["code"],
                "course_name": clean_text(course["name"]),
                "class_group": course["class_name"],
                "room": clean_text(course["room"]),
                "weekday": slot["day"],
                "start_time": slot["start"],
                "end_time": slot["end"],
            })
    return rows


def transform_pending_courses(raw):
    rows = []
    for course in raw["pending_components"]["subjects"]:
        rows.append({
            "course_code": course["code"],
            "course_name": clean_text(course["name"]),
            "workload_hours": course["workload"],
            "suggested_term": course["period"],
            "credits": course["credits"],
        })
    return rows


def transform_workload(raw):
    rows = []
    for item in raw["workload_summary"]:
        rows.append({
            "category": clean_text(item["name"]),
            "required_hours": item["integration"],
            "completed_hours": item["completed_hours"],
            "waived_hours": item["waived_hours"],
            "remaining_hours": item["to_complete_hours"],
            "completed_percentage": item["completed_percentage"],
        })
    return rows


def transform_curriculum(raw):
    rows = []
    for block in raw["blocks"]:
        for course in block["subjects"]:
            prerequisites = [prerequisite["code"] for prerequisite in course["prerequisites"]]
            rows.append({
                "block": clean_text(block["name"]),
                "course_code": course["code"],
                "course_name": clean_text(course["name"]),
                "course_type": course["type"],
                "term": course["period"],
                "workload_hours": course["workload"]["total"],
                "credits": course["credits"],
                "prerequisites": ", ".join(prerequisites),
                "syllabus": clean_text(course["syllabus"]),
            })
    return rows


def transform(raw):
    transcript = transform_transcript(raw["transcript"]) if raw["transcript"] else []
    progress = raw["academic_progress"]
    return {
        "student": transform_student(raw["student"], raw["transcript"], progress, transcript),
        "transcript": transcript,
        "grades": transform_grades(raw["grades"]) if raw["grades"] else [],
        "schedule": transform_schedule(raw["schedule"]) if raw["schedule"] else [],
        "pending_courses": transform_pending_courses(progress) if progress else [],
        "workload": transform_workload(progress) if progress else [],
        "curriculum": transform_curriculum(raw["curriculum"]) if raw["curriculum"] else [],
    }
