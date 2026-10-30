from abc import ABC, abstractmethod
from collections.abc import Iterator
import numpy as np

from mazegen.constants import (
    Coord,
    SolveSteps,
    WALL_DIRECTIONS,
)


class Solve(ABC):
    def __init__(
        self,
        grid: np.ndarray,
        entry: Coord,
        exit: Coord,
    ) -> None:

        self.grid = grid
        self.entry = entry
        self.exit = exit

    @abstractmethod
    def steps(self) -> Iterator[SolveSteps]:
        pass
    #  devolver el resultado de bfssolver que suele ser el mas corto.
    #  el subject no dice de tener que devolver el mas corto de cada algorihm

    def open_neighbor(self, x: int, y: int) -> Iterator:
        for (dx, dy), (wall, _) in WALL_DIRECTIONS.items():
            if not (int(self.grid[y, x]) & wall):
                yield (x + dx, y + dy)

    def path(self) -> list[Coord]:
        cells = [(x, y) for kind, x, y in self.steps() if kind == "path"]
        if not cells:
            raise ValueError("Exit can not be reached from entry")
        return cells
