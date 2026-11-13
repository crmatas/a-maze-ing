"""Application orchestrator: config, scenes, and MLX lifecycle.

Construction order:
  config.txt -> MazeGenerator -> probe screen -> window size -> MlxRender
  -> MazeInterpreter -> MenuScene / MazeScene -> mlx_loop
"""

import sys
from pathlib import Path

from mlx import Mlx
from pydantic import ValidationError

from app.interpret.maze_interpreter import MazeInterpreter
from app.parser import Config
from app.render.mlx_render import MlxRender, compute_window_size
from app.render.render_contract import (
    GoToMaze,
    GoToMenu,
    IntervalChanged,
    Quit,
    Regenerate,
    SeedChanged,
    ThemeChanged,
)
from app.runtime_settings import (
    DEFAULT_SEED,
    FALLBACK_MAX_HEIGHT,
    FALLBACK_MAX_WIDTH,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    RuntimeSettings,
)
from app.scenes.maze_scene import MazeScene
from app.scenes.menu_scene import MenuScene
from app.theme.catalog import default_theme, get_theme
from app.theme.theme import Theme
from mazegen.maze_generator import MazeGenerator


def probe_screen_size() -> tuple[int, int]:
    """Ask MiniLibX for the display size; fall back if the probe fails."""
    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    if not mlx_ptr:
        return FALLBACK_MAX_WIDTH, FALLBACK_MAX_HEIGHT
    try:
        ret, width, height = mlx.mlx_get_screen_size(mlx_ptr)
        if ret != 0 or width <= 0 or height <= 0:
            return FALLBACK_MAX_WIDTH, FALLBACK_MAX_HEIGHT
        return int(width), int(height)
    finally:
        mlx.mlx_release(mlx_ptr)


class App:
    """Own runtime settings, scene transitions, and ordered MLX teardown.

    ``handle_action`` is the only place that matches on action kinds.
    Regenerating builds a new MazeGenerator with the menu seed (same seed
    → same maze) and clears the window via set_scene / on_enter.
    """

    def __init__(
        self,
        config: Config,
        *,
        screen_size: tuple[int, int] | None = None,
    ) -> None:
        self._config = config
        seed = config.seed if config.seed is not None else DEFAULT_SEED
        self._settings = RuntimeSettings(seed=seed)
        self._theme: Theme = default_theme()

        if screen_size is None:
            screen_w, screen_h = probe_screen_size()
        else:
            screen_w, screen_h = screen_size

        self._window_width, self._window_height = compute_window_size(
            maze_width=config.width,
            maze_height=config.height,
            desired_tile=self._settings.desired_tile_size,
            menu_min_w=MENU_MIN_WIDTH,
            menu_min_h=MENU_MIN_HEIGHT,
            screen_w=screen_w,
            screen_h=screen_h,
        )

        self._renderer = MlxRender(
            width=self._window_width,
            height=self._window_height,
            window_title=self._settings.window_title,
            on_action=self.handle_action,
        )

        self._menu = MenuScene(self._settings, self._theme)
        self._rebuild_maze()
        self._active: MenuScene | MazeScene = self._maze

    def _new_generator(self) -> MazeGenerator:
        """Build a MazeGenerator from config + the current runtime seed."""
        cfg = self._config
        return MazeGenerator(
            width=cfg.width,
            height=cfg.height,
            entry=cfg.entry,
            exit=cfg.exit,
            output_file=cfg.output_file,
            perfect=cfg.perfect,
            seed=self._settings.seed,
            algorithm=cfg.algorithm,
        )

    def _rebuild_maze(self) -> None:
        """New generator + interpreter+scene; next set_scene clears/redraws."""
        self._generator = self._new_generator()
        self._interpreter = MazeInterpreter(
            self._generator.grid,
            entry=self._config.entry,
            exit=self._config.exit,
            canvas_width=self._window_width,
            canvas_height=self._window_height,
            desired_tile_size=self._settings.desired_tile_size,
        )
        self._maze = MazeScene(
            self._generator,
            self._interpreter,
            self._settings,
            self._theme,
        )

    def handle_action(
        self,
        action: (
            ThemeChanged
            | IntervalChanged
            | SeedChanged
            | Regenerate
            | GoToMaze
            | GoToMenu
            | Quit
        ),
    ) -> None:
        """Apply scene actions; the only place that matches on action kinds."""
        if isinstance(action, ThemeChanged):
            self._settings = self._settings.with_theme(action.theme)
            self._theme = get_theme(action.theme)
            self._menu.update_settings(self._settings, self._theme)
            self._maze.update_settings(self._settings, self._theme)
        elif isinstance(action, IntervalChanged):
            self._settings = self._settings.with_interval(action.seconds)
            self._menu.update_settings(self._settings, self._theme)
            self._maze.update_settings(self._settings, self._theme)
        elif isinstance(action, SeedChanged):
            self._settings = self._settings.with_seed(action.seed)
            self._menu.update_settings(self._settings, self._theme)
            self._maze.update_settings(self._settings, self._theme)
        elif isinstance(action, Regenerate):
            self._rebuild_maze()
            self._active = self._maze
            self._renderer.set_scene(self._maze)
        elif isinstance(action, GoToMenu):
            self._active = self._menu
            self._renderer.set_scene(self._menu)
        elif isinstance(action, GoToMaze):
            if self._generator.seed != self._settings.seed:
                self._rebuild_maze()
            self._active = self._maze
            self._renderer.set_scene(self._maze)
        elif isinstance(action, Quit):
            self._renderer.request_quit()

    def run(self) -> None:
        """Initialize renderer, show the maze scene, enter the MLX loop."""
        self._renderer.initialize()
        self._active = self._maze
        self._renderer.set_scene(self._maze)
        self._renderer.run()


def load_config(path: str) -> Config:
    """Load maze settings from a config file path.

    Raises:
        FileNotFoundError: if ``path`` is missing or not a file.
        ValidationError: if required fields are missing or invalid.
    """
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    return Config(_env_file=str(config_path))


def main(argv: list[str] | None = None) -> int:
    """CLI entry: load config, wire App, run the MLX loop."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: a_maze_ing.py <config.txt>", file=sys.stderr)
        return 2

    path = args[0]
    try:
        config = load_config(path)
        app = App(config)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2
    except ValidationError as exc:
        print(f"Invalid config ({path}):\n{exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        # MazeGenerator model validation (bounds, entry/exit, pattern, …).
        print(f"Invalid maze settings: {exc}", file=sys.stderr)
        return 2

    print(
        "A-Maze-Ing "
        f"({config.width}x{config.height}, "
        f"window={app._window_width}x{app._window_height}, "
        f"entry={config.entry}, exit={config.exit}).",
        flush=True,
    )
    try:
        app.run()
    except RuntimeError as exc:
        print(f"Render error: {exc}", file=sys.stderr)
        return 1
    return 0
