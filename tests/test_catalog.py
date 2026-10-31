import pytest
from app.theme.catalog import (get_theme, next_theme_name,
                               default_theme, theme_names)
from app.runtime_settings import DEFAULT_THEME_NAME


def test_get_theme():
    theme = get_theme("classic")
    assert theme is not None
    assert theme.name == "classic"


def test_get_nonexistent_theme():
    with pytest.raises(ValueError):
        get_theme("nonexistent")


def test_next_theme_name():
    names = theme_names()
    n = len(names)
    for name in names:
        i = names.index(name)
        assert next_theme_name(name, 1) == names[(i + 1) % n]
        assert next_theme_name(name, -1) == names[(i - 1) % n]


def test_get_default_theme():
    assert default_theme().name == DEFAULT_THEME_NAME
    assert get_theme(DEFAULT_THEME_NAME) is not None
