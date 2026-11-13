"""Translate maze grid / generation events into pixel draw commands."""

from collections.abc import Iterable

import numpy as np

from app.render.render_contract import Color, Draw, FillRect, Text
from app.runtime_settings import MIN_USABLE_TILE_SIZE
from app.theme.theme import Theme
from mazegen.constants import EAST, NORTH, SOUTH, Step, WEST


class MazeInterpreter:
    """Bit masks + events + theme -> FillRect commands.

    Knows cells; does not touch MiniLibX.
    Computes tile size (fit canvas) and centering with margins.
    Cell paint: floor, walls, pattern, trail, head, entry, exit.
    Solution is a continuous path drawn after all cells so it is not
    covered by neighboring floors; entry/exit are redrawn on top.
    On backtrack: no cursor; mark left cells with trail colour.
    Pattern cells come from generation 'blocked' events, not the ctor.
    """

    def __init__(
        self,
        grid: np.ndarray,
        entry: tuple[int, int],
        exit: tuple[int, int],
        canvas_width: int,
        canvas_height: int,
        desired_tile_size: int,
        wall_thickness: int | None = None,
    ) -> None:
        """Bind to a live grid and fix geometry for this canvas.

        'desired_tile_size' is a preference: the real tile is shrunk so the
        whole maze fits, then clamped to 'MIN_USABLE_TILE_SIZE'. Offsets
        letterbox the maze when the canvas is larger than 'width*tile' /
        'height*tile'. Pattern is empty until 'blocked' events arrive.
        """
        # NumPy indexes [row, col] == [y, x].
        self._grid = grid
        self._height = int(grid.shape[0])
        self._width = int(grid.shape[1])
        self._entry = entry
        self._exit = exit
        self._canvas_w = canvas_width
        self._canvas_h = canvas_height
        self._desired_tile = desired_tile_size
        self._tile = max(
            MIN_USABLE_TILE_SIZE,
            min(
                desired_tile_size,
                canvas_width // self._width,
                canvas_height // self._height,
            ),
        )
        # Default ~1/8 of the tile so walls stay readable on small tiles.
        self._wall_thickness = (
            wall_thickness
            if wall_thickness is not None
            else max(1, self._tile // 8)
        )
        self._offset_x = (canvas_width - self._width * self._tile) // 2
        self._offset_y = (canvas_height - self._height * self._tile) // 2
        # Animation marks (not stored in the grid bitmasks).
        self._trail: set[tuple[int, int]] = set()
        self._head: tuple[int, int] | None = None
        self._solution: list[tuple[int, int]] = []
        self._pattern: set[tuple[int, int]] = set()

    @property
    def tile_size(self) -> int:
        """Resolved cell size in pixels after fit/clamp."""
        return self._tile

    @property
    def offset(self) -> tuple[int, int]:
        """Top-left pixel of cell (0, 0) on the canvas."""
        return self._offset_x, self._offset_y

    def reset_runtime_marks(self) -> None:
        """Drop trail, head, pattern and solution (grid walls stay as-is)."""
        self._trail = set()
        self._head = None
        self._solution = []
        self._pattern = set()

    def clear_generation_marks(self) -> None:
        """Drop trail/head after generation ends; keep pattern and solution."""
        self._trail = set()
        self._head = None

    def set_solution_cells(self, cells: Iterable[tuple[int, int]]) -> None:
        """Replace the ordered solution path (caller runs BfsSolver/path())."""
        self._solution = list(cells)

    def apply_event(self, event: Step) -> None:
        """Update animation marks from one 'generate_steps' event.

        Does not mutate the grid: the generator already carved/braided before
        yielding. Unknown kinds are ignored.

        - start: place head at entry
        - blocked: remember a pattern (42) cell for later paint
        - carve: trail at source, head at destination
        - braid: walls-only post-pass (perfect=False); do not move head/trail
        - backtrack: trail at left cell,clear head(no cursor while retreating)
        """
        kind, x1, y1, x2, y2 = event

        if kind == "start":
            self._head = (x1, y1)
        elif kind == "blocked":
            self._pattern.add((x1, y1))
        elif kind == "carve":
            self._trail.add((x1, y1))
            self._head = (x2, y2)
        elif kind == "braid":
            # Loop carving is not DFS motion; leave cursor/trail alone
            # (cleared on StopIteration with a full_repaint).
            return
        elif kind == "backtrack":
            self._trail.add((x1, y1))
            self._head = None

    def full_repaint(self, theme: Theme) -> Draw:
        """Redraw the whole maze and clear the canvas with 'theme.background'.

        Used on scene enter / theme change / resume from menu.
        """
        cells = [
            (x, y)
            for y in range(self._height)
            for x in range(self._width)
        ]
        draw = self.commands_for_cells(cells, theme)
        return Draw(commands=draw.commands, clear=theme.background)

    def commands_for_cells(
        self, cells: list[tuple[int, int]], theme: Theme
    ) -> Draw:
        """Paint 'cells', then the solution path, then entry/exit on top."""
        cmds: list[FillRect | Text] = []
        for x, y in cells:
            cmds.extend(self._cell_rects(x, y, theme))
        cmds.extend(self._solution_rects(theme))
        if self._solution:
            cmds.extend(self._cell_rects(*self._entry, theme))
            if self._exit != self._entry:
                cmds.extend(self._cell_rects(*self._exit, theme))
        return Draw(commands=cmds)

    def commands_for_event(self, event: Step, theme: Theme) -> Draw:
        """Apply 'event' then repaint only the cells it touched.

        Carve/braid touch two cells; start/blocked/backtrack touch one.
        """
        self.apply_event(event)
        kind, x1, y1, x2, y2 = event
        if kind in ("carve", "braid"):
            cells = [(x1, y1), (x2, y2)]
        else:
            cells = [(x1, y1)]
        return self.commands_for_cells(cells, theme)

    def _cell_origin(self, x: int, y: int) -> tuple[int, int]:
        """Canvas pixel of the top-left corner of cell (x, y)."""
        return (
            self._offset_x + x * self._tile,
            self._offset_y + y * self._tile,
        )

    def _solution_rects(self, theme: Theme) -> list[FillRect]:
        """FillRects along cell centers for the current solution path."""
        if not self._solution:
            return []

        tile = self._tile
        thick = max(2, tile // 4)
        half = thick // 2
        color = theme.solution
        cmds: list[FillRect] = []

        for i, (x, y) in enumerate(self._solution):
            left, top = self._cell_origin(x, y)
            cx = left + tile // 2
            cy = top + tile // 2
            cmds.append(FillRect(cx - half, cy - half, thick, thick, color))

            if i + 1 >= len(self._solution):
                break
            x2, y2 = self._solution[i + 1]
            left2, top2 = self._cell_origin(x2, y2)
            nx = left2 + tile // 2
            ny = top2 + tile // 2

            if cy == ny:
                cmds.append(
                    FillRect(
                        min(cx, nx) - half,
                        cy - half,
                        abs(nx - cx) + thick,
                        thick,
                        color,
                    )
                )
            elif cx == nx:
                cmds.append(
                    FillRect(
                        cx - half,
                        min(cy, ny) - half,
                        thick,
                        abs(ny - cy) + thick,
                        color,
                    )
                )
        return cmds

    def _cell_rects(self, x: int, y: int, theme: Theme) -> list[FillRect]:
        """Build layered FillRects for one cell.

        Order: floor -> walls -> pattern -> trail -> head -> entry -> exit.
        Solution is painted separately after all cells.
        """
        px, py = self._cell_origin(x, y)
        tile = self._tile
        wall = self._wall_thickness
        cell = (x, y)
        masks = int(self._grid[y, x])
        cmds = [FillRect(px, py, tile, tile, theme.cell_floor)]

        if masks & NORTH:
            cmds.append(FillRect(px, py, tile, wall, theme.wall))
        if masks & SOUTH:
            cmds.append(FillRect(px, py + tile - wall, tile, wall, theme.wall))
        if masks & WEST:
            cmds.append(FillRect(px, py, wall, tile, theme.wall))
        if masks & EAST:
            cmds.append(FillRect(px + tile - wall, py, wall, tile, theme.wall))

        # Keep overlays inside the wall strips.
        inset = min(wall, max(0, tile // 2 - 1))
        inner = tile - 2 * inset

        def overlay(color: Color) -> None:
            if inner > 0:
                cmds.append(
                    FillRect(px + inset, py + inset, inner, inner, color)
                )

        if cell in self._pattern:
            overlay(theme.pattern)
        if cell in self._trail:
            overlay(theme.trail)
        if cell == self._head:
            overlay(theme.head)
        if cell == self._entry:
            overlay(theme.entry)
        if cell == self._exit:
            overlay(theme.exit)

        return cmds
