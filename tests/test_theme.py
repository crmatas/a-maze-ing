import pytest
from app.theme.theme import Theme
from app.render.render_contract import Color


def test_valid_theme():
    assert Theme(
            name="test",
            background=Color(0, 0, 0, 0),
            text=Color(255, 255, 255, 255),
            text_highlight=Color(255, 255, 255, 255),
            wall=Color(0, 0, 0, 0),
            cell_floor=Color(0, 0, 0, 0),
            trail=Color(0, 0, 0, 0),
            head=Color(0, 0, 0, 0),
            entry=Color(0, 0, 0, 0),
            exit=Color(0, 0, 0, 0),
            solution=Color(0, 0, 0, 0),
            pattern=Color(0, 0, 0, 0)
            ).validate() is None


def test_invalid_contrast_text_theme():
    with pytest.raises(ValueError) as e:
        Theme(
            name="test",
            background=Color(0, 0, 0, 0),
            text=Color(0, 0, 0, 0),
            text_highlight=Color(255, 0, 0, 0),
            wall=Color(0, 0, 0, 0),
            cell_floor=Color(0, 0, 0, 0),
            trail=Color(0, 0, 0, 0),
            head=Color(0, 0, 0, 0),
            entry=Color(0, 0, 0, 0),
            exit=Color(0, 0, 0, 0),
            solution=Color(0, 0, 0, 0),
            pattern=Color(0, 0, 0, 0)
        ).validate()
    assert "Text contrast ratio is too low:" in str(e.value)


def test_invalid_contrast_highlight_text_theme():
    with pytest.raises(ValueError) as e:
        Theme(
            name="test",
            background=Color(0, 0, 0, 0),
            text=Color(255, 0, 0, 0),
            text_highlight=Color(0, 0, 0, 0),
            wall=Color(0, 0, 0, 0),
            cell_floor=Color(0, 0, 0, 0),
            trail=Color(0, 0, 0, 0),
            head=Color(0, 0, 0, 0),
            entry=Color(0, 0, 0, 0),
            exit=Color(0, 0, 0, 0),
            solution=Color(0, 0, 0, 0),
            pattern=Color(0, 0, 0, 0)
        ).validate()
    assert "Text highlight contrast ratio is too low:" in str(e.value)
