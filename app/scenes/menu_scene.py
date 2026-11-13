"""Fixed-layout settings menu driven only by the keyboard.

Does not talk to MiniLibX: returns Draw/Idle for the renderer and
ThemeChanged / IntervalChanged / SeedChanged / GoToMaze / Quit for the app.
"""

from enum import Enum

from app.render.render_contract import (
    Draw,
    FillRect,
    GoToMaze,
    Idle,
    IntervalChanged,
    Key,
    Quit,
    SeedChanged,
    Text,
    ThemeChanged,
)
from app.runtime_settings import (
    INTERVAL_STEP,
    MAX_STEP_INTERVAL,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    MIN_STEP_INTERVAL,
    RuntimeSettings,
    SEED_STEP,
)
from app.theme.catalog import next_theme_name
from app.theme.theme import Theme

# Approximate default MLX font metrics.
_CHAR_W = 10
_LINE_H = 20


class MenuOption(Enum):
    """Rows shown in the menu; .value is the selection index."""

    THEME = 0
    SPEED = 1
    SEED = 2
    BACK = 3


class MenuScene:
    """Main-menu scene: theme, speed, seed, and return to the maze.

    Option rows share one left edge; that column is centered on the canvas
    using an estimated text width (_CHAR_W). The stack is also centered
    vertically. The selected row uses text_highlight.

    Painting is pull-based: on_key / update_settings only mark
    _scene_change; on_tick (or on_enter) returns the actual Draw.
    Esc quits the app (root scene); Enter on Back emits GoToMaze.
    """

    def __init__(self, settings: RuntimeSettings, theme: Theme) -> None:
        self._settings = settings
        self._theme = theme
        self._selected = 0
        # True when the next on_tick must rebuild the frame.
        self._scene_change = False
        self._canvas_h = MENU_MIN_HEIGHT
        self._canvas_w = MENU_MIN_WIDTH

    def _edit_speed(self, delta: int) -> float:
        """Return step_interval ± INTERVAL_STEP, clamped to MIN/MAX."""
        return max(
            MIN_STEP_INTERVAL,
            min(
                self._settings.step_interval + delta * INTERVAL_STEP,
                MAX_STEP_INTERVAL,
            ),
        )

    def _edit_seed(self, delta: int) -> int:
        """Return seed ± SEED_STEP, clamped to >= 0."""
        return max(0, self._settings.seed + delta * SEED_STEP)

    def _label_for(self, option: MenuOption) -> str:
        match option:
            case MenuOption.THEME:
                return f"Theme: {self._settings.theme_name}"
            case MenuOption.SPEED:
                return f"Speed: {self._settings.step_interval:.2f}"
            case MenuOption.SEED:
                return f"Seed: {self._settings.seed}"
            case MenuOption.BACK:
                return "Render maze"

    def _composer(self) -> Draw:
        """Build one full frame: clear with theme.background + option texts."""
        labels = [self._label_for(option) for option in MenuOption]
        content_height = len(labels) * _LINE_H
        content_width = max(len(label) * _CHAR_W for label in labels)
        # Left-aligned column, optically centered on the canvas.
        text_x = max(0, (self._canvas_w - content_width) // 2)
        text_y = max(0, (self._canvas_h - content_height) // 2)
        text_options: list[FillRect | Text] = []
        for option, content in zip(MenuOption, labels):
            color = (
                self._theme.text_highlight
                if option.value == self._selected
                else self._theme.text
            )
            text_options.append(
                Text(x=text_x, y=text_y, content=content, color=color)
            )
            text_y = text_y + _LINE_H
        return Draw(commands=text_options, clear=self._theme.background)

    def update_settings(self, settings: RuntimeSettings, theme: Theme) -> None:
        """Store an immutable settings/theme snapshot from the app"""
        if self._settings != settings or self._theme != theme:
            self._settings = settings
            self._theme = theme
            self._scene_change = True

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        """Called when this scene becomes active; always full repaint."""
        self._canvas_w = canvas_width
        self._canvas_h = canvas_height
        self._scene_change = False
        return self._composer()

    def on_tick(self, elapsed: float) -> Draw | Idle:
        """Repaint only if dirty (selection or settings changed); else Idle.

        elapsed is unused here; MazeScene will use it for step timing.
        """
        if self._scene_change:
            self._scene_change = False
            return self._composer()
        return Idle()

    def on_key(
        self, key: Key
    ) -> ThemeChanged | IntervalChanged | SeedChanged | GoToMaze | Quit | None:
        """Handle navigation and edits; return an action for the app or None.

        Up/Down: move selection and mark dirty (repaint on next tick).
        Left/Right: ThemeChanged / IntervalChanged / SeedChanged.
        Enter on Back: GoToMaze. Esc: Quit.
        """
        match key:
            case Key.UP:
                self._selected = (self._selected - 1) % len(MenuOption)
                self._scene_change = True
                return None
            case Key.DOWN:
                self._selected = (self._selected + 1) % len(MenuOption)
                self._scene_change = True
                return None
            case Key.RIGHT:
                if self._selected == MenuOption.THEME.value:
                    return ThemeChanged(
                        next_theme_name(self._settings.theme_name, 1)
                    )
                if self._selected == MenuOption.SPEED.value:
                    return IntervalChanged(self._edit_speed(1))
                if self._selected == MenuOption.SEED.value:
                    return SeedChanged(self._edit_seed(1))
                return None
            case Key.LEFT:
                if self._selected == MenuOption.THEME.value:
                    return ThemeChanged(
                        next_theme_name(self._settings.theme_name, -1)
                    )
                if self._selected == MenuOption.SPEED.value:
                    return IntervalChanged(self._edit_speed(-1))
                if self._selected == MenuOption.SEED.value:
                    return SeedChanged(self._edit_seed(-1))
                return None
            case Key.ENTER:
                if self._selected == MenuOption.BACK.value:
                    return GoToMaze()
                return None
            case Key.ESC:
                return Quit()
        return None
