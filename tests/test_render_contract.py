import pytest
from dataclasses import FrozenInstanceError
from app.render.render_contract import (Color, FillRect, Text, Draw,
                                        ThemeChanged, IntervalChanged)


def test_color_class():
    color = Color(r=255, g=0, b=0, a=255)
    assert color.r == 255
    assert color.g == 0
    assert color.b == 0
    assert color.a == 255


def test_color_frozen():
    color = Color(r=255, g=0, b=0, a=255)
    with pytest.raises(FrozenInstanceError):
        color.r = 0


def test_fill_rect_class():
    fill_rect = FillRect(x=0, y=0, width=100, height=100,
                         color=Color(r=255, g=0, b=0, a=255))
    assert fill_rect.x == 0
    assert fill_rect.y == 0
    assert fill_rect.width == 100
    assert fill_rect.height == 100
    assert fill_rect.color == Color(r=255, g=0, b=0, a=255)


def test_fill_rect_frozen():
    fill_rect = FillRect(x=0, y=0, width=100, height=100,
                         color=Color(r=255, g=0, b=0, a=255))
    with pytest.raises(FrozenInstanceError):
        fill_rect.x = 0


def test_text_class():
    text = Text(x=10, y=5, content="Hello world!",
                color=Color(r=255, g=0, b=0, a=255))
    assert text.x == 10
    assert text.y == 5
    assert text.content == "Hello world!"
    assert text.color == Color(r=255, g=0, b=0, a=255)


def test_text_frozen():
    text = Text(x=10, y=5, content="Hello world!",
                color=Color(r=255, g=0, b=0, a=255))
    with pytest.raises(FrozenInstanceError):
        text.x = 0


def test_draw_class():
    color = Color(r=255, g=0, b=0, a=255)
    text = Text(x=10, y=5, content="Hello world!", color=color)
    fill_rect = FillRect(x=0, y=0, width=100, height=100, color=color)
    fill_rect_2 = FillRect(x=100, y=100, width=100, height=100, color=color)
    clear_color = Color(r=255, g=0, b=0, a=255)
    draw = Draw(commands=[text, fill_rect, fill_rect_2], clear=clear_color)
    assert len(draw.commands) == 3
    assert draw.commands == [text, fill_rect, fill_rect_2]
    assert draw.clear == clear_color

    draw = Draw(commands=[text, fill_rect])
    assert len(draw.commands) == 2
    assert draw.commands == [text, fill_rect]
    assert draw.clear is None


def test_draw_frozen():
    color = Color(r=255, g=0, b=0, a=255)
    text = Text(x=10, y=5, content="Hello world!", color=color)
    fill_rect = FillRect(x=0, y=0, width=100, height=100, color=color)
    fill_rect_2 = FillRect(x=100, y=100, width=100, height=100, color=color)
    clear_color = Color(r=255, g=0, b=0, a=255)
    draw = Draw(commands=[text, fill_rect, fill_rect_2], clear=clear_color)
    with pytest.raises(FrozenInstanceError):
        draw.commands = [text, fill_rect]


def test_theme_changed_class():
    theme_changed = ThemeChanged(theme="dark")
    assert theme_changed.theme == "dark"


def test_theme_changed_frozen():
    theme_changed = ThemeChanged(theme="dark")
    with pytest.raises(FrozenInstanceError):
        theme_changed.theme = "light"


def test_interval_changed_class():
    interval_changed = IntervalChanged(seconds=1.0)
    assert interval_changed.seconds == 1.0


def test_interval_changed_frozen():
    interval_changed = IntervalChanged(seconds=1.0)
    with pytest.raises(FrozenInstanceError):
        interval_changed.seconds = 2.0
