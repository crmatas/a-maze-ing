"""Tests for regenerate + solution toggle (#58 / #59) — no MiniLibX."""

from app.interpret.maze_interpreter import MazeInterpreter
from app.render.render_contract import Draw, Idle, Key, Regenerate
from app.runtime_settings import (
    DESIRED_TILE_SIZE,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    RuntimeSettings,
)
from app.scenes.maze_scene import MazeScene
from app.theme.catalog import default_theme
from mazegen.maze_generator import MazeGenerator


def _scene(seed: int = 1) -> tuple[MazeScene, MazeGenerator, MazeInterpreter]:
    gen = MazeGenerator(
        width=5,
        height=5,
        entry=(0, 0),
        exit=(4, 4),
        output_file="",
        perfect=True,
        seed=seed,
    )
    settings = RuntimeSettings(step_interval=0.01)
    theme = default_theme()
    interp = MazeInterpreter(
        gen.grid,
        entry=gen.entry,
        exit=gen.exit,
        canvas_width=MENU_MIN_WIDTH,
        canvas_height=MENU_MIN_HEIGHT,
        desired_tile_size=DESIRED_TILE_SIZE,
    )
    scene = MazeScene(gen, interp, settings, theme)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    return scene, gen, interp


def _drain(scene: MazeScene, limit: int = 50_000) -> None:
    for _ in range(limit):
        scene.on_tick(0.01)
        if scene._done:
            return
    raise AssertionError("generation never finished")


def test_r_returns_regenerate_action() -> None:
    scene, _, _ = _scene(seed=3)
    _drain(scene)
    assert isinstance(scene.on_key(Key.R), Regenerate)


def _drain_solution(scene: MazeScene, limit: int = 50_000) -> None:
    for _ in range(limit):
        if not scene._show_solution:
            return
        if scene._shown >= len(scene._path):
            return
        scene.on_tick(0.01)
    raise AssertionError("solution reveal never finished")


def test_s_toggles_solution_only_when_finished() -> None:
    scene, _, interp = _scene(seed=4)
    # While generating, S is ignored.
    assert scene.on_key(Key.S) is None
    assert interp._solution == []
    assert scene._show_solution is False

    _drain(scene)
    assert scene.on_key(Key.S) is None
    draw = scene.on_tick(0.0)
    assert isinstance(draw, Draw)
    assert scene._show_solution is True
    # First tick of reveal shows the entry cell only.
    assert interp._solution == [(0, 0)]
    _drain_solution(scene)
    assert len(interp._solution) >= 2
    assert interp._solution[0] == (0, 0)
    assert interp._solution[-1] == (4, 4)
    assert interp._solution == scene._path

    scene.on_key(Key.S)
    scene.on_tick(0.0)
    assert scene._show_solution is False
    assert interp._solution == []


def test_enter_also_toggles_solution_when_done() -> None:
    scene, _, interp = _scene(seed=5)
    _drain(scene)
    scene.on_key(Key.ENTER)
    scene.on_tick(0.0)
    assert scene._show_solution is True
    assert interp._solution
    _drain_solution(scene)
    assert interp._solution == scene._path


def test_solution_reveal_grows_one_cell_per_interval() -> None:
    scene, _, interp = _scene(seed=8)
    _drain(scene)
    scene.on_key(Key.S)
    scene.on_tick(0.0)
    assert len(interp._solution) == 1
    scene.on_tick(0.01)
    assert len(interp._solution) == 2
    assert interp._solution == scene._path[:2]


def test_r_while_generating_still_asks_regenerate() -> None:
    scene, _, _ = _scene(seed=6)
    scene.on_tick(0.01)
    assert scene._done is False
    assert isinstance(scene.on_key(Key.R), Regenerate)


def test_braid_does_not_move_head_or_trail() -> None:
    gen = MazeGenerator(
        width=8,
        height=8,
        entry=(0, 0),
        exit=(7, 7),
        output_file="",
        perfect=False,
        seed=1,
    )
    settings = RuntimeSettings(step_interval=0.01)
    theme = default_theme()
    interp = MazeInterpreter(
        gen.grid,
        entry=gen.entry,
        exit=gen.exit,
        canvas_width=MENU_MIN_WIDTH,
        canvas_height=MENU_MIN_HEIGHT,
        desired_tile_size=DESIRED_TILE_SIZE,
    )
    interp.apply_event(("start", 0, 0, 0, 0))
    interp.apply_event(("carve", 0, 0, 1, 0))
    head_before = interp._head
    trail_before = set(interp._trail)
    interp.apply_event(("braid", 2, 2, 3, 2))
    assert interp._head == head_before
    assert interp._trail == trail_before


def test_finish_clears_trail_and_head() -> None:
    scene, _, interp = _scene(seed=7)
    _drain(scene)
    assert scene._done is True
    assert interp._trail == set()
    assert interp._head is None
