import pytest
from pydantic import ValidationError
from app.parser.conf_procss_pydantic import Config


def test_config_with_default_values():
    config = Config(_env_file=None, width=20,
                    height=10, entry=(0, 0),
                    exit=(19, 9), output_file="maze.txt")
    assert config.width == 20
    assert config.height == 10
    assert config.entry == (0, 0)
    assert config.exit == (19, 9)
    assert config.output_file == "maze.txt"
    assert config.perfect is True
    assert config.seed is None
    assert config.algorithm is None


def test_config_invalid_width():
    for invalid_width in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=invalid_width,
                   height=10, entry=(0, 0),
                   exit=(19, 9), output_file="maze.txt")


def test_config_invalid_height():
    for invalid_height in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=invalid_height, entry=(0, 0),
                   exit=(19, 9), output_file="maze.txt")


def test_config_invalid_entry():
    for invalid_entry in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=invalid_entry,
                   exit=(19, 9), output_file="maze.txt")


def test_config_invalid_exit():
    for invalid_exit in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=(0, 0),
                   exit=invalid_exit, output_file="maze.txt")


def test_config_invalid_perfect():
    for invalid_perfect in ["invalid", None, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20,
                   height=10, entry=(0, 0), exit=(19, 9),
                   perfect=invalid_perfect, output_file="maze.txt")


def test_config_invalid_seed():
    for invalid_seed in ["invalid", 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20, height=10,
                   entry=(0, 0), exit=(19, 9), seed=invalid_seed,
                   output_file="maze.txt")


def test_config_invalid_algorithm():
    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm="",
                  output_file="maze.txt").algorithm is None

    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm="   ",
                  output_file="maze.txt").algorithm is None

    assert Config(_env_file=None, width=20, height=10,
                  entry=(0, 0), exit=(19, 9), algorithm=None,
                  output_file="maze.txt").algorithm is None

    assert Config(_env_file=None, width=20, height=10, entry=(0, 0),
                  exit=(19, 9), algorithm="algorithm  space",
                  output_file="maze.txt").algorithm == "algorithm space"

    for invalid_algorithm in [{"key": "value"}, 3.14]:
        with pytest.raises(ValidationError):
            Config(_env_file=None, width=20, height=10, entry=(0, 0),
                   exit=(19, 9), algorithm=invalid_algorithm,
                   output_file="maze.txt")


def test_config_file():
    config = Config(_env_file="config.txt")
    assert config.width == 20
    assert config.height == 15
    assert config.entry == (0, 0)
    assert config.exit == (19, 14)
    assert config.perfect is True
    assert config.output_file == "maze.txt"
    assert config.seed is None
    assert config.algorithm is None
