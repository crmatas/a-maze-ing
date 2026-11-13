"""Tests for MazeInterpreter (#52 / #53) — no MiniLibX."""

import numpy as np

from app.interpret.maze_interpreter import MazeInterpreter
from app.render.render_contract import FillRect
from app.runtime_settings import DESIRED_TILE_SIZE, MIN_USABLE_TILE_SIZE
from app.theme.catalog import default_theme
from mazegen.constants import EAST, NORTH, SOUTH, WEST


def _grid(cells: list[list[int]]) -> np.ndarray:
    return np.array(cells, dtype=np.uint8)


def _interp(
    grid: np.ndarray,
    *,
    canvas: tuple[int, int] = (320, 240),
    desired: int = DESIRED_TILE_SIZE,
    entry: tuple[int, int] = (0, 0),
    exit_: tuple[int, int] = (1, 0),
) -> MazeInterpreter:
    return MazeInterpreter(
        grid,
        entry=entry,
        exit=exit_,
        canvas_width=canvas[0],
        canvas_height=canvas[1],
        desired_tile_size=desired,
    )


def test_tile_fits_desired_when_canvas_allows() -> None:
    grid = _grid([[15, 15], [15, 15]])
    interp = _interp(grid, canvas=(480, 360), desired=24)
    assert interp.tile_size == 24
    assert interp.offset == (
        (480 - 2 * 24) // 2,
        (360 - 2 * 24) // 2,
    )


def test_tile_shrinks_to_fit_canvas() -> None:
    grid = _grid([[15] * 10 for _ in range(10)])
    interp = _interp(grid, canvas=(100, 100), desired=24)
    assert interp.tile_size == max(MIN_USABLE_TILE_SIZE, 100 // 10)
    assert interp.tile_size == 10


def test_apply_event_start_blocked_carve_backtrack() -> None:
    grid = _grid([[15, 15], [15, 15]])
    interp = _interp(grid)

    interp.apply_event(("start", 0, 0, 0, 0))
    assert interp._head == (0, 0)

    interp.apply_event(("blocked", 1, 1, 1, 1))
    assert (1, 1) in interp._pattern

    interp.apply_event(("carve", 0, 0, 1, 0))
    assert interp._head == (1, 0)
    assert (0, 0) in interp._trail

    interp.apply_event(("backtrack", 1, 0, 1, 0))
    assert interp._head is None
    assert (1, 0) in interp._trail


def test_reset_runtime_marks_clears_pattern_too() -> None:
    grid = _grid([[15]])
    interp = _interp(grid, exit_=(0, 0))
    interp.apply_event(("start", 0, 0, 0, 0))
    interp.apply_event(("blocked", 0, 0, 0, 0))
    interp.set_solution_cells([(0, 0)])
    interp.reset_runtime_marks()
    assert interp._head is None
    assert interp._trail == set()
    assert interp._pattern == set()
    assert interp._solution == set()


def test_commands_for_event_carve_repaints_both_cells() -> None:
    # Open corridor: remove EAST from (0,0) and WEST from (1,0)
    grid = _grid([[15 ^ EAST, 15 ^ WEST]])
    theme = default_theme()
    interp = _interp(grid, canvas=(48, 24), desired=24)

    draw = interp.commands_for_event(("carve", 0, 0, 1, 0), theme)
    origins = {(r.x, r.y) for r in draw.commands if isinstance(r, FillRect)}
    # At least floor origins for both cells
    ox, oy = interp.offset
    t = interp.tile_size
    assert (ox, oy) in origins
    assert (ox + t, oy) in origins
    assert draw.clear is None


def test_full_repaint_clears_with_background() -> None:
    grid = _grid([[15, 15], [15, 15]])
    theme = default_theme()
    interp = _interp(grid)
    draw = interp.full_repaint(theme)
    assert draw.clear == theme.background
    assert any(isinstance(c, FillRect) for c in draw.commands)


def test_cell_wall_bits_emit_wall_rects() -> None:
    grid = _grid([[NORTH | SOUTH | EAST | WEST]])
    theme = default_theme()
    interp = _interp(grid, canvas=(24, 24), desired=24, exit_=(0, 0))
    draw = interp.commands_for_cells([(0, 0)], theme)
    wall_rects = [c for c in draw.commands if c.color == theme.wall]
    assert len(wall_rects) == 4


def test_pattern_overlay_after_blocked_event() -> None:
    grid = _grid([[15]])
    theme = default_theme()
    interp = _interp(grid, canvas=(24, 24), desired=24, exit_=(0, 0))
    draw = interp.commands_for_event(("blocked", 0, 0, 0, 0), theme)
    assert any(c.color == theme.pattern for c in draw.commands)


def test_set_solution_cells_marks_solution_color() -> None:
    grid = _grid([[15]])
    theme = default_theme()
    interp = _interp(grid, canvas=(24, 24), desired=24, exit_=(0, 0))
    interp.set_solution_cells([(0, 0)])
    draw = interp.commands_for_cells([(0, 0)], theme)
    assert any(c.color == theme.solution for c in draw.commands)
