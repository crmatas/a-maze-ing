"""Shared types between the renderer, scenes, and the app.

ThemeChanged, IntervalChanged, SeedChanged, Regenerate, GoToMaze,
GoToMenu, Quit are actions that scenes return for the app (renderer
only forwards them). Those actions are dataclasses because
Scene.on_key() returns them.
"""


from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol


class Key(Enum):
    """Logical keys. The renderer maps raw X11 keycodes to these names.
    This contract should not have magic numbers or scatter X11 symbols.
    The magic numbers are defined in the renderer."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    ENTER = auto()
    ESC = auto()
    R = auto()  # regenerate maze (#58)
    S = auto()  # toggle solution path (#58)


@dataclass(frozen=True)
class Color:
    """RGBA colour. The renderer handles MLX channel order."""

    r: int
    g: int
    b: int
    a: int = 255


@dataclass(frozen=True)
class FillRect:
    """Filled rectangle in canvas pixels (goes to the framebuffer)."""

    x: int
    y: int
    width: int
    height: int
    color: Color


@dataclass(frozen=True)
class Text:
    """Text at a pixel position (goes through mlx_string_put)."""

    x: int
    y: int
    content: str
    color: Color


@dataclass(frozen=True)
class Draw:
    """Something to paint this tick.

    If clear is set, fill the whole canvas with that colour first.
    Paint order is decided by the renderer: rects -> image -> texts.
    """

    commands: list[FillRect | Text]
    clear: Color | None = None


@dataclass(frozen=True)
class Idle:
    """Nothing new: the renderer skips repainting this tick."""


@dataclass(frozen=True)
class ThemeChanged:
    """Change the theme of the application. The theme is a string."""

    theme: str


@dataclass(frozen=True)
class IntervalChanged:
    """Change the interval of the application.
    The interval is a float in seconds."""

    seconds: float


@dataclass(frozen=True)
class SeedChanged:
    """Change the maze RNG seed (applied by the app)."""

    seed: int


@dataclass(frozen=True)
class Regenerate:
    """Rebuild the maze with the current seed and replay generation."""


@dataclass(frozen=True)
class GoToMaze:
    """Leave the menu and activate the maze scene."""


@dataclass(frozen=True)
class GoToMenu:
    """Leave the maze and activate the menu scene."""


@dataclass(frozen=True)
class Quit:
    """Close the application."""


class Scene(Protocol):
    """What the renderer needs from whatever is on screen."""

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        """Called when the scene becomes active. Must return a full repaint."""
        ...

    def on_tick(self, elapsed: float) -> Draw | Idle:
        """Called each loop tick.
        elapsed is seconds since the previous tick."""
        ...

    def on_key(self, key: Key) -> (
        ThemeChanged
        | IntervalChanged
        | SeedChanged
        | Regenerate
        | GoToMaze
        | GoToMenu
        | Quit
        | None
    ):
        """Called with a logical key. May return an action for the app."""
        ...
