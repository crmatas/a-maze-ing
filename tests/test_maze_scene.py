"""Tests for MazeScene (#54 / #55) — no MiniLibX.

Uses a small seeded MazeGenerator plus the real MazeInterpreter so ticks
exercise interval pacing, Esc→GoToMenu, and suspend/resume of the iterator.
"""

from collections.abc import Iterator

import numpy as np

from app.interpret.maze_interpreter import MazeInterpreter
from app.render.render_contract import Draw, GoToMenu, Idle, Key
from app.runtime_settings import (
    DESIRED_TILE_SIZE,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    RuntimeSettings,
)
from app.scenes.maze_scene import MazeScene
from app.theme.catalog import default_theme, get_theme
from mazegen.constants import Step
from mazegen.maze_generator import MazeGenerator


class _CountingGenerator:
    """Wrap MazeGenerator to count generate_steps() calls (resume check)."""

    def __init__(self, inner: MazeGenerator) -> None:
        self._inner = inner
        self.calls = 0

    @property
    def grid(self) -> np.ndarray:
        return self._inner.grid

    def generate_steps(self) -> Iterator[Step]:
        self.calls += 1
        yield from self._inner.generate_steps()


def _make_generator(
    *,
    width: int = 4,
    height: int = 4,
    seed: int = 1,
) -> MazeGenerator:
    return MazeGenerator(
        width=width,
        height=height,
        entry=(0, 0),
        exit=(width - 1, height - 1),
        output_file="",
        perfect=True,
        seed=seed,
    )


def _scene(
    *,
    interval: float = 0.05,
    theme_name: str | None = None,
    counting: bool = False,
) -> tuple[MazeScene, _CountingGenerator | MazeGenerator, MazeInterpreter]:
    inner = _make_generator()
    wrapped: _CountingGenerator | None = (
        _CountingGenerator(inner) if counting else None
    )
    gen: _CountingGenerator | MazeGenerator = wrapped or inner
    settings = RuntimeSettings(step_interval=interval)
    theme = get_theme(theme_name) if theme_name else default_theme()
    interp = MazeInterpreter(
        inner.grid,
        entry=(0, 0),
        exit=(inner.width - 1, inner.height - 1),
        canvas_width=MENU_MIN_WIDTH,
        canvas_height=MENU_MIN_HEIGHT,
        desired_tile_size=DESIRED_TILE_SIZE,
    )
    scene = MazeScene(gen, interp, settings, theme)  # type: ignore[arg-type]
    return scene, gen, interp


def test_on_enter_returns_full_repaint_with_clear() -> None:
    scene, _, _ = _scene()
    theme = default_theme()
    scene._theme = theme
    draw = scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert isinstance(draw, Draw)
    assert draw.clear == theme.background
    assert draw.commands
    assert scene._started is True
    assert scene._steps is not None


def test_on_enter_starts_iterator_only_once() -> None:
    # generate_steps() bodies run on first next(), not on call — tick once.
    scene, gen, _ = _scene(counting=True, interval=0.05)
    assert isinstance(gen, _CountingGenerator)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    scene.on_tick(0.05)
    assert gen.calls == 1
    steps = scene._steps
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    scene.on_tick(0.05)
    assert gen.calls == 1
    assert scene._steps is steps


def test_on_tick_idle_before_interval() -> None:
    scene, _, _ = _scene(interval=0.10)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    result = scene.on_tick(0.05)
    assert isinstance(result, Idle)


def test_on_tick_draws_one_event_after_interval() -> None:
    scene, _, interp = _scene(interval=0.05)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert interp._head is None
    result = scene.on_tick(0.05)
    assert isinstance(result, Draw)
    assert result.clear is None
    # First generator event is start → head at entry.
    assert interp._head == (0, 0)


def test_on_tick_idle_when_finished() -> None:
    scene, _, _ = _scene(interval=0.01)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    # Drain the iterator.
    for _ in range(10_000):
        result = scene.on_tick(0.01)
        if scene._done:
            assert isinstance(result, Idle)
            break
    else:
        raise AssertionError("generation never finished")
    assert isinstance(scene.on_tick(1.0), Idle)


def test_esc_returns_go_to_menu() -> None:
    scene, _, _ = _scene()
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert isinstance(scene.on_key(Key.ESC), GoToMenu)


def test_other_keys_return_none() -> None:
    scene, _, _ = _scene()
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    for key in (Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT, Key.ENTER):
        assert scene.on_key(key) is None


def test_update_settings_applies_new_interval() -> None:
    scene, _, _ = _scene(interval=1.0)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert isinstance(scene.on_tick(0.05), Idle)
    scene.update_settings(
        RuntimeSettings(step_interval=0.05),
        default_theme(),
    )
    result = scene.on_tick(0.05)
    assert isinstance(result, Draw)


def test_reenter_preserves_generation_progress() -> None:
    scene, gen, interp = _scene(interval=0.05, counting=True)
    assert isinstance(gen, _CountingGenerator)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    scene.on_tick(0.05)  # start
    scene.on_tick(0.05)  # next event (blocked or carve)
    head_after = interp._head
    trail_after = set(interp._trail)

    # Simulate menu round-trip: Esc then set_scene again.
    assert isinstance(scene.on_key(Key.ESC), GoToMenu)
    redraw = scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert isinstance(redraw, Draw)
    assert gen.calls == 1
    assert interp._head == head_after
    assert interp._trail == trail_after
