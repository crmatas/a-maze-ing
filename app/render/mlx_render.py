"""MiniLibX window owner: pixels in, logical keys out, actions forwarded."""

# from mlx import Mlx
from app.render.framebuffer import Framebuffer
from app.render.render_contract import Color, Draw, Key, Scene
from app.runtime_settings import (
    FALLBACK_MAX_HEIGHT,
    FALLBACK_MAX_WIDTH,
    TARGET_MAX_FPS,
)

# Fill with X11 keysyms -> Key (never scatter magic numbers in hooks).
# Hint: arrows are often 65361..65364; Esc 65307 / 27; Return 65293.
_X11_KEYMAP: dict[int, Key] = {}


def color_to_mlx_int(color: Color) -> int:
    """Pack a Color into the uint expected by mlx_string_put (0x00RRGGBB)."""
    raise NotImplementedError


class MlxRender:
    """Own MLX resources and drive the active scene once per tick.

    Does not know about maze cells, bit masks, or app navigation logic.
    One window created once; no sleep/threads inside the loop hook.
    """

    def __init__(
        self,
        width: int,
        height: int,
        window_title: str = "A-Maze-Ing",
        on_action: object | None = None,
        max_fps: float = TARGET_MAX_FPS,
    ) -> None:
        """Store size, title, action callback, and fps cap; init attributes.

        on_action is a callable(action) -> None provided by the app, or None.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Window size must be positive")
        self._width = width
        self._height = height
        self._window_title = window_title
        self._on_action = on_action
        self._min_frame_interval = 1.0 / max_fps if max_fps > 0 else 0.0

        self._mlx: object | None = None
        self._mlx_ptr: object | None = None
        self._win_ptr: object | None = None
        self._frame_buffer: Framebuffer | None = None
        self._scene: Scene | None = None

        self._last_tick = 0.0
        self._last_paint = 0.0
        self._screen_width = FALLBACK_MAX_WIDTH
        self._screen_height = FALLBACK_MAX_HEIGHT
        self._initialized = False

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def screen_width(self) -> int:
        """Display width from mlx_get_screen_size (or fallback)."""
        return self._screen_width

    @property
    def screen_height(self) -> int:
        """Display height from mlx_get_screen_size (or fallback)."""
        return self._screen_height

    def initialize(self) -> None:
        """Create MLX connection, one window, framebuffer; install hooks.

        Call mlx_get_screen_size after mlx_init. Propagate errors; do not
        swallow exceptions and continue with null pointers.
        """
        raise NotImplementedError

    def set_scene(self, scene: Scene) -> None:
        """Activate a scene: clear window text + FB, then paint on_enter."""
        raise NotImplementedError

    def run(self) -> None:
        """Install loop_hook, enter blocking mlx_loop, close() in finally."""
        raise NotImplementedError

    def request_quit(self) -> None:
        """Ask MiniLibX to leave its event loop (mlx_loop_exit)."""
        raise NotImplementedError

    def close(self) -> None:
        """Release framebuffer, then window, then MLX connection."""
        raise NotImplementedError

    def _close_hook(self, _dummy: object) -> None:
        """Window-close callback: request_quit."""
        raise NotImplementedError

    def _key_hook(self, keynum: int, _param: object) -> None:
        """Map raw key via _X11_KEYMAP; call scene.on_key; forward Action."""
        raise NotImplementedError

    def _on_loop(self, _param: object) -> None:
        """Compute elapsed, call scene.on_tick; skip paint on Idle/fps cap."""
        raise NotImplementedError

    def _paint(self, draw: Draw, force_clear_window: bool = False) -> None:
        """Fixed order: clear?->FillRect to FB->put_image->Text on window."""
        raise NotImplementedError


def compute_window_size(
    maze_width: int,
    maze_height: int,
    desired_tile: int,
    menu_min_w: int,
    menu_min_h: int,
    screen_w: int,
    screen_h: int,
) -> tuple[int, int]:
    """Clamp ideal maze window between menu minimum and screen maximum."""

    width = max(menu_min_w, maze_width * desired_tile)
    height = max(menu_min_h, maze_height * desired_tile)
    width = min(width, screen_w)
    height = min(height, screen_h)
    return (width, height)
