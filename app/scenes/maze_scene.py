"""Maze generation scene: one generator event per configured interval."""

from collections.abc import Iterator

from app.interpret.maze_interpreter import MazeInterpreter
from app.render.render_contract import (
    Draw,
    GoToMaze,
    GoToMenu,
    Idle,
    IntervalChanged,
    Key,
    Quit,
    Regenerate,
    ThemeChanged,
)
from app.runtime_settings import RuntimeSettings
from app.theme.theme import Theme
from mazegen import BfsSolver, MazeGenerator
from mazegen.constants import Step


class MazeScene:
    """Holds generate_steps; suspended when the menu is shown, never destroyed.

    On re-enter: full repaint from the grid with the curr theme, then continue.
    States: generating / finished (Idle when done).

    When finished: R asks the app to rebuild (same seed → same maze);
    S / Enter toggles an animated continuous solution path (#58).
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
        self._show_solution = False
        self._path: list[tuple[int, int]] = []
        self._shown = 0
        self._needs_repaint = False

    def update_settings(self, settings: RuntimeSettings, theme: Theme) -> None:
        """Receive a new immutable settings / theme snapshot from the app."""
        self._settings = settings
        self._theme = theme

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        """Start the iterator once; always return a full grid repaint."""
        if not self._started:
            self._start_generation()
        self._needs_repaint = False
        return self._interpreter.full_repaint(self._theme)

    def on_tick(self, elapsed: float) -> Draw | Idle:
        """Accumulate elapsed; advance generation or solution reveal."""
        if self._needs_repaint:
            self._needs_repaint = False
            return self._interpreter.full_repaint(self._theme)

        revealing = (
            self._done
            and self._show_solution
            and self._shown < len(self._path)
        )
        if revealing:
            self._accum += elapsed
            if self._accum < self._settings.step_interval:
                return Idle()
            self._accum = 0.0
            self._shown += 1
            self._interpreter.set_solution_cells(self._path[: self._shown])
            return self._interpreter.full_repaint(self._theme)

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
            # Drop DFS trail/head so braid leftovers cannot linger on screen.
            self._interpreter.clear_generation_marks()
            return self._interpreter.full_repaint(self._theme)
        return self._interpreter.commands_for_event(event, self._theme)

    def on_key(
        self, key: Key
    ) -> (
        ThemeChanged
        | IntervalChanged
        | Regenerate
        | GoToMaze
        | GoToMenu
        | Quit
        | None
    ):
        """Esc → menu; R → Regenerate; S/Enter (when done)→toggle solution."""
        if key == Key.ESC:
            return GoToMenu()
        if key == Key.R:
            return Regenerate()
        if key in (Key.S, Key.ENTER):
            if self._done:
                self._toggle_solution()
                self._needs_repaint = True
            return None
        return None

    def _start_generation(self) -> None:
        """Begin a fresh generate_steps iterator."""
        self._interpreter.reset_runtime_marks()
        self._show_solution = False
        self._path = []
        self._shown = 0
        self._done = False
        self._accum = 0.0
        self._steps = self._generator.generate_steps()
        self._started = True

    def _toggle_solution(self) -> None:
        """Show or hide the shortest path; show starts a stepped reveal."""
        if self._show_solution:
            self._show_solution = False
            self._path = []
            self._shown = 0
            self._interpreter.set_solution_cells(())
            return

        path = BfsSolver(
            self._generator.grid,
            self._generator.entry,
            self._generator.exit,
        ).path()
        self._show_solution = True
        self._path = path
        # First cell on the pending full_repaint; the rest grow in on_tick.
        self._shown = 1 if path else 0
        self._interpreter.set_solution_cells(path[: self._shown])
        self._accum = 0.0
