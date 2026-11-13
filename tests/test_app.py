"""Tests for App wiring (#56 / #57) — no MiniLibX loop / no display.

``App(..., screen_size=...)`` skips ``probe_screen_size`` so CI stays headless.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

import numpy as np

from app.app import App, load_config, main
from app.render.render_contract import (
    GoToMaze,
    GoToMenu,
    IntervalChanged,
    PerfectChanged,
    Quit,
    Regenerate,
    SeedChanged,
    ThemeChanged,
)
from app.runtime_settings import MENU_MIN_HEIGHT, MENU_MIN_WIDTH
from app.scenes.maze_scene import MazeScene
from app.scenes.menu_scene import MenuScene
from app.theme.catalog import theme_names


def _write_tiny_config(tmp_path: Path) -> Path:
    path = tmp_path / "cfg.txt"
    path.write_text(
        "WIDTH = 2\n"
        "HEIGHT = 2\n"
        "ENTRY = 0,0\n"
        "EXIT = 1,1\n"
        "OUTPUT_FILE = out.txt\n"
        "PERFECT = True\n"
        "SEED = 1\n",
        encoding="utf-8",
    )
    return path


def _app(tmp_path: Path) -> App:
    config = load_config(str(_write_tiny_config(tmp_path)))
    return App(config, screen_size=(1920, 1080))


def test_load_config_reads_repo_config() -> None:
    config = load_config("config.txt")
    assert config.width == 20
    assert config.height == 15
    assert config.entry == (0, 0)
    assert config.exit == (19, 14)


def test_load_config_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_config("no_such_config.txt")


def test_load_config_invalid_contents_raise(tmp_path: Path) -> None:
    path = tmp_path / "bad.txt"
    path.write_text("WIDTH = nope\n", encoding="utf-8")
    with pytest.raises(ValidationError):
        load_config(str(path))


def test_main_reports_missing_config(capsys:
                                     pytest.CaptureFixture[str]) -> None:
    assert main(["missing_config.txt"]) == 2
    err = capsys.readouterr().err
    assert "not found" in err.lower()


def test_app_wires_window_scenes_and_shared_grid(tmp_path: Path) -> None:
    app = _app(tmp_path)
    assert app._window_width == MENU_MIN_WIDTH
    assert app._window_height == MENU_MIN_HEIGHT
    assert isinstance(app._menu, MenuScene)
    assert isinstance(app._maze, MazeScene)
    assert app._interpreter._grid is app._generator.grid
    assert app._active is app._menu


def test_handle_theme_and_interval_update_both_scenes(tmp_path: Path) -> None:
    app = _app(tmp_path)
    names = theme_names()
    other = names[1] if len(names) > 1 else names[0]
    app.handle_action(ThemeChanged(other))
    assert app._settings.theme_name == other
    assert app._theme.name == other
    assert app._menu._theme.name == other
    assert app._maze._theme.name == other

    app.handle_action(IntervalChanged(0.2))
    assert app._settings.step_interval == 0.2
    assert app._menu._settings.step_interval == 0.2
    assert app._maze._settings.step_interval == 0.2


def test_handle_go_to_menu_and_maze_switches_scene(tmp_path: Path) -> None:
    app = _app(tmp_path)
    switched: list[object] = []

    def capture_set_scene(scene: object) -> None:
        switched.append(scene)

    app._renderer.set_scene = capture_set_scene  # type: ignore[method-assign]

    app.handle_action(GoToMenu())
    assert switched[-1] is app._menu
    assert app._active is app._menu

    app.handle_action(GoToMaze())
    assert switched[-1] is app._maze
    assert app._active is app._maze


def test_regenerate_same_seed_replays_maze(tmp_path: Path) -> None:
    app = _app(tmp_path)
    app._generator.generate()
    first = app._generator.grid.copy()
    app._renderer.set_scene = lambda _scene: None  # type: ignore[method-assign]
    app.handle_action(Regenerate())
    maze = app._maze
    maze.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    for _ in range(50_000):
        maze.on_tick(0.01)
        if maze._done:
            break
    else:
        raise AssertionError("generation never finished")
    assert np.array_equal(first, app._generator.grid)
    assert app._generator.seed == app._settings.seed


def test_seed_change_rebuilds_on_go_to_maze(tmp_path: Path) -> None:
    app = _app(tmp_path)
    old = app._generator
    app.handle_action(SeedChanged(99))
    assert app._settings.seed == 99
    assert app._generator is old
    app._renderer.set_scene = lambda _scene: None  # type: ignore[method-assign]
    app.handle_action(GoToMaze())
    assert app._generator is not old
    assert app._generator.seed == 99


def test_perfect_change_rebuilds_on_go_to_maze(tmp_path: Path) -> None:
    app = _app(tmp_path)
    assert app._generator.perfect is True
    old = app._generator
    app.handle_action(PerfectChanged(False))
    assert app._settings.perfect is False
    assert app._generator is old
    app._renderer.set_scene = lambda _scene: None  # type: ignore[method-assign]
    app.handle_action(GoToMaze())
    assert app._generator is not old
    assert app._generator.perfect is False


def test_handle_quit_requests_renderer_exit(tmp_path: Path) -> None:
    app = _app(tmp_path)
    called: list[str] = []
    app._renderer.request_quit = (  # type: ignore[method-assign]
        lambda: called.append("quit")
    )
    app.handle_action(Quit())
    assert called == ["quit"]
