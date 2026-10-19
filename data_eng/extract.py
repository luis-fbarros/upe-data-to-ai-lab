import json
import logging
import re
import time
from collections.abc import Callable

from playwright.sync_api import Frame, Locator, Page, sync_playwright

from data_eng.config import (
    ERRORS_DIR, EXTRACTORS_DIR, LOGIN_TIMEOUT_SECONDS, PAGE_TIMEOUT_SECONDS, RAW_DIR, SHOW_BROWSER,
    SIGA_LOGIN_URLS,
)

log = logging.getLogger(__name__)

SECTIONS = ["student", "transcript", "academic_progress", "curriculum", "schedule", "grades"]

PAGE_READY = {
    "menu": "document.querySelectorAll('[id$=\":outputLinkTransacao\"]').length > 0",
    "student": "!!document.querySelector('#tableCabecalho')",
    "transcript": "Array.from(document.querySelectorAll('div#content table'))"
                  ".some(t => t.innerText.trim().startsWith('Período:'))",
    "academic_progress": "!!document.getElementById('bt_a1')",
    "curriculum": "!!document.querySelector('[id=\"formDetalharPerfilCurricular:tabelas\"] span.editBold')",
    "schedule": "(document.querySelector('font.subtitle')?.innerText || '').includes('Disciplinas Solicitadas')",
    "grades": "!!document.getElementById('form-corpo') && "
              "!!document.querySelector('input[type=\"button\"][value=\"Imprimir\"]')",
}

MENU_TEXT = "Detalhamento de Discente"
STUDENT_INFO_BUTTON = "Informações do Discente"
GRADES_BUTTON = "Notas"
INVALID_LOGIN_TEXT = "Nome de usuário ou senha inválida!"

STUDENT_INFO_LINKS = [
    ("transcript", "Histórico Escolar"),
    ("academic_progress", "Aproveitamento Acadêmico"),
    ("curriculum", "Perfil Curricular"),
    ("schedule", "Grade de Horário"),
]


class SigaClient:
    """Browser session on SIGA. Keeps the credentials to log in again if the session drops."""

    def __init__(self, page: Page, institution: str, login: str, password: str):
        self.page = page
        self.login_url = SIGA_LOGIN_URLS[institution]
        self.login = login
        self.password = password

    def frame(self) -> Frame | None:
        return self.page.frame(name="Conteudo")

    @staticmethod
    def click(locator: Locator) -> None:
        """JavaScript click: also works on hidden elements, like SIGA's menu."""
        locator.first.evaluate("element => element.click()", timeout=15_000)

    def wait_until_ready(self, section: str) -> None:
        start = time.time()
        while time.time() - start < PAGE_TIMEOUT_SECONDS:
            try:
                if self.frame() is None:
                    raise RuntimeError(f"SIGA left the logged-in area (current page: {self.page.url})")
                if self.frame().url.startswith("chrome-error"):
                    raise RuntimeError("the page failed to load")
                if self.frame().evaluate(PAGE_READY[section]):
                    return
            except RuntimeError:
                raise
            except Exception:
                pass
            self.page.wait_for_timeout(500)
        raise RuntimeError(f"the page did not load within {PAGE_TIMEOUT_SECONDS} seconds")

    def run_extractor(self, section: str) -> dict:
        script = (EXTRACTORS_DIR / f"{section}.js").read_text(encoding="utf-8")
        script = script[script.index("() =>"):]
        data = self.frame().evaluate(script)
        if "error" in data:
            raise RuntimeError(data["error"])
        return data

    def save_error_snapshot(self, name: str) -> None:
        try:
            ERRORS_DIR.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=ERRORS_DIR / f"{name}.png", full_page=True)
            (ERRORS_DIR / f"{name}.html").write_text(self.page.content(), encoding="utf-8")
            if self.frame() is not None:
                (ERRORS_DIR / f"{name}-iframe.html").write_text(self.frame().content(), encoding="utf-8")
        except Exception:
            pass

    def sign_in(self) -> None:
        self.page.goto(self.login_url)
        self.page.fill("#cpf", self.login)
        self.page.fill("#txtPassword", self.password)
        self.page.click("#btnEntrar")
        log.info("Signing in... (if a captcha shows up, solve it in the browser window)")

        start = time.time()
        while time.time() - start < LOGIN_TIMEOUT_SECONDS:
            try:
                if self.page.query_selector("#lblNomePessoa"):
                    return
                if INVALID_LOGIN_TEXT in self.page.inner_text("body"):
                    raise SystemExit("Invalid CPF/student ID or password.")
                # Captcha: keep the fields filled; SIGA submits by itself once it is solved.
                password_field = self.page.query_selector("#txtPassword")
                if password_field and password_field.input_value() == "":
                    self.page.fill("#cpf", self.login)
                    self.page.fill("#txtPassword", self.password)
            except SystemExit:
                raise
            except Exception:
                pass
            self.page.wait_for_timeout(1000)
        raise SystemExit("Could not sign in to SIGA (timed out).")

    def ensure_signed_in(self) -> None:
        if self.frame() is None or not self.page.query_selector("#lblNomePessoa"):
            log.info("  SIGA session dropped; signing in again...")
            self.sign_in()

    def open_menu(self) -> None:
        self.ensure_signed_in()
        if self.frame().url.startswith("chrome-error"):
            self.page.reload()
        self.click(self.page.get_by_text(MENU_TEXT, exact=True))
        self.wait_until_ready("menu")

    def open_menu_button(self, text: str) -> None:
        self.open_menu()
        self.click(self.frame().locator('[id$=":outputLinkTransacao"]', has_text=text))

    def open_student_info_link(self, text: str, attempt: int) -> None:
        """The links stay on screen (SIGA swaps content via AJAX); on a retry, reopen the page first."""
        if attempt == 2 or self.frame() is None:
            self.open_menu_button(STUDENT_INFO_BUTTON)
            self.wait_until_ready("student")
        # Exact match: another link is called "Perfil Curricular X Histórico Escolar".
        exact_text = re.compile(rf"^\s*{text}\s*$")
        self.click(self.frame().locator("ul.sanfona a, a.default").filter(has_text=exact_text))

    def extract_section(self, section: str, open_page: Callable[[int], None]) -> dict | None:
        for attempt in (1, 2):
            start = time.time()
            try:
                open_page(attempt)
                self.wait_until_ready(section)
                data = self.run_extractor(section)
                log.info(f"  [ok]     {section} ({time.time() - start:.0f}s)")
                return data
            except Exception as error:
                log.warning(f"  [failed] {section}, attempt {attempt}: {error}")
                self.save_error_snapshot(f"{section}-{attempt}")
        return None

    def extract_all(self) -> dict[str, dict | None]:
        raw = {}
        raw["student"] = self.extract_section(
            "student", lambda attempt: self.open_menu_button(STUDENT_INFO_BUTTON))

        for section, link_text in STUDENT_INFO_LINKS:
            raw[section] = self.extract_section(
                section, lambda attempt, text=link_text: self.open_student_info_link(text, attempt))

        raw["grades"] = self.extract_section("grades", lambda attempt: self.open_menu_button(GRADES_BUTTON))
        return raw


def extract_from_siga(institution: str, login: str, password: str) -> dict[str, dict | None]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not SHOW_BROWSER)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        client = SigaClient(page, institution, login, password)
        client.sign_in()
        log.info("Signed in. Extracting:")
        raw = client.extract_all()
        browser.close()
    return raw


def save_raw(raw: dict[str, dict | None]) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in RAW_DIR.glob("*.json"):
        old_file.unlink()  # never mix data from different students
    for section, content in raw.items():
        if content is not None:
            (RAW_DIR / f"{section}.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


def load_raw() -> dict[str, dict | None]:
    raw = {}
    for section in SECTIONS:
        file = RAW_DIR / f"{section}.json"
        if file.exists():
            raw[section] = json.loads(file.read_text(encoding="utf-8"))
        else:
            log.warning(f"  warning: {file} does not exist")
            raw[section] = None
    return raw
