"""Deprecated PoC. Use app.render.mlx_render.MlxRender instead."""
import random
from dataclasses import dataclass
from typing import Sequence
from time import perf_counter
from mlx import Mlx


CellState = Sequence[int]


@dataclass(frozen=True)
class MazeState:
    """Temporary representation of the current maze state."""

    cells: Sequence[Sequence[CellState]]


class MlxRender():
    """Manage the MiniLibX window and display the current frame."""

    def __init__(self, maze: MazeState, tile_size: int = 32,
                 window_title: str = "A-Maze-Ing",
                 width: int = 0, height: int = 0) -> None:
        self._maze = maze
        self._tile_size = tile_size
        self.window_title = window_title
        self._width = width
        self._height = height
        self._is_initializening = False
        self._mlx = Mlx()
        self._mlx_ptr = None
        self._win_ptr = None
        self._frame_buffer: Framebuffer | None = None
        self._last_update = 0.0
        self._show_interval = 0.3
        self._hide_interval = 0.05
        self._column = 0
        self._row = 0
        self._reset_cell = False

    def _close_hook(self, dummy):
        """Ask MiniLibX to stop its event loop when the window is closed."""
        if self._mlx_ptr is not None:
            self._mlx.mlx_loop_exit(self._mlx_ptr)

    def _speed(self, keynum):
        match keynum:
            case 65361:
                self._show_interval -= 0.01
            case 65363:
                self._show_interval += 0.01

    def _initialize(self) -> None:
        """Create the MiniLibX connection, window, and framebuffer image."""
        if self._is_initializening:
            return
        try:
            self._is_initializening = True
            window_width = self._width * self._tile_size
            window_height = self._height * self._tile_size
            self._frame_buffer = Framebuffer(window_width, window_height)
            self._mlx_ptr = self._mlx.mlx_init()
            if not self._mlx_ptr:
                raise RuntimeError("Failed to initialize MiniLibX")
            self._win_ptr = self._mlx.mlx_new_window(self._mlx_ptr,
                                                     window_width,
                                                     window_height,
                                                     self.window_title)
            if not self._win_ptr:
                raise RuntimeError("Failed to create the MiniLibX window")

            self._mlx.mlx_clear_window(self._mlx_ptr, self._win_ptr)
            self._mlx.mlx_hook(self._win_ptr, 33, 0, self._close_hook, None)
            self._mlx.mlx_key_hook(self._win_ptr, self._speed, None)
            self._frame_buffer.initialize(self._mlx, self._mlx_ptr)
        except Exception as e:
            print(e)

    def render(self) -> None:
        """Start the event loop and update the displayed image."""
        try:
            self._initialize()
            self._mlx.mlx_loop_hook(self._mlx_ptr, self._on_loop,
                                    param=self._random_color())
            self._mlx.mlx_loop(self._mlx_ptr)
        finally:
            self.close()

    def _on_loop(self, color) -> None:
        """Update the framebuffer at regular intervals."""

        if not self._reset_cell and self._frame_buffer is not None:
            self.fill_cell(color, self._column, self._row)
            self._mlx.mlx_put_image_to_window(self._mlx_ptr,
                                              self._win_ptr,
                                              self._frame_buffer._image_ptr,
                                              0, 0)
            self._reset_cell = True

        now = perf_counter()
        if now - self._last_update < self._show_interval:
            return
        self._last_update = now

        if (self._frame_buffer is not None):
            self.fill_cell([0, 0, 0, 255], self._column, self._row)
            self._mlx.mlx_put_image_to_window(self._mlx_ptr, self._win_ptr,
                                              self._frame_buffer._image_ptr,
                                              0, 0)
        self._reset_cell = False

        if self._column < self._width - 1:
            self._column += 1
        elif self._row < self._height - 1:
            self._column = 0
            self._row += 1
        else:
            self._column = 0
            self._row = 0

    def close(self) -> None:
        """Release the framebuffer, window, and MiniLibX connection."""
        try:
            if self._frame_buffer is not None:
                self._frame_buffer.release(self._mlx, self._mlx_ptr)
                self._frame_buffer = None
        except Exception as e:
            print(e)
            print("Error to realease the frame buffer")

        try:
            if self._mlx_ptr is not None and self._win_ptr is not None:
                self._mlx.mlx_destroy_window(self._mlx_ptr, self._win_ptr)
                self._win_ptr = None
        except Exception as e:
            print(e)
            print("Error to destroy the window")

        try:
            if self._mlx_ptr is not None:
                self._mlx.mlx_release(self._mlx_ptr)
                self._mlx_ptr = None
        except Exception as e:
            print(e)
            print("Error to release the mlx instance")

        self._is_initializening = False

    def _random_color(self) -> list[int]:
        """Return a random opaque RGBA colour for the rendering test."""
        red = random.randrange(256)
        green = random.randrange(256)
        blue = random.randrange(256)
        alpha = 255
        return ([red, green, blue, alpha])

    def fill_cell(self, color: list[int], x: int = 0, y: int = 0) -> None:
        """Complete a cell in the framebuffer with the given RGBA colour."""
        pixel_x_init = x * self._tile_size
        pixel_y_init = y * self._tile_size
        for px_y in range(pixel_y_init, pixel_y_init + self._tile_size):
            for px_x in range(pixel_x_init, pixel_x_init + self._tile_size):
                self._frame_buffer.fill_px(color, px_x, px_y)

    def cell_in_range(self, x: int = 0, y: int = 0) -> bool:
        if (0 <= x < self._width and 0 <= y < self._height):
            return True
        return False


@dataclass
class Framebuffer():
    """Store an image in memory before sending it to the window."""

    width_px: int
    height_px: int
    _image_ptr: object | None = None
    _image_data: memoryview | None = None
    _bits_per_pixel: int = 0
    _bytes_per_pixel: int = 0
    _size_line: int = 0
    _image_format: int = 0

    def initialize(self, mlx: Mlx, mlx_ptr: object) -> None:
        """Create the image and expose its pixel memory."""
        self._image_ptr = mlx.mlx_new_image(mlx_ptr, self.width_px,
                                            self.height_px)

        if not self._image_ptr:
            raise RuntimeError("Failed to initialize the image")
        (self._image_data,
         self._bits_per_pixel,
         self._size_line,
         self._image_format) = mlx.mlx_get_data_addr(self._image_ptr)
        self._bytes_per_pixel = self._bits_per_pixel // 8

    def release(self, mlx: Mlx, mlx_ptr: object) -> None:
        """Destroy the MiniLibX image and clear its local references."""
        if self._image_ptr is not None:
            mlx.mlx_destroy_image(mlx_ptr, self._image_ptr)
            self._image_ptr = None
            self._image_data = None

    def fill_px(self, color: list[int], x: int = 0, y: int = 0) -> None:
        """Fill_px every pixel in the image with the given RGBA colour."""
        if self._image_format == 0:
            pixel = bytes((color[0], color[1], color[2], color[3]))
        elif self._image_format == 1:
            pixel = bytes((color[3], color[2], color[1], color[0]))
        else:
            raise RuntimeError("Image format not recognaized")

        if (self._image_data is None):
            return
        # offset = y * _size_line + x * _bytes_per_pixel
        px = y * self._size_line + x * self._bytes_per_pixel
        self._image_data[px:px + self._bytes_per_pixel] = pixel


def main() -> None:
    """Run a small colour-changing MiniLibX demonstration."""
    maze_state = MazeState(
        cells=[
            [
                [1, 0, 0, 1],
                [1, 1, 0, 0]
            ]
        ]
    )
    renderer = MlxRender(maze=maze_state, tile_size=32, width=50, height=50)
    renderer.render()


if __name__ == "__main__":
    main()
