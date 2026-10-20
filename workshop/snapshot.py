import json
import re
from collections import Counter

from data_eng.config import DATA_DIR, RAW_DIR

OUTPUT_FILE = DATA_DIR / "snapshot.md"
CPF = re.compile(r"\b\d{11}\b")
MAX_SAMPLES = 5


def mask(text: str) -> str:
    return CPF.sub("***********", text)


def is_scalar(value) -> bool:
    return not isinstance(value, (dict, list))


def collect_lists(value, path: str, found: dict[str, list]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            collect_lists(item, f"{path}.{key}" if path else key, found)
    elif isinstance(value, list):
        found.setdefault(path + "[]", []).extend(value)
        for item in value:
            collect_lists(item, path + "[]", found)


def describe_columns(items: list[dict]) -> list[str]:
    lines = ["| coluna | tipos | nulos | distintos | exemplos |", "|---|---|---|---|---|"]
    keys = list(dict.fromkeys(key for item in items for key in item))
    for key in keys:
        values = [item.get(key) for item in items]
        scalars = [value for value in values if is_scalar(value) and value is not None]
        types = ", ".join(sorted({type(value).__name__ for value in values if value is not None})) or "null"
        distinct = {json.dumps(value, ensure_ascii=False) for value in scalars}
        samples = ", ".join(sorted(distinct)[:MAX_SAMPLES])
        lines.append(f"| {key} | {types} | {values.count(None)} | {len(distinct)} | {samples} |")
    return lines


def describe_section(name: str, content: dict) -> list[str]:
    lines = [f"## {name}", ""]
    scalars = {key: value for key, value in content.items() if is_scalar(value)}
    if scalars:
        lines += ["### campos simples", "", "```json", json.dumps(scalars, ensure_ascii=False, indent=2), "```", ""]

    found: dict[str, list] = {}
    collect_lists(content, "", found)
    for path, items in found.items():
        records = [item for item in items if isinstance(item, dict)]
        if not records:
            continue
        lines += [f"### {path} ({len(records)} itens)", ""]
        lines += describe_columns(records)
        lines += ["", "exemplo:", "", "```json", json.dumps(records[0], ensure_ascii=False, indent=2), "```", ""]
    return lines


def main() -> None:
    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        raise SystemExit("No files in data/raw/. Run the pipeline first.")

    lines = ["# Snapshot dos dados brutos do SIGA", ""]
    lines += [f"Seções: {', '.join(file.stem for file in files)}", ""]
    for file in files:
        content = json.loads(file.read_text(encoding="utf-8"))
        lines += describe_section(file.stem, content)

    OUTPUT_FILE.write_text(mask("\n".join(lines)), encoding="utf-8")
    print(f"Snapshot saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
