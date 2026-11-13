"""Tests for MlxRender (#19 / #27) — logic with stubs (no display).

## Manual checklist (when a display is available)

Run a short smoke e.g.`poetry run python -m app.render.smoke_menu` and verify:

1. Window opens at the expected size and title.
2. Closing the window (×) exits the loop cleanly (no hang / orphan process).
3. At least one filled rect and one text string are visible.
4. Esc from the menu triggers Quit / app exit path.
5. Text does not flicker wildly while Idle ticks run (FPS cap holds).
"""

from collections.abc import Callable
from time import perf_counter
from typing import Any

import pytest

from app.render.mlx_render import (
    MlxRender,
    _X11_KEYMAP,
    color_to_mlx_int,
)
from app.render.render_contract import (
    Color,
    Draw,
    FillRect,
    GoToMaze,
    GoToMenu,
    Idle,
    IntervalChanged,
    Key,
    Quit,
    Text,
    ThemeChanged,
)

_Action = ThemeChanged | IntervalChanged | GoToMaze | GoToMenu | Quit


class _FakeScene:
    """Minimal Scene double for keymap / tick / enter tests."""

    def __init__(
        self,
        tick_result: Draw | Idle | None = None,
        key_action: _Action | None = None,
    ) -> None:
        self.tick_result: Draw | Idle = (
            Idle() if tick_result is None else tick_result
        )
        self.key_action = key_action
        self.enter_sizes: list[tuple[int, int]] = []
        self.keys: list[Key] = []
        self.ticks: list[float] = []
        self.enter_draw = Draw(
            commands=[
                Text(0, 0, "enter", Color(255, 255, 255)),
            ],
            clear=Color(0, 0, 0),
        )

    def on_enter(self, canvas_width: int, canvas_height: int) -> Draw:
        self.enter_sizes.append((canvas_width, canvas_height))
        return self.enter_draw

    def on_tick(self, elapsed: float) -> Draw | Idle:
        self.ticks.append(elapsed)
        return self.tick_result

    def on_key(self, key: Key) -> _Action | None:
        self.keys.append(key)
        return self.key_action


class _StubFramebuffer:
    def __init__(self) -> None:
        self._image_ptr: object = object()
        self.clear_calls: list[Color] = []
        self.fill_rect_calls: list[dict[str, Any]] = []
        self.release_calls: list[tuple[object, object]] = []
        self.initialize_calls: list[tuple[object, object]] = []

    def initialize(self, mlx: object, mlx_ptr: object) -> None:
        self.initialize_calls.append((mlx, mlx_ptr))

    def clear(self, color: Color) -> None:
        self.clear_calls.append(color)

    def fill_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
    ) -> None:
        self.fill_rect_calls.append(
            {"x": x, "y": y, "width": width, "height": height, "color": color}
        )

    def release(self, mlx: object, mlx_ptr: object) -> None:
        self.release_calls.append((mlx, mlx_ptr))


class _StubMlx:
    def __init__(
        self,
        *,
        mlx_ptr: object | None = None,
        win_ptr: object | None = None,
        screen: tuple[int, int, int] = (0, 1920, 1080),
        fail_init: bool = False,
        fail_window: bool = False,
    ) -> None:
        self._mlx_ptr = object() if mlx_ptr is None else mlx_ptr
        self._win_ptr = object() if win_ptr is None else win_ptr
        self._screen = screen
        self._fail_init = fail_init
        self._fail_window = fail_window
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self.calls.append((name, args, kwargs))

    def mlx_init(self) -> object | None:
        self._record("mlx_init")
        return None if self._fail_init else self._mlx_ptr

    def mlx_get_screen_size(self, mlx_ptr: object) -> tuple[int, int, int]:
        self._record("mlx_get_screen_size", mlx_ptr)
        return self._screen

    def mlx_new_window(
        self,
        mlx_ptr: object,
        width: int,
        height: int,
        title: str,
    ) -> object | None:
        self._record("mlx_new_window", mlx_ptr, width, height, title)
        return None if self._fail_window else self._win_ptr

    def mlx_clear_window(self, mlx_ptr: object, win_ptr: object) -> None:
        self._record("mlx_clear_window", mlx_ptr, win_ptr)

    def mlx_key_hook(
        self, win_ptr: object, hook: object, param: object
    ) -> None:
        self._record("mlx_key_hook", win_ptr, hook, param)

    def mlx_hook(
        self,
        win_ptr: object,
        event: int,
        mask: int,
        hook: object,
        param: object,
    ) -> None:
        self._record("mlx_hook", win_ptr, event, mask, hook, param)

    def mlx_put_image_to_window(
        self,
        mlx_ptr: object,
        win_ptr: object,
        image_ptr: object,
        x: int,
        y: int,
    ) -> None:
        self._record(
            "mlx_put_image_to_window", mlx_ptr, win_ptr, image_ptr, x, y
        )

    def mlx_string_put(
        self,
        mlx_ptr: object,
        win_ptr: object,
        x: int,
        y: int,
        color: int,
        string: str,
    ) -> None:
        self._record(
            "mlx_string_put",
            mlx_ptr=mlx_ptr,
            win_ptr=win_ptr,
            x=x,
            y=y,
            color=color,
            string=string,
        )

    def mlx_loop_exit(self, mlx_ptr: object) -> None:
        self._record("mlx_loop_exit", mlx_ptr)

    def mlx_destroy_window(self, mlx_ptr: object, win_ptr: object) -> None:
        self._record("mlx_destroy_window", mlx_ptr, win_ptr)

    def mlx_release(self, mlx_ptr: object) -> None:
        self._record("mlx_release", mlx_ptr)

    def names(self) -> list[str]:
        return [name for name, _, _ in self.calls]


def _wired_renderer(
    on_action: Callable[..., None] | None = None,
    max_fps: float = 0.0,
) -> tuple[MlxRender, _StubMlx, _StubFramebuffer]:
    """Build an initialized-looking renderer with stub MLX + FB."""
    renderer = MlxRender(320, 240, on_action=on_action, max_fps=max_fps)
    mlx = _StubMlx()
    fb = _StubFramebuffer()
    renderer._mlx = mlx
    renderer._mlx_ptr = mlx._mlx_ptr
    renderer._win_ptr = mlx._win_ptr
    renderer._frame_buffer = fb  # type: ignore[assignment]
    renderer._initialized = True
    renderer._last_paint = 0.0
    renderer._last_tick = 0.0
    return renderer, mlx, fb


def test_color_to_mlx_int_packs_rgb() -> None:
    assert color_to_mlx_int(Color(0x12, 0x34, 0x56, 0x78)) == 0x123456
    assert color_to_mlx_int(Color(255, 0, 0)) == 0xFF0000
    assert color_to_mlx_int(Color(0, 255, 0)) == 0x00FF00
    assert color_to_mlx_int(Color(0, 0, 255)) == 0x0000FF


def test_init_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError, match="positive"):
        MlxRender(0, 240)
    with pytest.raises(ValueError, match="positive"):
        MlxRender(320, -1)


def test_x11_keymap_covers_arrows_enter_esc() -> None:
    assert _X11_KEYMAP[65362] is Key.UP
    assert _X11_KEYMAP[65364] is Key.DOWN
    assert _X11_KEYMAP[65361] is Key.LEFT
    assert _X11_KEYMAP[65363] is Key.RIGHT
    assert _X11_KEYMAP[65293] is Key.ENTER
    assert _X11_KEYMAP[65307] is Key.ESC
    assert _X11_KEYMAP[27] is Key.ESC
    assert _X11_KEYMAP[114] is Key.R
    assert _X11_KEYMAP[82] is Key.R
    assert _X11_KEYMAP[115] is Key.S
    assert _X11_KEYMAP[83] is Key.S


def test_key_hook_maps_and_forwards_action() -> None:
    actions: list[Any] = []
    scene = _FakeScene(key_action=Quit())
    renderer, _, _ = _wired_renderer(on_action=actions.append)
    renderer._scene = scene

    renderer._key_hook(65307, None)

    assert scene.keys == [Key.ESC]
    assert actions == [Quit()]


def test_key_hook_ignores_unknown_keysym() -> None:
    actions: list[Any] = []
    scene = _FakeScene(key_action=Quit())
    renderer, _, _ = _wired_renderer(on_action=actions.append)
    renderer._scene = scene

    renderer._key_hook(32, None)  # space — not in map

    assert scene.keys == []
    assert actions == []


def test_key_hook_skips_when_scene_returns_none() -> None:
    actions: list[Any] = []
    scene = _FakeScene(key_action=None)
    renderer, _, _ = _wired_renderer(on_action=actions.append)
    renderer._scene = scene

    renderer._key_hook(65293, None)

    assert scene.keys == [Key.ENTER]
    assert actions == []


def test_on_loop_skips_paint_on_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    scene = _FakeScene(tick_result=Idle())
    renderer, _, _ = _wired_renderer(max_fps=0.0)
    renderer._scene = scene
    painted: list[Draw] = []
    monkeypatch.setattr(renderer, "_paint", lambda draw,
                        **_kw: painted.append(draw))

    renderer._on_loop(None)

    assert len(scene.ticks) == 1
    assert painted == []


def test_on_loop_paints_on_draw(monkeypatch: pytest.MonkeyPatch) -> None:
    draw = Draw(commands=[], clear=Color(1, 2, 3))
    scene = _FakeScene(tick_result=draw)
    renderer, _, _ = _wired_renderer(max_fps=0.0)
    renderer._scene = scene
    painted: list[Draw] = []
    monkeypatch.setattr(renderer, "_paint", lambda d, **_kw: painted.append(d))

    renderer._on_loop(None)

    assert painted == [draw]


def test_on_loop_respects_fps_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    scene = _FakeScene(tick_result=Draw(commands=[]))
    renderer, _, _ = _wired_renderer(max_fps=30.0)
    renderer._scene = scene
    renderer._last_paint = perf_counter()
    painted: list[Draw] = []
    monkeypatch.setattr(renderer, "_paint", lambda d, **_kw: painted.append(d))

    renderer._on_loop(None)

    assert scene.ticks == []
    assert painted == []


def test_paint_order_rects_then_image_then_texts() -> None:
    renderer, mlx, fb = _wired_renderer()
    red = Color(255, 0, 0)
    white = Color(255, 255, 255)
    draw = Draw(
        commands=[
            FillRect(1, 2, 10, 10, red),
            Text(5, 5, "hi", white),
            FillRect(3, 4, 8, 8, red),
            Text(6, 6, "yo", white),
        ],
        clear=Color(0, 0, 0),
    )

    renderer._paint(draw)

    assert fb.clear_calls == [Color(0, 0, 0)]
    assert len(fb.fill_rect_calls) == 2
    assert mlx.names() == [
        "mlx_put_image_to_window",
        "mlx_string_put",
        "mlx_string_put",
    ]
    assert mlx.calls[1][2] == {
        "mlx_ptr": renderer._mlx_ptr,
        "win_ptr": renderer._win_ptr,
        "x": 5,
        "y": 5,
        "color": 0xFFFFFF,
        "string": "hi",
    }
    assert mlx.calls[2][2] == {
        "mlx_ptr": renderer._mlx_ptr,
        "win_ptr": renderer._win_ptr,
        "x": 6,
        "y": 6,
        "color": 0xFFFFFF,
        "string": "yo",
    }


def test_set_scene_clears_enters_and_paints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scene = _FakeScene()
    renderer, mlx, _ = _wired_renderer()
    painted: list[tuple[Draw, bool]] = []

    def capture_paint(
        draw: Draw, force_clear_window: bool = False
    ) -> None:
        painted.append((draw, force_clear_window))

    monkeypatch.setattr(renderer, "_paint", capture_paint)
    renderer.set_scene(scene)

    assert renderer._scene is scene
    assert scene.enter_sizes == [(320, 240)]
    assert mlx.names() == ["mlx_clear_window"]
    assert painted == [(scene.enter_draw, True)]


def test_close_hook_requests_quit(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer, _, _ = _wired_renderer()
    called: list[str] = []
    monkeypatch.setattr(
        renderer, "request_quit", lambda: called.append("quit")
    )
    renderer._close_hook(None)
    assert called == ["quit"]


def test_request_quit_calls_loop_exit() -> None:
    renderer, mlx, _ = _wired_renderer()
    renderer.request_quit()
    assert mlx.calls == [("mlx_loop_exit", (renderer._mlx_ptr,), {})]


def test_initialize_wires_hooks_and_framebuffer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mlx = _StubMlx()
    fb = _StubFramebuffer()
    monkeypatch.setattr("app.render.mlx_render.Mlx", lambda: mlx)
    monkeypatch.setattr(
        "app.render.mlx_render.Framebuffer",
        lambda width, height: fb,
    )

    renderer = MlxRender(100, 80, window_title="t")
    renderer.initialize()

    assert renderer._initialized is True
    assert renderer.screen_width == 1920
    assert renderer.screen_height == 1080
    assert fb.initialize_calls == [(mlx, mlx._mlx_ptr)]
    assert "mlx_key_hook" in mlx.names()
    assert (
        "mlx_hook",
        (mlx._win_ptr, 33, 0, renderer._close_hook, None),
        {},
    ) in mlx.calls


def test_close_releases_framebuffer_window_and_mlx() -> None:
    renderer, mlx, fb = _wired_renderer()
    mlx_ptr = renderer._mlx_ptr
    win_ptr = renderer._win_ptr

    renderer.close()

    assert fb.release_calls == [(mlx, mlx_ptr)]
    assert ("mlx_destroy_window", (mlx_ptr, win_ptr), {}) in mlx.calls
    assert ("mlx_release", (mlx_ptr,), {}) in mlx.calls
    assert renderer._initialized is False
    assert renderer._frame_buffer is None
    assert renderer._win_ptr is None
    assert renderer._mlx_ptr is None
