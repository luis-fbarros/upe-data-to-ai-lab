from google import genai
from google.genai import types

MODEL = "gemini-embedding-001"
DIMENSIONS = 768
BATCH_SIZE = 50


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    client = genai.Client()
    config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=DIMENSIONS)
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start:start + BATCH_SIZE]
        response = client.models.embed_content(model=MODEL, contents=batch, config=config)
        vectors.extend(item.values for item in response.embeddings)
    return vectors


def to_vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(value) for value in vector) + "]"
