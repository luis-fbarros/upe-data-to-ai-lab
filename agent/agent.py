import os

from google.adk.agents import Agent

from agent.tools import TOOLS, query
from rag.search import search_documents
from workshop import my_tools

MODEL = "gemini-2.5-flash"

INSTRUCTION = """Você é um assistente acadêmico que responde dúvidas de um aluno usando os dados dele do SIGA.
O student_id do aluno é {student_id}. Use sempre esse valor nas ferramentas.
Responda em português, de forma curta e direta, usando só o que as ferramentas retornarem.
Se uma informação não estiver nos dados, diga que não encontrou."""


def current_student_id() -> str:
    student_id = os.environ.get("STUDENT_ID")
    if student_id:
        return student_id
    rows = query("SELECT student_id FROM student ORDER BY updated_at DESC LIMIT 1")
    if not rows:
        raise SystemExit("No student in the database. Run the pipeline first.")
    return rows[0]["student_id"]


root_agent = Agent(
    name="siga_assistant",
    model=MODEL,
    instruction=lambda context: INSTRUCTION.format(student_id=current_student_id()),
    tools=[*TOOLS, search_documents, *my_tools.TOOLS],
)
