"""MiniLibX window owner: pixels in, logical keys out, actions forwarded."""

from time import perf_counter
from mlx import Mlx
from app.render.framebuffer import Framebuffer
from app.render.render_contract import (Color, Draw, Idle, FillRect,
                                        Text, Key, Scene)
from app.runtime_settings import (
    FALLBACK_MAX_HEIGHT,
    FALLBACK_MAX_WIDTH,
    TARGET_MAX_FPS,
)

# Fill with X11 keysyms -> Key (never scatter magic numbers in hooks).
# Hint: arrows are often 65361..65364; Esc 65307 / 27; Return 65293.
_X11_KEYMAP: dict[int, Key] = {
    65362: Key.UP,
    65364: Key.DOWN,
    65361: Key.LEFT,
    65363: Key.RIGHT,
    65293: Key.ENTER,
    65307: Key.ESC,
    27: Key.ESC,
}


def color_to_mlx_int(color: Color) -> int:
    """Pack a Color into the uint expected by mlx_string_put (0x00RRGGBB)."""
    return (color.r << 16) | (color.g << 8) | color.b


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

        self._mlx: Mlx | None = None
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
        """Create MLX connection, one window, framebuffer; install hooks."""

        if self._initialized:
            return
        try:
            self._mlx = Mlx()
            self._mlx_ptr = self._mlx.mlx_init()
            if not self._mlx_ptr:
                raise RuntimeError("Error, failed to initialize MiniLibX")

            self._frame_buffer = Framebuffer(self._width, self._height)
            self._frame_buffer.initialize(self._mlx, self._mlx_ptr)
            (ret, self._screen_width, self._screen_height) = \
                self._mlx.mlx_get_screen_size(self._mlx_ptr)
            if ret != 0:
                self._screen_width = FALLBACK_MAX_WIDTH
                self._screen_height = FALLBACK_MAX_HEIGHT
            self._win_ptr = self._mlx.mlx_new_window(self._mlx_ptr,
                                                     self._width,
                                                     self._height,
                                                     self._window_title)
            if not self._win_ptr:
                raise RuntimeError("Error, failed to create the MLX window")

            self._mlx.mlx_clear_window(self._mlx_ptr, self._win_ptr)
            self._mlx.mlx_key_hook(self._win_ptr, self._key_hook, None)
            self._mlx.mlx_hook(self._win_ptr, 33, 0, self._close_hook, None)
            self._initialized = True
        except Exception as e:
            self._initialized = False
            self.close()
            raise RuntimeError("Error, failed to initialize Mlx") from e

    def set_scene(self, scene: Scene) -> None:
        """Activate a scene: clear window text + FB, then paint on_enter."""
        self._scene = scene
        self._mlx.mlx_clear_window(self._mlx_ptr, self._win_ptr)
        draw = scene.on_enter(self._width, self._height)
        self._paint(draw=draw, force_clear_window=True)
        self._last_tick = perf_counter()

    def run(self) -> None:
        """Install loop_hook, enter blocking mlx_loop, close() in finally."""
        if not self._initialized:
            self.initialize()
        self._mlx.mlx_loop_hook(self._mlx_ptr, self._on_loop, None)
        try:
            self._mlx.mlx_loop(self._mlx_ptr)
        finally:
            self.close()

    def request_quit(self) -> None:
        """Ask MiniLibX to leave its event loop (mlx_loop_exit)."""
        if self._mlx_ptr is not None:
            self._mlx.mlx_loop_exit(self._mlx_ptr)

    def close(self) -> None:
        """Release framebuffer, then window, then MLX connection."""
        try:
            if self._frame_buffer is not None:
                self._frame_buffer.release(self._mlx, self._mlx_ptr)
                self._frame_buffer = None
        except Exception as e:
            print(e)
            raise RuntimeError("Error, failed to realease the frame buffer")

        try:
            if self._mlx_ptr is not None and self._win_ptr is not None:
                self._mlx.mlx_destroy_window(self._mlx_ptr, self._win_ptr)
                self._win_ptr = None
        except Exception as e:
            print(e)
            raise RuntimeError("Error, failed to destroy the window")

        try:
            if self._mlx_ptr is not None:
                self._mlx.mlx_release(self._mlx_ptr)
                self._mlx_ptr = None
        except Exception as e:
            raise RuntimeError("Error, failed to release the mlx instance") \
                from e

        self._initialized = False

    def _close_hook(self, _dummy: object) -> None:
        """Window-close callback: request_quit."""
        self.request_quit()

    def _key_hook(self, keynum: int, _param: object) -> None:
        """Map raw key via _X11_KEYMAP; call scene.on_key; forward Action."""
        key = _X11_KEYMAP.get(keynum)
        if key is None or self._scene is None:
            return
        action = self._scene.on_key(key)
        if action is None or self._on_action is None:
            return
        self._on_action(action)

    def _on_loop(self, _param: object) -> None:
        """Compute elapsed, call scene.on_tick; skip paint on Idle/fps cap."""
        now = perf_counter()
        if now - self._last_paint < self._min_frame_interval:
            return
        elapsed = now - self._last_tick
        self._last_tick = now
        if self._scene is None:
            return
        result = self._scene.on_tick(elapsed)
        if isinstance(result, Idle):
            return
        self._paint(result)
        self._last_paint = now

    def _paint(self, draw: Draw, force_clear_window: bool = False) -> None:
        """Fixed order: clear?->FillRect to FB->put_image->Text on window."""
        if draw is None:
            return
        if draw.clear is not None:
            self._frame_buffer.clear(draw.clear)
        elif force_clear_window:
            self._mlx.mlx_clear_window(self._mlx_ptr, self._win_ptr)
        rect_cmd = [cmd for cmd in draw.commands if isinstance(cmd, FillRect)]
        txt_cmd = [cmd for cmd in draw.commands if isinstance(cmd, Text)]
        for cmd in rect_cmd:
            self._frame_buffer.fill_rect(x=cmd.x, y=cmd.y, width=cmd.width,
                                         height=cmd.height, color=cmd.color)
        self._mlx.mlx_put_image_to_window(self._mlx_ptr, self._win_ptr,
                                          self._frame_buffer._image_ptr,
                                          0, 0)

        for cmd in txt_cmd:
            color = color_to_mlx_int(cmd.color)
            self._mlx.mlx_string_put(mlx_ptr=self._mlx_ptr,
                                     win_ptr=self._win_ptr,
                                     x=cmd.x, y=cmd.y,
                                     color=color,
                                     string=cmd.content)


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
