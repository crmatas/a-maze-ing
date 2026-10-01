from dataclasses import dataclass


@dataclass
class Config:
    """Store the configuration parameters for the maze."""

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: int | None = None
    algorithm: str | None = None


def parse_coordinates(value: str) -> tuple[int, int]:
    """Parse coordinates in the format 'x,y'."""
    try:
        x, y = value.split(",")
        return int(x), int(y)
    except ValueError:
        raise ValueError(f"Invalid coordinates: {value}")


def load_config(filename: str) -> Config:
    """Load and validate the maze configuration."""

    values = {}

    try:
        with open(filename, "r") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()

                # Ignore empty lines and comments
                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    raise ValueError(
                        f"Invalid syntax on line {line_number}: {line}"
                    )

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                values[key] = value

    except FileNotFoundError:
        raise ValueError(f"Configuration file not found: {filename}")

    required = {
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
    }

    missing = required - values.keys()

    if missing:
        raise ValueError(
            f"Missing required configuration keys: {missing}"
        )

    try:
        width = int(values["WIDTH"])
        height = int(values["HEIGHT"])
        entry = parse_coordinates(values["ENTRY"])
        exit = parse_coordinates(values["EXIT"])
        perfect = values["PERFECT"].lower() == "true"
    except ValueError as error:
        raise ValueError(f"Invalid configuration: {error}")

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit=exit,
        output_file=values["OUTPUT_FILE"],
        perfect=perfect,
    )
