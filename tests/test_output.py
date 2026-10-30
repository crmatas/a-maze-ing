import pytest
from mazegen.maze_generator import MazeGenerator


@pytest.fixture
def out(tmp_path):
    path = tmp_path / "maze.txt"
    maze = MazeGenerator(width=15, height=11, entry=(0, 0),
                         exit=(14, 10), seed=11, output_file=str(path))
    maze.generate()
    maze.export_to_file()
    return maze, path.read_text()


def test_ends_with_newline(out):
    _, raw = out
    assert raw.endswith("\n")
