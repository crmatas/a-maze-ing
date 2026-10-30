import unittest

from mazegen.maze_generator import (
    MazeGenerator,
)
from mazegen.constants import (
    NORTH, EAST, SOUTH, WEST,
    PATTERN_42, PATTERN_WIDTH, PATTERN_HEIGHT, PATTERN_42_ASCII,
)

MOVES = [
    (0, -1, NORTH),
    (1, 0, EAST),
    (0, 1, SOUTH),
    (-1, 0, WEST),
]
OPPOSITE = {NORTH: SOUTH, EAST: WEST, SOUTH: NORTH, WEST: EAST}


def build(w: int, h: int, seed: int | None = None) -> MazeGenerator:
    """Laberinto w x h, entrada (0, 0) y salida en la esquina opuesta."""
    return MazeGenerator(
        width=w, height=h, entry=(0, 0), exit=(w - 1, h - 1), seed=seed
    )


def blocked_for(w: int, h: int) -> frozenset[tuple[int, int]]:
    """Celdas bloqueadas (patrón '42') de un laberinto w x h."""
    return build(w, h).blocked


class TestPattern42(unittest.TestCase):
    """Pruebas del patrón '42' y del conjunto de celdas bloqueadas."""

    ODD_SIZES = [(9, 7), (11, 9), (15, 11), (21, 15), (25, 25)]
    ALL_SIZES = ODD_SIZES + [(10, 8), (16, 12)]

    # --- El patrón en sí ---

    def test_pattern_is_rectangular_and_valid(self):
        self.assertEqual(len(PATTERN_42_ASCII), PATTERN_HEIGHT)
        for row in PATTERN_42_ASCII:
            self.assertEqual(len(row), PATTERN_WIDTH)
            self.assertTrue(set(row) <= {"X", "."})

    # --- Celdas bloqueadas ---

    def test_too_small_returns_empty_set(self):
        for w, h in [(8, 20), (20, 6), (5, 5), (2, 2)]:
            with self.subTest(size=(w, h)):
                self.assertEqual(blocked_for(w, h), set())

    def test_minimum_size_fits(self):
        maze = build(PATTERN_WIDTH + 2, PATTERN_HEIGHT + 2)
        self.assertTrue(maze.has_42)
        self.assertEqual(len(maze.blocked), len(PATTERN_42))

    def test_blocked_cells_inside_bounds_with_margin(self):
        for w, h in self.ALL_SIZES:
            with self.subTest(size=(w, h)):
                for x, y in blocked_for(w, h):
                    self.assertTrue(1 <= x <= w - 2)
                    self.assertTrue(1 <= y <= h - 2)

    def test_corners_never_blocked(self):
        for w, h in self.ALL_SIZES:
            with self.subTest(size=(w, h)):
                blocked = blocked_for(w, h)
                corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
                for corner in corners:
                    self.assertNotIn(corner, blocked)

    def test_center_free_for_odd_sizes(self):
        for w, h in self.ODD_SIZES:
            with self.subTest(size=(w, h)):
                self.assertNotIn((w // 2, h // 2), blocked_for(w, h))

    def test_blocked_is_deterministic(self):
        self.assertEqual(blocked_for(15, 11), blocked_for(15, 11))

    # --- Integración con MazeGenerator ---

    def test_generator_exposes_blocked_and_has_42(self):
        maze = build(15, 11)
        self.assertTrue(maze.has_42)
        self.assertEqual(maze.blocked, blocked_for(15, 11))

    def test_small_maze_has_no_42(self):
        maze = build(5, 5)
        self.assertFalse(maze.has_42)
        self.assertEqual(maze.blocked, set())

    def test_blocked_does_not_depend_on_seed(self):
        self.assertEqual(
            build(15, 11, seed=1).blocked,
            build(15, 11, seed=2).blocked,
        )

    def test_entry_or_exit_inside_pattern_raises(self):
        cell = min(blocked_for(15, 11))
        with self.assertRaises(ValueError):
            MazeGenerator(width=15, height=11, entry=cell, exit=(14, 10))
        with self.assertRaises(ValueError):
            MazeGenerator(width=15, height=11, entry=(0, 0), exit=cell)

    def test_blocked_cells_stay_fully_closed(self):
        maze = build(15, 11, seed=5)
        maze.generate()
        for x, y in maze.blocked:
            self.assertEqual(int(maze.grid[y, x]), 15)

    def test_free_cells_are_all_carved(self):
        maze = build(15, 11, seed=5)
        maze.generate()
        for y in range(maze.height):
            for x in range(maze.width):
                if (x, y) not in maze.blocked:
                    self.assertNotEqual(
                        int(maze.grid[y, x]), 15, f"({x},{y})"
                    )

    def test_neighbors_keep_wall_towards_blocked_cells(self):
        maze = build(15, 11, seed=5)
        maze.generate()
        for bx, by in maze.blocked:
            for dx, dy, wall in MOVES:
                nx, ny = bx + dx, by + dy
                if (nx, ny) in maze.blocked:
                    continue
                if not (0 <= nx < maze.width and 0 <= ny < maze.height):
                    continue
                self.assertTrue(int(maze.grid[ny, nx]) & OPPOSITE[wall])

    def test_all_free_cells_reachable_from_entry(self):
        maze = build(15, 11, seed=9)
        maze.generate()
        seen = {maze.entry}
        todo = [maze.entry]
        while todo:
            x, y = todo.pop()
            for dx, dy, wall in MOVES:
                nxt = (x + dx, y + dy)
                if not (maze.grid[y, x] & wall) and nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        self.assertEqual(
            len(seen), maze.width * maze.height - len(maze.blocked)
        )


if __name__ == "__main__":
    unittest.main()
