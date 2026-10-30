from mlx import Mlx

from app.render.framebuffer import Framebuffer
from app.render.render_contract import Color


def _pixel_bytes(frame: Framebuffer, color: Color) -> bytes:
    if frame._image_format == 0:
        return bytes((color.r, color.g, color.b, color.a))
    if frame._image_format == 1:
        return bytes((color.a, color.b, color.g, color.r))
    raise RuntimeError(f"Unexpected image format: {frame._image_format}")


def _pixel_at(frame: Framebuffer, x: int, y: int) -> bytes:
    bpp = frame._bytes_per_pixel
    offset = y * frame._size_line + x * bpp
    assert frame._image_data is not None
    return bytes(frame._image_data[offset:offset + bpp])


def _new_frame(width: int = 200, height: int = 150) -> tuple[Mlx,
                                                             object,
                                                             Framebuffer]:
    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    frame = Framebuffer(width, height)
    frame.initialize(mlx, mlx_ptr)
    return mlx, mlx_ptr, frame


def test_framebuffer():
    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    frame = Framebuffer(720, 1280)
    assert frame._image_ptr is None
    assert frame._image_data is None
    assert frame._bits_per_pixel == 0
    assert frame._bytes_per_pixel == 0
    assert frame._size_line == 0

    frame.initialize(mlx, mlx_ptr)
    assert isinstance(frame, Framebuffer)
    assert frame.width_px == 720
    assert frame.height_px == 1280
    assert frame._image_ptr is not None
    assert frame._image_data is not None
    assert frame._bits_per_pixel != 0
    assert frame._bytes_per_pixel != 0
    assert frame._size_line != 0


def test_fill_rect():
    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    frame = Framebuffer(720, 1280)
    frame.initialize(mlx, mlx_ptr)
    color = Color(255, 0, 0, 100)
    x = 10
    y = 10
    width = 100
    height = 100
    frame.fill_rect(x, y, width, height, color)
    bytes_per_pixel = frame._bytes_per_pixel
    pixel = bytes((color.r, color.g, color.b, color.a))
    last_row_offset = (y + height - 1) * frame._size_line + x * bytes_per_pixel
    next_row_offset = (y + height) * frame._size_line + x * bytes_per_pixel
    # check if the last row is filled
    assert (
        frame._image_data[
            last_row_offset:last_row_offset + width * bytes_per_pixel
        ]
        == pixel * width
    )
    # check if on the next row the first pixel is not filled
    assert (
        frame._image_data[next_row_offset:next_row_offset + bytes_per_pixel]
        != pixel
    )
    # check if the next row is not filled
    assert (
        frame._image_data[
            next_row_offset:next_row_offset + width * bytes_per_pixel
        ]
        != pixel * width
    )


def test_fill_rect_out_of_bounds():
    mlx = Mlx()
    mlx_ptr = mlx.mlx_init()
    frame = Framebuffer(720, 1280)
    frame.initialize(mlx, mlx_ptr)
    color = Color(255, 0, 0, 100)
    frame.fill_rect(10, 10, 720, 1281, color)
    bytes_per_pixel = frame._bytes_per_pixel
    pixel = bytes((color.r, color.g, color.b, color.a))
    out_of_bounds_offset = 1291 * frame._size_line + 10 * bytes_per_pixel
    real_offset = 1279 * frame._size_line + 10 * bytes_per_pixel
    # check if the last row using the out of bounds offset is not filled
    assert frame._image_data[out_of_bounds_offset:
                             out_of_bounds_offset +
                             10 * frame._bytes_per_pixel] != pixel * 10
    # check if the last row using the real offset is filled
    assert frame._image_data[real_offset:
                             real_offset +
                             10 * frame._bytes_per_pixel] == pixel * 10


def test_clear() -> None:
    mlx, mlx_ptr, frame = _new_frame()
    red = Color(255, 0, 0, 255)
    blue = Color(0, 0, 255, 255)
    frame.fill_rect(20, 20, 40, 40, red)
    frame.clear(blue)
    expected = _pixel_bytes(frame, blue)
    assert _pixel_at(frame, 0, 0) == expected
    assert _pixel_at(frame, 20, 20) == expected
    assert _pixel_at(frame, frame.width_px - 1,
                     frame.height_px - 1) == expected
    frame.release(mlx, mlx_ptr)


def test_release() -> None:
    mlx, mlx_ptr, frame = _new_frame()
    assert frame.image_ptr is not None
    frame.release(mlx, mlx_ptr)
    assert frame._image_ptr is None
    assert frame._image_data is None
    assert frame._bits_per_pixel == 0
    assert frame._bytes_per_pixel == 0
    assert frame._size_line == 0
    assert frame.image_ptr is None
    frame.release(mlx, mlx_ptr)  # second call must be a no-op


def test_fill_rect_negative_origin_clips() -> None:
    _, _, frame = _new_frame()
    color = Color(0, 255, 0, 255)
    expected = _pixel_bytes(frame, color)
    frame.fill_rect(-10, -5, 20, 15, color)
    assert _pixel_at(frame, 0, 0) == expected
    assert _pixel_at(frame, 9, 9) == expected
    # just outside the clipped rect (x goes 0..9, y 0..9)
    assert _pixel_at(frame, 10, 0) != expected


def test_fill_rect_empty_size_is_noop() -> None:
    _, _, frame = _new_frame()
    color = Color(255, 255, 0, 255)
    expected = _pixel_bytes(frame, color)
    frame.fill_rect(5, 5, 0, 10, color)
    frame.fill_rect(5, 5, 10, 0, color)
    assert _pixel_at(frame, 5, 5) != expected
