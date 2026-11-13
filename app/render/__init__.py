"""Pixel renderer: MiniLibX window owner and shared draw contract."""

from app.render.mlx_render import MlxRender, compute_window_size

__all__ = [
    "MlxRender",
    "compute_window_size",
]
