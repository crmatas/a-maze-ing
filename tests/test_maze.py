import os
import tempfile
import unittest

import numpy as np

# Import the maze generator and its wall bitmasks.
from mazegen.maze_generator import MazeGenerator
from mazegen.constants import NORTH, SOUTH, WEST, EAST


class TestMazeGeneratorInitialization(unittest.TestCase):
    """Test validation performed during initialization."""

    def test_valid_initialization(self):
        maze = MazeGenerator(width=10, height=8, entry=(0, 0), exit=(9, 7))
        self.assertEqual(maze.width, 10)
        self.assertEqual(maze.height, 8)
        self.assertEqual(maze.entry, (0, 0))
        self.assertEqual(maze.exit, (9, 7))
        self.assertEqual(maze.grid.shape, (8, 10))
        self.assertTrue(np.all(maze.grid == 15))

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            MazeGenerator(width=1, height=5, entry=(0, 0), exit=(0, 1))
        with self.assertRaises(ValueError):
            MazeGenerator(width=5, height=1, entry=(0, 0), exit=(1, 0))

    def test_entry_out_of_bounds(self):
        with self.assertRaises(ValueError):
            MazeGenerator(width=5, height=5, entry=(5, 0), exit=(1, 1))
        with self.assertRaises(ValueError):
            MazeGenerator(width=5, height=5, entry=(-1, 0), exit=(1, 1))

    def test_exit_out_of_bounds(self):
        with self.assertRaises(ValueError):
            MazeGenerator(width=5, height=5, entry=(0, 0), exit=(5, 5))

    def test_entry_equals_exit(self):
        with self.assertRaises(ValueError):
            MazeGenerator(width=5, height=5, entry=(2, 2), exit=(2, 2))


class TestMazeGenerationLogic(unittest.TestCase):
    """Test maze generation and consistency between neighboring walls."""

    def test_generation_modifies_grid(self):
        maze = MazeGenerator(width=10, height=10, entry=(0, 0), exit=(9, 9))
        self.assertTrue(np.all(maze.grid == 15))
        maze.generate()
        self.assertFalse(np.all(maze.grid == 15))

    def test_seed_reproducibility(self):
        maze1 = MazeGenerator(
            width=12, height=12, entry=(0, 0), exit=(11, 11), seed=42
        )
        maze1.generate()
        maze2 = MazeGenerator(
            width=12, height=12, entry=(0, 0), exit=(11, 11), seed=42
        )
        maze2.generate()
        np.testing.assert_array_equal(maze1.grid, maze2.grid)

    def test_wall_coherence(self):
        """Verify that neighboring cells agree on their shared walls."""
        maze = MazeGenerator(
            width=8, height=8, entry=(0, 0), exit=(7, 7), seed=123
        )
        maze.generate()

        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.grid[y, x]

                # Check the eastern neighbor.
                if x + 1 < maze.width:
                    neighbor = maze.grid[y, x + 1]
                    has_east_wall = bool(cell & EAST)
                    has_west_wall = bool(neighbor & WEST)
                    self.assertEqual(
                        has_east_wall,
                        has_west_wall,
                        f"East/west wall mismatch at ({x}, {y})",
                    )

                # Check the southern neighbor.
                if y + 1 < maze.height:
                    neighbor = maze.grid[y + 1, x]
                    has_south_wall = bool(cell & SOUTH)
                    has_north_wall = bool(neighbor & NORTH)
                    self.assertEqual(
                        has_south_wall,
                        has_north_wall,
                        f"South/north wall mismatch at ({x}, {y})",
                    )

    def test_generate_steps_yielding(self):
        """Verify that generate_steps yields correctly shaped steps."""
        maze = MazeGenerator(
            width=5, height=5, entry=(0, 0), exit=(4, 4), seed=99
        )
        steps = list(maze.generate_steps())

        self.assertGreater(len(steps), 0)

        first_step = steps[0]
        self.assertEqual(first_step[0], "start")
        self.assertEqual(first_step[1:], (0, 0, 0, 0))

        carve_steps = [s for s in steps if s[0] == "carve"]
        self.assertGreater(len(carve_steps), 0)

        for step in steps:
            self.assertEqual(len(step), 5)
            self.assertIn(step[0], ("start", "carve", "backtrack"))


class TestMazeExporting(unittest.TestCase):
    """Test exporting a maze to a text file."""

    def test_export_to_file_content(self):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            maze = MazeGenerator(
                width=4, height=3, entry=(0, 0), exit=(3, 2),
                seed=7, output_file=tmp_path,
            )
            maze.generate()
            maze.export_to_file()

            self.assertTrue(os.path.exists(tmp_path))

            with open(tmp_path, "r", encoding="utf-8") as f:
                raw = f.read()
            file_lines = raw.splitlines()

            # Three map rows, a blank line, entry, exit, and the path.
            self.assertEqual(len(file_lines), 7)
            self.assertTrue(raw.endswith("\n"))
            self.assertEqual(file_lines[3], "")
            self.assertEqual(file_lines[4], "0,0")
            self.assertEqual(file_lines[5], "3,2")

            # Verify that each map row has the expected width and hex values.
            for row_line in file_lines[:3]:
                self.assertEqual(len(row_line), 4)
                for char in row_line:
                    self.assertIn(char.upper(), "0123456789ABCDEF")

            # Follow the path to the exit without crossing any walls.
            moves = {
                "N": (0, -1, NORTH),
                "E": (1, 0, EAST),
                "S": (0, 1, SOUTH),
                "W": (-1, 0, WEST),
            }
            x, y = maze.entry
            for step in file_lines[6]:
                dx, dy, wall = moves[step]
                self.assertFalse(maze.grid[y, x] & wall)
                x, y = x + dx, y + dy
            self.assertEqual((x, y), maze.exit)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
