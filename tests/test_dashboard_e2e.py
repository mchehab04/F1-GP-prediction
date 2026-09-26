from streamlit.testing.v1 import AppTest
import os
import sys

import pytest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

APP_PATH = os.path.join(project_root, "python", "dashboard", "app.py")
PAGES = [
    "views/race_hub.py",
    "views/championship.py",
    "views/race_explorer.py",
    "views/qualifying.py",
    "views/teammates.py",
    "views/circuits.py",
    "views/race_weekend.py",
    "views/reliability.py",
    "views/predictor.py",
    "views/methodology.py",
]
SEASONS = [2022, 2023, 2024, 2025, 2026]


def _errors(at):
    return [e.value for e in at.exception]


def test_dashboard_full_run():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception, f"App loaded with exceptions: {_errors(at)}"


@pytest.mark.parametrize("page", PAGES)
def test_every_page_every_season(page):
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    at.switch_page(page).run()
    assert not at.exception, f"{page}: {_errors(at)}"
    for year in SEASONS:
        at.selectbox(key="season").select(year).run()
        assert not at.exception, f"{page} / {year}: {_errors(at)}"


if __name__ == "__main__":
    test_dashboard_full_run()
    for p in PAGES:
        test_every_page_every_season(p)
    print("[SUCCESS] ALL PAGES AND SEASONS RENDERED WITH 0 EXCEPTIONS")
