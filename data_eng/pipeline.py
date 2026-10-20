
import argparse
import getpass
import logging

from data_eng import db
from data_eng.config import SIGA_LOGIN_URLS
from data_eng.extract import extract_from_siga, load_raw, save_raw
from data_eng.load import load
from data_eng.transform import transform
from data_eng.validate import validate

log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SIGA -> PostgreSQL data pipeline")
    parser.add_argument("institution", nargs="?", default="ufape", choices=sorted(SIGA_LOGIN_URLS))
    parser.add_argument("--skip-extract", action="store_true", help="reuse data/raw/ instead of signing in to SIGA")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args()
    connection = db.connect()

    if args.skip_extract:
        log.info("1. Reading data/raw/")
        raw = load_raw()
    else:
        log.info("1. Extracting from SIGA")
        login = input("CPF or student ID: ").strip()
        password = getpass.getpass("SIGA password: ")
        raw = extract_from_siga(args.institution, login, password)
        save_raw(raw)

    if not raw["student"]:
        raise SystemExit("The student section is missing, so there is no student ID. Run it again.")

    log.info("\n2. Transforming")
    tables = transform(raw)
    student = tables["student"][0]

    log.info("\n3. Loading")
    db.create_tables(connection)
    load(connection, tables)

    log.info("\n4. Validating")
    if validate(connection, student["student_id"]):
        connection.commit()
        log.info(f"\nDone! Data for {student['name']} saved. GPA: {student.get('computed_gpa')}")
    else:
        connection.rollback()
        log.info("\nValidation failed, nothing was saved.")
    connection.close()


if __name__ == "__main__":
    main()
