"""Fixed-layout settings menu driven only by the keyboard."""

from app.render.render_contract import (
    Draw,
    Idle,
    Key,
    GoToMaze,
    IntervalChanged,
    Quit,
    ThemeChanged,
)
from app.runtime_settings import (RuntimeSettings,
                                  INTERVAL_STEP,
                                  MIN_STEP_INTERVAL,
                                  MAX_STEP_INTERVAL)
from app.theme.theme import Theme
from app.theme.catalog import next_theme_name
from enum import Enum


class MenuOption(Enum):
    THEME = 0
    SPEED = 1
    BACK = 2


class MenuScene:
    """Centered fixed layout; size is the menu minimum offset if window larger.

    Options (to implement): theme, speed, back to maze.
    Selection index + brief colour pulse on the selected row.
    Preview uses the current theme (background fill on full repaint).
    """

    def __init__(self, settings: RuntimeSettings, theme: Theme) -> None:
        self._settings = settings
        self._theme = theme
        self._selected = 0
        self._highlight_elapsed = 0.0
        self._scene_change = False

    def _edit_speed(self, delta: int) -> float:
        new_speed: float = max(MIN_STEP_INTERVAL,
                               min(self._settings.step_interval +
                                   delta * INTERVAL_STEP,
                                   MAX_STEP_INTERVAL))
        return new_speed

    def update_settings(self, settings: RuntimeSettings, theme: Theme) -> None:
        """Receive a new immutable settings / theme snapshot from the app."""
        if (self._settings != settings or self._theme != theme):
            self._settings = settings
            self._theme = theme
            self._scene_change = True

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        """Full repaint of the menu (must clear with theme.background)."""
        raise NotImplementedError

    def on_tick(self, elapsed: float) -> Draw | Idle:
        """Advance selection pulse; return Draw while animating, else Idle."""
        raise NotImplementedError

    def on_key(
        self, key: Key
    ) -> ThemeChanged | IntervalChanged | GoToMaze | Quit | None:
        """
        Up/down change index; left/right edit;
        Enter -> GoToMaze; Esc -> Quit
        """

        match key:
            case Key.UP:
                self._selected = (self._selected - 1) % len(MenuOption)
                self._highlight_elapsed = 0.0
                return None
            case Key.DOWN:
                self._selected = (self._selected + 1) % len(MenuOption)
                self._highlight_elapsed = 0.0
                return None
            case Key.RIGHT:
                if self._selected == MenuOption.THEME.value:
                    return ThemeChanged(
                        next_theme_name(self._settings.theme_name, 1))
                elif self._selected == MenuOption.SPEED.value:
                    return IntervalChanged(self._edit_speed(1))
                return None
            case Key.LEFT:
                if self._selected == MenuOption.THEME.value:
                    return ThemeChanged(
                            next_theme_name(self._settings.theme_name, -1))
                elif self._selected == MenuOption.SPEED.value:
                    return IntervalChanged(self._edit_speed(-1))
                return None
            case Key.ENTER:
                if self._selected == MenuOption.BACK.value:
                    return GoToMaze()
                return None
            case Key.ESC:
                return Quit()
