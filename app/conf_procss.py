from dataclasses import dataclass
from configparser import ConfigParser

""" With dataclass python generates automatically
    __init__"""


@dataclass
class Config:
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    width: int | None = None
    height: int | None = None
    entry: tuple[int, int] = (0, 0)
    seed: int | None = None
    algorithm: str | None = None


def parse_coordinates(value: str) -> tuple[int, int]:
    """ Parse a coordinate str into a tuple of int """
    """x, y = value.split(",")
        if len(parts) != 2:
            raise ValueError  """
    try:
        parts = value.split(",")
        x, y = int(parts[0].strip()), int(parts[1].strip())
        return (x, y)
    except ValueError:
        raise ValueError(f"Invalid coordinates: {value}")


def load_config(filename: str) -> Config:
    try:
        parser = ConfigParser()
        with open(filename, "r", encoding="utf-8")as file:
            parser.read_string("[maze]\n" + file.read())
    except OSError as error:
        raise ValueError(f"Cannot read configuration file {error}")
        # esto es un engaño porque no tenermos un archivo INI sino un txt
        # y estamos usando configparser
        # checks for required keys.
    required = {
        "width",
        "height",
        "entry",
        "exit",
        "output_file",
        "perfect",
    }
    configMaze = parser["maze"]
    missing = not required.issubset(set(configMaze.keys()))
    if missing:
        raise ValueError(
            f"Missing required configuration keys {missing}"
        )
    # perfect is declare before bacause mypy error.
    perfect = configMaze.getboolean("perfect")
    if perfect is None:
        raise ValueError("Invalid value for perfect")
    return Config(
        width=configMaze.getint("width"),
        height=configMaze.getint("height"),
        entry=parse_coordinates(configMaze["entry"]),
        exit=parse_coordinates(configMaze["exit"]),
        output_file=configMaze["output_file"],
        perfect=perfect,
        seed=configMaze.getint("seed", fallback=None),
        algorithm=configMaze.get("algorithm", fallback=None),
    )


if __name__ == "__main__":
    load_config("config.txt")
