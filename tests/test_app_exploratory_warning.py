from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_real_pilot_data_are_explicitly_labelled_exploratory():
    app = AppTest.from_file(str(ROOT / "app" / "main.py"), default_timeout=45)
    app.run()

    assert not app.exception, "\n".join(
        str(exception.value) for exception in app.exception
    )
    warning_text = [element.value for element in app.warning]
    assert any("EXPLORATORY REAL-DATA PILOT" in value for value in warning_text)
    assert any("not an approved geomorphic AOI" in value for value in warning_text)
    info_text = [element.value for element in app.info]
    assert any("Slope P50 and P90 only" in value for value in info_text)
