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
)

from typing import Optional, Tuple
from pydantic import field_validator, PrivateAttr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated


class MazeGenerator(BaseSettings):
    """Validate, generate, and store the maze matrix."""
    width: int
    height: int
    entry: Annotated[Tuple[int, int], NoDecode]
    exit: Annotated[Tuple[int, int], NoDecode]
    output_file: Annotated[str, NoDecode]
    perfect: bool = True
    seed: Optional[int] = None
    algorithm: Optional[str] = None

    # Configuration that indicates which file read.
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",  # Ignores extra keys that are not on class.
    )

    rng: random.Random = PrivateAttr()
    grid: np.ndarray = PrivateAttr()
    blocked: frozenset[Coord] = PrivateAttr()

    def model_post_init(self, context) -> None:
        self.rng = random.Random(self.seed)
        self.grid = np.ndarray(np.full(
            (self.height, self.width), 15, dtype=np.uint8
        ))
        self.blocked: frozenset[Coord] = self._get_blocked_42()

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

    @model_validator(model="after")
    def maze_validation(self) -> None:
        """Validate the maze settings and initialize a fully walled grid."""

        if self.width < 2 or self.height < 2:
            raise ValueError("Dimensions must be at least 2x2")
        if not (0 <= self.entry[0] < self.width and
                0 <= self.entry[1] < self.height):
            raise ValueError("Entry is out of bounds")
        if not (0 <= self.exit[0] < self.width and 0 <= exit[1] < self.height):
            raise ValueError("Exit is out of bounds")
        if self.entry == self.exit:
            raise ValueError("Entry and exit cannot be the same")

    def init_generation_structures(self) -> tuple[
        np.ndarray, list[Coord]
    ]:
        """Create the visited-cell array and DFS stack for generation."""
        visited = np.zeros((self.height, self.width), dtype=bool)
        start_x, start_y = self.entry
        for bx, by in self.blocked:
            visited[by, bx] = True
        visited[start_y, start_x] = True
        stack: list[Coord] = [(start_x, start_y)]
        return visited, stack

#  If it does not fit will raise a message controlled on main
    @property
    def has_42(self) -> bool:
        return bool(self.blocked)

    def _get_blocked_42(self) -> frozenset[Coord]:
        if self.width < PATTERN_WIDTH + 2 or self.height < PATTERN_HEIGHT + 2:
            print("Warning Maze is too small for '42' pattern:"
                  "Generating without it!")
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
            raise ValueError("Entry or Exit colides with '42' pattern")
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
        self.grid[y1, x1] &= (0xFF ^ wall_current)
        self.grid[y2, x2] &= (0xFF ^ wall_neighbor)

    def generate_steps(self) -> Iterator[Step]:
        """Yield start, carve, and backtrack events.

        The events are produced by a depth-first search.
        """
        visited, stack = self.init_generation_structures()
        start_x, start_y = self.entry
        yield ("start", start_x, start_y, start_x, start_y)
        for bx, by in self.blocked:
            yield ("Blocked", bx, by, bx, by)
        while stack:
            current_x, current_y = stack[-1]
            neighbors = self._get_unvisited_neighbors(
                current_x, current_y, visited
            )
            if neighbors:
                next_x, next_y = self.rng.choice(neighbors)
                self._remove_wall(current_x, current_y, next_x, next_y)
                visited[next_y, next_x] = True
                stack.append((next_x, next_y))
                yield ("carve", current_x, current_y, next_x, next_y)
            else:
                dead_x, dead_y = stack.pop()
                yield ("backtrack", dead_x, dead_y, dead_x, dead_y)

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
        cells = BfsSolver(self.grid, self.entry, self.exit).path()
        return self._path_to_letters(cells)

    def export_to_file(self) -> str:
        """Serialize the maze and solution.

        Write the serialized maze to a file when an output path is set.
        """
        rows = ["".join(f"{int(c):X}" for c in row) for row in self.grid]
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
