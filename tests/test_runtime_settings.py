from app.render.mlx_render import compute_window_size
from app.runtime_settings import (
    DEFAULT_STEP_INTERVAL,
    DEFAULT_THEME_NAME,
    DESIRED_TILE_SIZE,
    MAX_STEP_INTERVAL,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    MIN_STEP_INTERVAL,
    RuntimeSettings,
)


def test_intervals() -> None:
    rt = RuntimeSettings()
    assert rt.step_interval == DEFAULT_STEP_INTERVAL
    assert rt.theme_name == DEFAULT_THEME_NAME
    assert rt.desired_tile_size == DESIRED_TILE_SIZE
    assert rt.window_title == "A-Maze-Ing"

    rt = rt.with_interval(-1)
    assert rt.step_interval == MIN_STEP_INTERVAL
    rt = rt.with_interval(2)
    assert rt.step_interval == MAX_STEP_INTERVAL
    rt = rt.with_interval(0.5)
    assert rt.step_interval == 0.5


def test_theme_change() -> None:
    rt = RuntimeSettings()
    rt_v2 = rt.with_theme("test")
    assert rt_v2.theme_name == "test"
    assert rt.theme_name == DEFAULT_THEME_NAME


def test_compute_window_size_uses_ideal_when_between_menu_and_screen() -> None:
    # 20*24=480, 15*24=360 → between menu min and a large screen
    width, height = compute_window_size(
        maze_width=20,
        maze_height=15,
        desired_tile=DESIRED_TILE_SIZE,
        menu_min_w=MENU_MIN_WIDTH,
        menu_min_h=MENU_MIN_HEIGHT,
        screen_w=1920,
        screen_h=1080,
    )
    assert width == 20 * DESIRED_TILE_SIZE
    assert height == 15 * DESIRED_TILE_SIZE


def test_compute_window_size_raises_to_menu_minimum() -> None:
    # Ideal smaller than menu → clamp up to menu min
    width, height = compute_window_size(
        maze_width=2,
        maze_height=2,
        desired_tile=10,
        menu_min_w=MENU_MIN_WIDTH,
        menu_min_h=MENU_MIN_HEIGHT,
        screen_w=1920,
        screen_h=1080,
    )
    assert width == MENU_MIN_WIDTH

    assert height == MENU_MIN_HEIGHT


def test_compute_window_size_caps_to_screen() -> None:
    # Ideal larger than screen → clamp down to screen
    width, height = compute_window_size(
        maze_width=100,
        maze_height=100,
        desired_tile=DESIRED_TILE_SIZE,
        menu_min_w=MENU_MIN_WIDTH,
        menu_min_h=MENU_MIN_HEIGHT,
        screen_w=800,
        screen_h=600,
    )
    assert width == 800
    assert height == 600
