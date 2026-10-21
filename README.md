# Data-to-AI Lab

SIGA → ETL → PostgreSQL (Docker) → agente com tools e RAG.

## Fluxo

```
SIGA (login e senha) → data/raw/*.json → transform → PostgreSQL + pgvector → agente (ADK)
```

| Pasta | Função |
|---|---|
| `data_eng/` | extração do SIGA, transformação, carga e validação |
| `workshop/` | snapshot dos dados brutos e tools escritas pelos participantes |
| `rag/` | vetorização das ementas e arquivos, e busca semântica |
| `agent/` | tools de consulta ao banco e o agente |

## Executar

```bash
docker compose up -d
uv sync
uv run playwright install chromium
uv run python -m data_eng.pipeline ufape
```

## Oficina

1. Gerar o snapshot dos dados brutos (formatos, exemplos, sumário):

```bash
uv run python -m workshop.snapshot
```

2. Ler `data/snapshot.md` e escrever funções de normalização em `data_eng/transform.py`.
3. Completar os exercícios em `workshop/exercises.py`: `normalize_weekday`, `passed_course`, `best_term` e `gaps` (horários livres). Cada `raise NotImplementedError` é uma lacuna. O agente carrega `workshop/my_tools.py`, que usa essas funções. O gabarito está na branch `workshop-completo`.
4. Vetorizar ementas e arquivos de `data/docs/`:

```bash
cp agent/.env.example agent/.env
uv run python -m rag.index <matricula>
```

5. Conversar com o agente:

```bash
uv run adk web
```
