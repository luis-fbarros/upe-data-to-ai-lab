from psycopg.rows import dict_row

from data_eng import db
from rag.embed import embed, to_vector_literal

TOP_K = 4


def search_documents(student_id: str, question: str) -> list[dict]:
    """Busca semântica nas ementas das disciplinas e nos documentos indexados (ex: regulamento). Use para dúvidas sobre conteúdo de disciplinas e regras."""
    vector = to_vector_literal(embed([question], "RETRIEVAL_QUERY")[0])
    with db.connect() as connection:
        connection.row_factory = dict_row
        return connection.execute(
            "SELECT source, content, embedding <=> %s::vector AS distance FROM documents "
            "WHERE student_id = %s OR student_id IS NULL ORDER BY distance LIMIT %s",
            (vector, student_id, TOP_K),
        ).fetchall()
