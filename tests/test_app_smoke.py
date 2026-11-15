from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_app_renders_with_curated_exploratory_mvp_data():
    app = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=30)
    app.run()
    assert not app.exception, "\n".join(
        str(exception.value) for exception in app.exception
    )
