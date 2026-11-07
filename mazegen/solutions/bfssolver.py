from mazegen.solutions.solver import Solve
from collections import deque
from collections.abc import Iterator

from mazegen.constants import (
    Coord,
    SolveSteps,
)


class BfsSolver(Solve):
    """Breadth-first search: always finds the shortest path."""

    def steps(self) -> Iterator[SolveSteps]:
        # prev[cell] = cell we came from, None for entry
        prev: dict[Coord, Coord | None] = {self.entry: None}
        queue: deque[Coord] = deque([self.entry])
        while queue:
            cell = queue.popleft()
            x, y = cell
            yield ("visit", x, y)
            if cell == self.exit:
                break
            for nxt in self.open_neighbor(x, y):
                if nxt not in prev:
                    prev[nxt] = cell
                    queue.append(nxt)
        if self.exit not in prev:
            return                    # without path does not yield:"path"
        # goes back and emited in order
        path: list[Coord] = []
        cur: Coord | None = self.exit
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        for px, py in reversed(path):
            yield ("path", px, py)
