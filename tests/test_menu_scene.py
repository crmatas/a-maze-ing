"""Tests for MenuScene (#20 / #46) — no MiniLibX."""

from app.render.render_contract import (
    Draw,
    GoToMaze,
    Idle,
    IntervalChanged,
    Key,
    Quit,
    SeedChanged,
    Text,
    ThemeChanged,
)
from app.runtime_settings import (
    DEFAULT_STEP_INTERVAL,
    INTERVAL_STEP,
    MAX_STEP_INTERVAL,
    MENU_MIN_HEIGHT,
    MENU_MIN_WIDTH,
    MIN_STEP_INTERVAL,
    RuntimeSettings,
    SEED_STEP,
)
from app.scenes.menu_scene import MenuOption, MenuScene, _CHAR_W, _LINE_H
from app.theme.catalog import default_theme, get_theme, next_theme_name


def _menu(
    settings: RuntimeSettings | None = None,
    theme_name: str | None = None,
) -> MenuScene:
    settings = settings or RuntimeSettings()
    theme = get_theme(theme_name) if theme_name else default_theme()
    scene = MenuScene(settings, theme)
    scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    return scene


def _texts(draw: Draw) -> list[Text]:
    return [c for c in draw.commands if isinstance(c, Text)]


def test_on_enter_clears_with_theme_background() -> None:
    theme = default_theme()
    scene = MenuScene(RuntimeSettings(), theme)
    draw = scene.on_enter(MENU_MIN_WIDTH, MENU_MIN_HEIGHT)
    assert isinstance(draw, Draw)
    assert draw.clear == theme.background
    labels = [t.content for t in _texts(draw)]
    assert any("Theme:" in c for c in labels)
    assert any("Speed:" in c for c in labels)
    assert any("Seed:" in c for c in labels)
    assert "Back to maze" in labels


def test_on_enter_centers_content_on_larger_canvas() -> None:
    scene = MenuScene(RuntimeSettings(), default_theme())
    draw = scene.on_enter(640, 480)
    texts = _texts(draw)
    assert texts
    content_width = max(len(t.content) * _CHAR_W for t in texts)
    content_height = len(MenuOption) * _LINE_H
    assert texts[0].x == (640 - content_width) // 2
    assert texts[0].y == (480 - content_height) // 2
    assert texts[1].y == texts[0].y + _LINE_H
    assert all(t.x == texts[0].x for t in texts)


def test_down_to_back_enter_goes_to_maze() -> None:
    scene = _menu()
    assert scene.on_key(Key.DOWN) is None
    assert scene.on_key(Key.DOWN) is None
    assert scene.on_key(Key.DOWN) is None
    assert scene._selected == MenuOption.BACK.value
    assert isinstance(scene.on_key(Key.ENTER), GoToMaze)


def test_enter_on_theme_does_nothing() -> None:
    scene = _menu()
    assert scene._selected == MenuOption.THEME.value
    assert scene.on_key(Key.ENTER) is None


def test_esc_quits() -> None:
    scene = _menu()
    assert isinstance(scene.on_key(Key.ESC), Quit)


def test_theme_left_right_emits_theme_changed() -> None:
    scene = _menu()
    expected = next_theme_name(scene._settings.theme_name, 1)
    action = scene.on_key(Key.RIGHT)
    assert isinstance(action, ThemeChanged)
    assert action.theme == expected

    expected_left = next_theme_name(scene._settings.theme_name, -1)
    action_left = scene.on_key(Key.LEFT)
    assert isinstance(action_left, ThemeChanged)
    assert action_left.theme == expected_left


def test_speed_left_right_emits_interval_changed() -> None:
    scene = _menu()
    scene.on_key(Key.DOWN)  # SPEED
    action = scene.on_key(Key.RIGHT)
    assert isinstance(action, IntervalChanged)
    assert action.seconds == DEFAULT_STEP_INTERVAL + INTERVAL_STEP

    action_left = scene.on_key(Key.LEFT)
    assert isinstance(action_left, IntervalChanged)
    assert action_left.seconds == DEFAULT_STEP_INTERVAL - INTERVAL_STEP


def test_seed_left_right_emits_seed_changed() -> None:
    scene = _menu(RuntimeSettings(seed=10))
    scene.on_key(Key.DOWN)
    scene.on_key(Key.DOWN)  # SEED
    action = scene.on_key(Key.RIGHT)
    assert isinstance(action, SeedChanged)
    assert action.seed == 10 + SEED_STEP

    scene.update_settings(
        scene._settings.with_seed(action.seed), scene._theme
    )
    action_left = scene.on_key(Key.LEFT)
    assert isinstance(action_left, SeedChanged)
    assert action_left.seed == 10


def test_speed_clamped_to_min_max() -> None:
    scene = _menu(RuntimeSettings(step_interval=MIN_STEP_INTERVAL))
    scene.on_key(Key.DOWN)
    action = scene.on_key(Key.LEFT)
    assert isinstance(action, IntervalChanged)
    assert action.seconds == MIN_STEP_INTERVAL
    assert action.seconds >= 0

    scene_hi = _menu(RuntimeSettings(step_interval=MAX_STEP_INTERVAL))
    scene_hi.on_key(Key.DOWN)
    action_hi = scene_hi.on_key(Key.RIGHT)
    assert isinstance(action_hi, IntervalChanged)
    assert action_hi.seconds == MAX_STEP_INTERVAL


def test_up_down_marks_dirty_then_tick_draws_then_idle() -> None:
    scene = _menu()
    assert isinstance(scene.on_tick(0.016), Idle)

    scene.on_key(Key.DOWN)
    draw = scene.on_tick(0.016)
    assert isinstance(draw, Draw)
    texts = _texts(draw)
    # SPEED row highlighted
    assert texts[MenuOption.SPEED.value].color == scene._theme.text_highlight
    assert texts[MenuOption.THEME.value].color == scene._theme.text

    assert isinstance(scene.on_tick(0.016), Idle)


def test_update_settings_marks_dirty_and_updates_labels() -> None:
    scene = _menu()
    assert isinstance(scene.on_tick(0.0), Idle)

    new_settings = scene._settings.with_theme("neon").with_interval(0.2)
    new_theme = get_theme("neon")
    scene.update_settings(new_settings, new_theme)

    draw = scene.on_tick(0.0)
    assert isinstance(draw, Draw)
    assert draw.clear == new_theme.background
    labels = [t.content for t in _texts(draw)]
    assert any("neon" in c for c in labels)
    assert any("0.2" in c for c in labels)
    assert isinstance(scene.on_tick(0.0), Idle)


def test_selection_wraps() -> None:
    scene = _menu()
    scene.on_key(Key.UP)
    assert scene._selected == MenuOption.BACK.value
    scene.on_key(Key.DOWN)
    assert scene._selected == MenuOption.THEME.value
