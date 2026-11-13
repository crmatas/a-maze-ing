from app.render.render_contract import Color
from app.theme.theme import Theme


def _theme(*, text: Color, text_highlight: Color,
           background: Color = Color(0, 0, 0)) -> Theme:
    return Theme(
        name="test",
        background=background,
        text=text,
        text_highlight=text_highlight,
        wall=Color(0, 0, 0),
        cell_floor=Color(0, 0, 0),
        trail=Color(0, 0, 0),
        head=Color(0, 0, 0),
        entry=Color(0, 0, 0),
        exit=Color(0, 0, 0),
        solution=Color(0, 0, 0),
        pattern=Color(0, 0, 0),
    )


def test_valid_theme() -> None:
    theme = _theme(
        text=Color(255, 255, 255),
        text_highlight=Color(255, 255, 255),
    )
    assert theme.validate() is True


def test_invalid_contrast_text_theme() -> None:
    theme = _theme(
        text=Color(0, 0, 0),
        text_highlight=Color(255, 0, 0),
    )
    assert theme.validate() is False


def test_invalid_contrast_highlight_text_theme() -> None:
    theme = _theme(
        text=Color(255, 0, 0),
        text_highlight=Color(0, 0, 0),
    )
    assert theme.validate() is False
