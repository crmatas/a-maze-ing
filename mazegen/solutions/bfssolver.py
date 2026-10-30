from mazegen.solutions.solver import Solve
from collections import deque
from collections.abc import Iterator

from mazegen.constants import (
    Coord,
    WALL_DIRECTIONS,
    DIRECTION_LETTERS,
)


class BfsSolver(Solve):
    """Return a shortest path from entry to exit using N/E/S/W letters."""

    def steps(self) -> Iterator:
        prev: dict[Coord, tuple[Coord, str] | None] = {self.entry: None}
        queue: deque[Coord] = deque([self.entry])

        while queue:
            x, y = queue.popleft()
            if (x, y) == self.exit:
                break
            for (dx, dy), (wall, _) """ WALL_DIRECTIONS[(dx, dy)]
                if self.grid[y, x] & wall:
                    continue
                nxt = (x + dx, y + dy)
                if nxt not in prev:
                    prev[nxt] = ((x, y), letter)
                    queue.append(nxt)

        if self.exit not in prev:
            raise ValueError("Exit is not reachable from entry")
        cell = self.exit

    def open_neighbor(self, x: int, y: int) -> Iterator:
        for (dx, dy), (wall, _) in WALL_DIRECTIONS.items():
            if not (int(self.grid[y, x]) & wall):
                yield (x + dx, y + dy)

    def path(self) -> list[Coord]:
        cells = [(x, y) for kind, x, y in self.steps() if kind == "path"]
        if not cells:
            raise ValueError("Exit can not be reached from entry")
        return cells
