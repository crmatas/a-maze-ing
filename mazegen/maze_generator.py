from collections import deque
from collections.abc import Iterator
import numpy as np
import random

# Coordinate in (x, y) order.
Coord = tuple[int, int]
# Generation event: (type, source_x, source_y, destination_x, destination_y).
Step = tuple[str, int, int, int, int]

# Wall bitmasks, stored in each cell.
NORTH: int = 1  # 0b0001 (bit 0)
EAST: int = 2  # 0b0010 (bit 1)
SOUTH: int = 4  # 0b0100 (bit 2)
WEST: int = 8  # 0b1000 (bit 3)

# For each movement offset, map the source and neighboring cell walls.
WALL_DIRECTIONS: dict[tuple[int, int], tuple[int, int]] = {
    (0, -1): (NORTH, SOUTH),  # Move north; remove south from the neighbor.
    (1, 0): (EAST, WEST),  # Move east; remove west from the neighbor.
    (0, 1): (SOUTH, NORTH),  # Move south; remove north from the neighbor.
    (-1, 0): (WEST, EAST),  # Move west; remove east from the neighbor.
}

# Map movement offsets to letters used in the exported solution.
DIRECTION_LETTERS: dict[Coord, str] = {
    (0, -1): "N",
    (1, 0): "E",
    (0, 1): "S",
    (-1, 0): "W",
}


class MazeGenerator:
    """Validate, generate, and store the maze matrix."""

    def __init__(
        self,
        exit: Coord,
        output_file: str | None = None,
        perfect: bool = True,
        width: int | None = None,
        height: int | None = None,
        entry: Coord = (0, 0),
        seed: int | None = None,
        algorithm: str | None = None,
    ) -> None:
        """Validate the maze settings and initialize a fully walled grid."""

        if width is None or height is None or width < 2 or height < 2:
            raise ValueError("Dimensions must be at least 2x2")
        if not (0 <= entry[0] < width and 0 <= entry[1] < height):
            raise ValueError("Entry is out of bounds")
        if not (0 <= exit[0] < width and 0 <= exit[1] < height):
            raise ValueError("Exit is out of bounds")
        if entry == exit:
            raise ValueError("Entry and exit cannot be the same")

        self.exit = exit
        self.output_file = output_file
        self.perfect = perfect
        self.width = width
        self.height = height
        self.entry = entry
        self.seed = seed
        self.algorithm = algorithm
        # Keep random choices local to this maze instance.
        self.rng = random.Random(seed)
        self.grid: np.ndarray = np.full(
            (self.height, self.width), 15, dtype=np.uint8
        )

    def init_generation_structures(self) -> tuple[
        np.ndarray, list[Coord]
    ]:
        """Create the visited-cell array and DFS stack for generation."""
        visited = np.zeros((self.height, self.width), dtype=bool)
        start_x, start_y = self.entry
        visited[start_y, start_x] = True
        stack: list[Coord] = [(start_x, start_y)]
        return visited, stack

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

    def solve(self) -> str:
        """Return a shortest path from entry to exit using N/E/S/W letters."""
        prev: dict[Coord, tuple[Coord, str] | None] = {self.entry: None}
        queue: deque[Coord] = deque([self.entry])

        while queue:
            x, y = queue.popleft()
            if (x, y) == self.exit:
                break
            for (dx, dy), letter in DIRECTION_LETTERS.items():
                wall, _ = WALL_DIRECTIONS[(dx, dy)]
                if self.grid[y, x] & wall:
                    continue
                nxt = (x + dx, y + dy)
                if nxt not in prev:
                    prev[nxt] = ((x, y), letter)
                    queue.append(nxt)

        if self.exit not in prev:
            raise ValueError("Exit is not reachable from entry")

        path: list[str] = []
        cell = self.exit
        while True:
            link = prev[cell]
            if link is None:
                break
            cell, letter = link
            path.append(letter)
        return "".join(reversed(path))

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
            + self.solve() + "\n"
        )
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(content)
        return content
