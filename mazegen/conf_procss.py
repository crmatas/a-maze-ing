from dataclasses import dataclass
import configparser

""" With dataclass python generates automatically
    __init__"""


@dataclass
class Config:
    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None
    algorithm: str | None = None


def parse_coordinates(value: str) -> tuple[int, int]:
    """ Parse a coordinate str into a tuple of int """
    """x, y = value.split(",")
        if len(parts) != 2:
            raise ValueError  """
    try:
        x, y = int(parts[0].strip(), int(parts[1].strip()))
            return tuple[int(x), int(y)]
    except ValueError:
        raise ValueError(f"Invalid coordinates: {value}")


def load_config(filename: str) -> Config:
    parser = configparser.ConfigParser()
    try:
        with open(filename, "r", encoding="utf-8")as file:
            content = file.read()
    except OSError as error:
        raise ValueError(f"Cannot read configuration file {error}")
        # esto es un engaño porque no tenermos un archivo INI sino un txt
        # y estamos usando configparser
        content = "[maze]\n" + content
        # checks for required keys.
    required = {
        "width",
        "height",
        "entry",
        "exit",
        "output_file",
        "perfect",
    }
    missing = required - set(section.keys())
    if missing:
        raise ValueError(
            f"Missing required configuration keys {missing}"
        )
    # perfect is declare before bacause mypy error.
    perfect = section.getboolean("perfect")
    if perfect is None:
        raise ValueError("Invalid value for perfect")
    return Config(
        width=int(section["width"]),
        height=int(section["height"]),
        entry=parse_coordinates(section["entry"]),
        exit=parse_coordinates(section["exit"]),
        output_file=section["output_file"],
        perfect=perfect,
        seed=section.getint("seed", fallback=None),
        algorithm=section.get("algorithm", fallback=None),
    )
