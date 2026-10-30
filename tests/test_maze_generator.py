import pytest
import numpy as np

from mazegen.maze_generator import MazeGenerator


def test_maze_generator_with_valid_values():
    maze = MazeGenerator(
        exit=(9, 9),
        output_file="maze.txt",
        perfect=True,
        width=10,
        height=10,
        entry=(0, 0),
        seed=None,
        algorithm=None,
    )

    assert maze.width == 10
    assert maze.height == 10
    assert maze.entry == (0, 0)
    assert maze.exit == (9, 9)
    assert maze.output_file == "maze.txt"
    assert maze.perfect is True
    assert maze.seed is None
    assert maze.algorithm is None


def test_maze_generator_default_values():
    maze = MazeGenerator(
        exit=(9, 9),
        output_file="maze.txt",
        perfect=True,
        width=10,
        height=10,
    )

    assert maze.entry == (0, 0)
    assert maze.seed is None
    assert maze.algorithm is None


def test_maze_generator_invalid_width():
    for invalid_width in [0, 1]:
        with pytest.raises(ValueError):
            MazeGenerator(
                exit=(1, 1),
                output_file="maze.txt",
                perfect=True,
                width=invalid_width,
                height=10,
            )


def test_maze_generator_invalid_height():
    for invalid_height in [0, 1]:
        with pytest.raises(ValueError):
            MazeGenerator(
                exit=(1, 1),
                output_file="maze.txt",
                perfect=True,
                width=10,
                height=invalid_height,
            )


def test_maze_generator_invalid_entry():
    invalid_entries = [
        (-1, 0),
        (0, -1),
        (10, 0),
        (0, 10),
    ]

    for invalid_entry in invalid_entries:
        with pytest.raises(ValueError):
            MazeGenerator(
                exit=(9, 9),
                output_file="maze.txt",
                perfect=True,
                width=10,
                height=10,
                entry=invalid_entry,
            )


def test_maze_generator_invalid_exit():
    invalid_exits = [
        (-1, 0),
        (0, -1),
        (10, 0),
        (0, 10),
    ]

    for invalid_exit in invalid_exits:
        with pytest.raises(ValueError):
            MazeGenerator(
                exit=invalid_exit,
                output_file="maze.txt",
                perfect=True,
                width=10,
                height=10,
                entry=(0, 0),
            )


def test_maze_generator_entry_equals_exit():
    with pytest.raises(ValueError):
        MazeGenerator(
            exit=(5, 5),
            output_file="maze.txt",
            perfect=True,
            width=10,
            height=10,
            entry=(5, 5),
        )


def test_maze_generator_grid_initialization():
    maze = MazeGenerator(
        exit=(4, 4),
        output_file="maze.txt",
        perfect=True,
        width=5,
        height=5,
    )

    assert isinstance(maze.grid, np.ndarray)
    assert maze.grid.shape == (5, 5)
    assert maze.grid.dtype == np.uint8
    assert np.all(maze.grid == 15)
