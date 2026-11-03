from mazegen.solutions.bfssolver import BfsSolver
from collections.abc import Iterator

import numpy as np

import random

from mazegen.constants import (
    Coord,
    Step,
    WALL_DIRECTIONS,
    PATTERN_HEIGHT,
    PATTERN_WIDTH,
    PATTERN_42,
    DIRECTION_LETTERS,
    EAST, SOUTH,
)

from typing import Optional, Tuple, Any
from pydantic import field_validator, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated


class MazeGenerator(BaseSettings):
    """Validate, generate, and store the maze matrix."""
    width: int
    height: int
    entry: Annotated[Tuple[int, int], NoDecode]
    exit: Annotated[Tuple[int, int], NoDecode]
    output_file: str
    perfect: bool = False
    seed: Optional[int] = None
    algorithm: Optional[str] = None

    # Configuration that indicates which file read.
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",  # Ignores extra keys that are not on class.
    )

    # intern atributes, grid and blocked with property to be used out.
    _rng: random.Random = PrivateAttr()
    _grid: np.ndarray = PrivateAttr()
    _blocked: frozenset[Coord] = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        self._rng = random.Random(self.seed)
        self._grid = np.full(
            (self.height, self.width), 15, dtype=np.uint8
        )
        self._blocked = self._get_blocked_42()

    @property
    def grid(self) -> np.ndarray:
        return self._grid

    @property
    def blocked(self) -> frozenset[Coord]:
        return self._blocked

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coords(cls, value):
        if isinstance(value, str):
            return tuple(map(int, value.split(",")))
        return value

    @field_validator("algorithm", mode="after")
    @classmethod
    def parse_algorithm(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value or value == "":
            return None
        value = " ".join(value.split())
        return value

    @model_validator(mode="after")
    def maze_validation(self) -> "MazeGenerator":
        """Validate the maze settings and initialize a fully walled grid."""

        if self.width < 2 or self.height < 2:
            raise ValueError("Dimensions must be at least 2x2")
        if not (0 <= self.entry[0] < self.width and
                0 <= self.entry[1] < self.height):
            raise ValueError("Entry is out of bounds")
        if not (0 <= self.exit[0] < self.width and
                0 <= self.exit[1] < self.height):
            raise ValueError("Exit is out of bounds")
        if self.entry == self.exit:
            raise ValueError("Entry and exit cannot be the same")
        return self

    def init_generation_structures(self) -> tuple[
        np.ndarray, list[Coord]
    ]:
        """Create the visited-cell array and DFS stack for generation."""
        visited = np.zeros((self.height, self.width), dtype=bool)
        start_x, start_y = self.entry
        for bx, by in self._blocked:
            visited[by, bx] = True
        visited[start_y, start_x] = True
        stack: list[Coord] = [(start_x, start_y)]
        return visited, stack

#  If it does not fit will raise a message controlled on main
    @property
    def has_42(self) -> bool:
        return bool(self._blocked)

    def _get_blocked_42(self) -> frozenset[Coord]:
        if self.width < PATTERN_WIDTH + 2 or self.height < PATTERN_HEIGHT + 2:
            return frozenset()
        #  Calculate the offset to center the pattern.
        offset_x = (self.width - PATTERN_WIDTH) // 2
        offset_y = (self.height - PATTERN_HEIGHT) // 2
        #  Create absolute coords: relative plus offset.abs
        blocked = {
            (x + offset_x, y + offset_y)
            for x, y in PATTERN_42
        }
        if self.entry in blocked or self.exit in blocked:
            raise ValueError("Entry or Exit collides with '42' pattern")
        return frozenset(blocked)

    def _get_unvisited_neighbors(
        self, x: int, y: int, visited: np.ndarray
    ) -> list[Coord]:
        """Return in-bounds neighboring cells that have not been visited."""
        neighbors: list[Coord] = []
        for dx, dy in WALL_DIRECTIONS:
            nx: int = x + dx
            ny: int = y + dy

            # Keep only in-bounds cells that are still unvisited.
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if not visited[ny, nx]:
                    neighbors.append((nx, ny))
        return neighbors

    def _remove_wall(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Remove the shared wall between two neighboring cells."""
        dx: int = x2 - x1
        dy: int = y2 - y1
        wall_current, wall_neighbor = WALL_DIRECTIONS[(dx, dy)]

        # NumPy indexes the grid as [row, column], or [y, x].
        self._grid[y1, x1] &= (0xFF ^ wall_current)
        self._grid[y2, x2] &= (0xFF ^ wall_neighbor)

    def _open_count(self, x: int, y: int) -> int:
        """Number of open sides of a cell."""
        return sum(
            1 for wall, _ in WALL_DIRECTIONS.values()
            if not int(self._grid[y, x]) & wall
        )

    def _dead_ends(self) -> list[Coord]:
        """Free cells with exactly one open side."""
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if (x, y) not in self._blocked and self._open_count(x, y) == 1
        ]

    def _add_wall(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Restore the shared wall between two neighboring cells."""
        wall_current, wall_neighbor = WALL_DIRECTIONS[(x2 - x1, y2 - y1)]
        self._grid[y1, x1] |= wall_current
        self._grid[y2, x2] |= wall_neighbor

    def _block_open(self, tx: int, ty: int) -> bool:
        """True if the 3x3 block with top-left (tx, ty) is fully open."""
        for j in range(3):
            for i in range(3):
                cell = int(self._grid[ty + j, tx + i])
                if i < 2 and cell & EAST:
                    return False
                if j < 2 and cell & SOUTH:
                    return False
        return True

    def _open_3x3_near(self, x: int, y: int) -> bool:
        """True if any 3x3 block containing (x, y) is fully open."""
        for ty in range(y - 2, y + 1):
            for tx in range(x - 2, x + 1):
                if (0 <= tx and tx + 2 < self.width
                        and 0 <= ty and ty + 2 < self.height
                        and self._block_open(tx, ty)):
                    return True
        return False

    def _braid(self) -> Iterator[Step]:
        """Remove walls at dead ends to create loops (non-perfect mode)."""
        dead_ends = self._dead_ends()
        self._rng.shuffle(dead_ends)
        for x, y in dead_ends:
            if self._open_count(x, y) != 1:
                continue    # a previous removal already fixed it
            options = [
                (x + dx, y + dy)
                for (dx, dy), (wall, _) in WALL_DIRECTIONS.items()
                if int(self._grid[y, x]) & wall
                and 0 <= x + dx < self.width
                and 0 <= y + dy < self.height
                and (x + dx, y + dy) not in self._blocked
            ]
            self._rng.shuffle(options)
            for nx, ny in options:
                self._remove_wall(x, y, nx, ny)
                if self._open_3x3_near(x, y) or self._open_3x3_near(nx, ny):
                    self._add_wall(x, y, nx, ny)    # undo
                    continue
                yield ("braid", x, y, nx, ny)
                break

    def generate_steps(self) -> Iterator[Step]:
        """Yield start, carve, and backtrack events.

        The events are produced by a depth-first search.
        """
        visited, stack = self.init_generation_structures()
        start_x, start_y = self.entry
        yield ("start", start_x, start_y, start_x, start_y)
        for bx, by in self._blocked:
            yield ("blocked", bx, by, bx, by)
        while stack:
            current_x, current_y = stack[-1]
            neighbors = self._get_unvisited_neighbors(
                current_x, current_y, visited
            )
            if neighbors:
                next_x, next_y = self._rng.choice(neighbors)
                self._remove_wall(current_x, current_y, next_x, next_y)
                visited[next_y, next_x] = True
                stack.append((next_x, next_y))
                yield ("carve", current_x, current_y, next_x, next_y)
            else:
                dead_x, dead_y = stack.pop()
                yield ("backtrack", dead_x, dead_y, dead_x, dead_y)
        if not self.perfect:
            yield from self._braid()

    def generate(self) -> None:
        """Generate the complete maze by consuming all generation events."""
        for _ in self.generate_steps():
            pass

    #  Two method that use solver to export file.
    def _path_to_letters(self, cells: list[Coord]) -> str:
        """ Converts path cells into direction letters """
        return "".join(
            DIRECTION_LETTERS[(x2 - x1, y2 - y1)]
            for (x1, y1), (x2, y2) in zip(cells, cells[1:])
        )

    def solution_letters(self) -> str:
        """ Shorter path entry to exit direction letters , (always BSF) """
        cells = BfsSolver(self._grid, self.entry, self.exit).path()
        return self._path_to_letters(cells)

    def export_to_file(self) -> str:
        """Serialize the maze and solution.

        Write the serialized maze to a file when an output path is set.
        """
        rows = ["".join(f"{int(c):X}" for c in row) for row in self._grid]
        entry_str = "{},{}".format(*self.entry)
        exit_str = "{},{}".format(*self.exit)
        content = (
            "\n".join(rows) + "\n\n"
            + entry_str + "\n"
            + exit_str + "\n"
            + self.solution_letters() + "\n"
        )
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(content)
        return content
