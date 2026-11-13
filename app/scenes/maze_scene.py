"""Maze generation scene: one generator event per configured interval."""

from app.interpret.maze_interpreter import MazeInterpreter
from app.render.render_contract import (
    Draw,
    GoToMaze,
    GoToMenu,
    Idle,
    IntervalChanged,
    Key,
    Quit,
    ThemeChanged,
)
from app.runtime_settings import RuntimeSettings
from app.theme.theme import Theme
from mazegen import MazeGenerator
from mazegen.constants import Step
from collections.abc import Iterator


class MazeScene:
    """Holds generate_steps();suspended when the menu is shown,never destroyed.

    On re-enter: full repaint from the grid with the curr theme, then continue.
    States: generating / finished (Idle when done).

    The generator owns the grid; this scene only paces generate_steps().
    """

    def __init__(
        self,
        generator: MazeGenerator,
        interpreter: MazeInterpreter,
        settings: RuntimeSettings,
        theme: Theme,
    ) -> None:
        self._generator = generator
        self._interpreter = interpreter
        self._settings = settings
        self._theme = theme
        self._steps: Iterator[Step] | None = None
        self._accum = 0.0
        self._done = False
        self._started = False

    def update_settings(self, settings: RuntimeSettings, theme: Theme) -> None:
        """Receive a new immutable settings / theme snapshot from the app."""
        self._settings = settings
        self._theme = theme

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        """Start the iterator once; always return a full grid repaint."""
        if not self._started:
            self._interpreter.reset_runtime_marks()
            self._done = False
            self._accum = 0.0
            self._steps = self._generator.generate_steps()
            self._started = True
        return self._interpreter.full_repaint(self._theme)

    def on_tick(self, elapsed: float) -> Draw | Idle:
        """Accumulate elapsed; when past interval, take one event -> Draw."""
        if self._steps is None or self._done:
            return Idle()
        self._accum += elapsed
        if self._accum < self._settings.step_interval:
            return Idle()
        self._accum = 0.0
        try:
            event = next(self._steps)
        except StopIteration:
            self._done = True
            return Idle()
        return self._interpreter.commands_for_event(event, self._theme)

    def on_key(
        self, key: Key
    ) -> ThemeChanged | IntervalChanged | GoToMaze | GoToMenu | Quit | None:
        """Esc (and similar) should return GoToMenu."""
        if key == Key.ESC:
            return GoToMenu()
        return None
