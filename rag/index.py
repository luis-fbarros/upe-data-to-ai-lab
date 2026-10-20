import argparse

from data_eng import db
from data_eng.config import DOCS_DIR
from rag.embed import embed, to_vector_literal

CHUNK_SIZE = 800


def chunk(text: str) -> list[str]:
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        if current and len(current) + len(paragraph) > CHUNK_SIZE:
            chunks.append(current.strip())
            current = ""
        current += paragraph + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def syllabus_documents(connection, student_id: str) -> list[tuple[str | None, str, str]]:
    rows = connection.execute(
        "SELECT course_code, course_name, syllabus FROM curriculum WHERE student_id = %s AND syllabus <> ''",
        (student_id,),
    ).fetchall()
    return [(student_id, f"ementa:{code}", f"{name} ({code}): {syllabus}") for code, name, syllabus in rows]


def file_documents() -> list[tuple[str | None, str, str]]:
    documents = []
    for file in sorted(DOCS_DIR.glob("*")):
        if file.suffix not in (".txt", ".md"):
            continue
        for number, piece in enumerate(chunk(file.read_text(encoding="utf-8"))):
            documents.append((None, f"{file.name}#{number}", piece))
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Vectorizes syllabi and files in data/docs/ into PostgreSQL")
    parser.add_argument("student_id")
    args = parser.parse_args()

    connection = db.connect()
    db.create_tables(connection)
    documents = syllabus_documents(connection, args.student_id) + file_documents()
    if not documents:
        raise SystemExit("No documents to index.")

    vectors = embed([content for _, _, content in documents], "RETRIEVAL_DOCUMENT")
    connection.execute("DELETE FROM documents WHERE student_id = %s OR student_id IS NULL", (args.student_id,))
    for (student_id, source, content), vector in zip(documents, vectors):
        connection.execute(
            "INSERT INTO documents (student_id, source, content, embedding) VALUES (%s, %s, %s, %s::vector)",
            (student_id, source, content, to_vector_literal(vector)),
        )
    connection.commit()
    connection.close()
    print(f"{len(documents)} documents indexed")


if __name__ == "__main__":
    main()
