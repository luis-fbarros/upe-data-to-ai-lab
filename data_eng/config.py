from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT_DIR = PACKAGE_DIR.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
ERRORS_DIR = DATA_DIR / "errors"
DOCS_DIR = DATA_DIR / "docs"
EXTRACTORS_DIR = PACKAGE_DIR / "extractors"
SCHEMA_FILE = PACKAGE_DIR / "db" / "schema.sql"

DATABASE_URL = "postgresql://siga:siga@127.0.0.1:5433/siga"

SIGA_LOGIN_URLS = {
    "ufape": "https://siga.ufape.edu.br/ufape/index.jsp",
    "upe": "https://siga.upe.br/upe/index.jsp",
}
SHOW_BROWSER = True
PAGE_TIMEOUT_SECONDS = 120
LOGIN_TIMEOUT_SECONDS = 180
