"""In-memory MiniLibX image used as a framebuffer."""

from dataclasses import dataclass
from mlx import Mlx
from app.render.render_contract import Color


@dataclass
class Framebuffer:
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
        """Create the image via mlx_new_image and expose pixel memory.

        Store image_ptr, data addr, bits_per_pixel, size_line, image_format.
        Raise RuntimeError if creation fails.
        """
        try:
            self._image_ptr = mlx.mlx_new_image(mlx_ptr,
                                                self.width_px,
                                                self.height_px)
            if not self._image_ptr:
                raise RuntimeError("Failed to create framebuffer image")

            (self._image_data,
             self._bits_per_pixel,
             self._size_line,
             self._image_format) = mlx.mlx_get_data_addr(self._image_ptr)
            self._bytes_per_pixel = self._bits_per_pixel // 8
        except Exception as e:
            raise RuntimeError("Failed to initialize framebuffer") from e

    def release(self, mlx: Mlx, mlx_ptr: object) -> None:
        """Destroy the MiniLibX image and clear local references."""
        if self._image_ptr is None:
            return
        try:
            mlx.mlx_destroy_image(mlx_ptr=mlx_ptr, img_ptr=self._image_ptr)
            self._image_ptr = None
            self._image_data = None
            self._bits_per_pixel = 0
            self._size_line = 0
            self._image_format = 0
            self._bytes_per_pixel = 0
        except Exception as e:
            raise RuntimeError("Framebuffer image cannot be released") from e

    @property
    def image_ptr(self) -> object | None:
        """Return the underlying MiniLibX image pointer."""
        return self._image_ptr

    def fill_rect(
        self, x: int, y: int, width: int, height: int, color: Color
    ) -> None:
        """Fill a rectangle by writing whole pixel rows as byte slices.

        Respect image_format for channel order. Clip to the buffer bounds.
        Prefer row slices over per-pixel loops (see PoC pitfalls).
        """
        if self._image_format == 0:
            pixel = bytes((color.r, color.g, color.b, color.a))
        elif self._image_format == 1:
            pixel = bytes((color.a, color.b, color.g, color.r))
        else:
            raise RuntimeError("Image format not recognaized")

        if (self._image_data is None):
            return
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + width, self.width_px)
        y1 = min(y + height, self.height_px)
        x_width = x1 - x0
        slice_width = x_width * self._bytes_per_pixel
        for row in range(y0, y1):
            offset = row * self._size_line + x0 * self._bytes_per_pixel
            self._image_data[offset: offset + slice_width] = pixel * x_width

    def clear(self, color: Color) -> None:
        """Fill the entire framebuffer with one colour."""
        self.fill_rect(0, 0, self.width_px, self.height_px, color)
