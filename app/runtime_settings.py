"""Immutable runtime render settings owned by the app."""

from dataclasses import dataclass, replace

# Menu layout needs at least this canvas (pixels).
MENU_MIN_WIDTH = 320
MENU_MIN_HEIGHT = 240

# Ideal tile before the interpreter shrinks to fit.
DESIRED_TILE_SIZE = 24
MIN_USABLE_TILE_SIZE = 4

# Used only if mlx_get_screen_size fails.
FALLBACK_MAX_WIDTH = 1920
FALLBACK_MAX_HEIGHT = 1080

DEFAULT_THEME_NAME = "classic"
DEFAULT_STEP_INTERVAL = 0.05
MIN_STEP_INTERVAL = 0.01
MAX_STEP_INTERVAL = 1.0
INTERVAL_STEP = 0.01

TARGET_MAX_FPS = 30.0


@dataclass(frozen=True)
class RuntimeSettings:
    """Pure, immutable render configuration living only at runtime."""

    theme_name: str = DEFAULT_THEME_NAME
    step_interval: float = DEFAULT_STEP_INTERVAL
    desired_tile_size: int = DESIRED_TILE_SIZE
    window_title: str = "A-Maze-Ing"

    def with_theme(self, theme_name: str) -> "RuntimeSettings":
        """Return a copy with a different theme name."""
        return replace(self, theme_name=theme_name)

    def with_interval(self, seconds: float) -> "RuntimeSettings":
        """Return a copy with step_interval clamped to MIN/MAX_STEP_INTERVAL"""
        interval = max(MIN_STEP_INTERVAL, min(seconds, MAX_STEP_INTERVAL))
        return replace(self, step_interval=interval)
