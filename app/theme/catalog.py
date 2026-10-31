"""Named theme catalogue and default theme.

Themes live here as a private map; callers only use the public helpers.
"""

from app.render.render_contract import Color
from app.runtime_settings import DEFAULT_THEME_NAME
from app.theme.theme import Theme


def _classic() -> Theme:
    return Theme(
        name="classic",
        background=Color(18, 18, 24),
        text=Color(230, 230, 235),
        text_highlight=Color(255, 210, 80),
        wall=Color(200, 200, 210),
        cell_floor=Color(32, 32, 42),
        trail=Color(70, 90, 140),
        head=Color(255, 120, 80),
        entry=Color(80, 200, 120),
        exit=Color(220, 80, 100),
        solution=Color(120, 180, 255),
        pattern=Color(180, 140, 255),
    )


def _retro() -> Theme:
    # Amber CRT / terminal vibe.
    return Theme(
        name="retro",
        background=Color(10, 12, 8),
        text=Color(180, 255, 120),
        text_highlight=Color(255, 220, 60),
        wall=Color(60, 140, 60),
        cell_floor=Color(16, 28, 14),
        trail=Color(40, 90, 40),
        head=Color(255, 180, 40),
        entry=Color(100, 220, 100),
        exit=Color(255, 100, 60),
        solution=Color(140, 255, 180),
        pattern=Color(255, 200, 80),
    )


def _high_contrast() -> Theme:
    return Theme(
        name="high_contrast",
        background=Color(0, 0, 0),
        text=Color(255, 255, 255),
        text_highlight=Color(255, 255, 0),
        wall=Color(255, 255, 255),
        cell_floor=Color(20, 20, 20),
        trail=Color(0, 180, 255),
        head=Color(255, 80, 0),
        entry=Color(0, 255, 0),
        exit=Color(255, 0, 0),
        solution=Color(0, 200, 255),
        pattern=Color(255, 0, 255),
    )


def _halloween() -> Theme:
    return Theme(
        name="halloween",
        background=Color(12, 8, 18),
        text=Color(255, 200, 120),
        text_highlight=Color(255, 140, 40),
        wall=Color(180, 90, 40),
        cell_floor=Color(28, 16, 36),
        trail=Color(90, 40, 110),
        head=Color(255, 120, 30),
        entry=Color(80, 200, 80),
        exit=Color(220, 40, 40),
        solution=Color(255, 180, 60),
        pattern=Color(160, 60, 200),
    )


def _neon() -> Theme:
    # Tron-like: dark grid, cyan / magenta accents.
    return Theme(
        name="neon",
        background=Color(2, 8, 18),
        text=Color(180, 255, 255),
        text_highlight=Color(0, 255, 255),
        wall=Color(0, 200, 255),
        cell_floor=Color(6, 20, 40),
        trail=Color(0, 80, 140),
        head=Color(255, 0, 200),
        entry=Color(0, 255, 180),
        exit=Color(255, 40, 120),
        solution=Color(120, 220, 255),
        pattern=Color(255, 0, 255),
    )


def _build_catalog() -> dict[str, Theme]:
    catalog: dict[str, Theme] = {}
    for factory in (_classic, _retro, _high_contrast, _halloween, _neon):
        theme = factory()
        theme.validate()
        catalog[theme.name] = theme
    return catalog


_THEMES: dict[str, Theme] = _build_catalog()


def get_theme(name: str) -> Theme:
    """Return a theme by name, or raise ValueError."""
    if name not in _THEMES:
        raise ValueError(f"Unknown theme: {name!r}")
    return _THEMES[name]


def default_theme() -> Theme:
    """Return the default theme (see RuntimeSettings.DEFAULT_THEME_NAME)."""
    return get_theme(DEFAULT_THEME_NAME)


def theme_names() -> tuple[str, ...]:
    """Return ordered theme names for the menu selector."""
    others = sorted(n for n in _THEMES if n != DEFAULT_THEME_NAME)
    return (DEFAULT_THEME_NAME, *others)


def next_theme_name(current: str, delta: int) -> str:
    """Cycle theme names by delta (+1 / -1)."""
    names = theme_names()
    try:
        index = names.index(current)
    except ValueError:
        return names[0]
    # Cycle through the theme names, wrapping around to the start if necessary.
    return names[(index + delta) % len(names)]
