from agent.tools import grade_situation
from data_eng.transform import compute_cr, split_course_code, to_number, truncate
from rag.index import chunk
from workshop.snapshot import describe_columns, mask


def test_to_number_accepts_comma():
    assert to_number("7,5") == 7.5
    assert to_number("abc") is None
    assert to_number(None) is None


def test_truncate_does_not_round():
    assert truncate(8.6785) == 8.67


def test_compute_cr_weighs_by_workload():
    rows = [
        {"term": "2025.1", "final_grade": 10.0, "workload_hours": 60},
        {"term": "2025.1", "final_grade": 5.0, "workload_hours": 30},
        {"term": "2025.2", "final_grade": None, "workload_hours": 60},
    ]
    assert compute_cr(rows) == 8.33
    assert compute_cr(rows, "2025.2") is None


def test_split_course_code():
    assert split_course_code("BCC00003 - EMPREENDEDORISMO I - CC5") == ("BCC00003", "EMPREENDEDORISMO I", "CC5")


def test_grade_situation():
    assert grade_situation(8.0, 7.0, None)["situation"] == "passing"
    assert grade_situation(4.0, 3.0, None)["situation"] == "final exam"
    assert grade_situation(1.0, 1.0, None)["situation"] == "failing"
    assert grade_situation(None, None, None)["situation"] == "no grades yet"


def test_chunk_splits_long_text():
    text = "\n\n".join(["a" * 500, "b" * 500, "c" * 100])
    assert len(chunk(text)) == 2


def test_mask_hides_cpf():
    assert "12345678901" not in mask("cpf 12345678901")


def test_describe_columns_counts_nulls():
    lines = describe_columns([{"grade": "7,5"}, {"grade": None}])
    assert "| grade | str | 1 | 1 |" in lines[-1]
