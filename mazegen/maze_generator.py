import numpy as np

# Constants of bits
NORTH: int = 1  # 0b0001 (bit 0)
EAST: int = 2  # 0b0010 (bit 1)
SOUTH: int = 4  # 0b0100 (bit 2)
WEST: int = 8  # 0b100 (bit 3)


class MazeGenerator:
    """Validate, generate, and store the maze matrix."""

    def __init__(
        self,
        exit: tuple[int, int],
        output_file: str,
        perfect: bool,
        width: int | None = None,
        height: int | None = None,
        entry: tuple[int, int] = (0, 0),
        seed: int | None = None,
        algorithm: str | None = None,
    ) -> None:
        """Validate configuration and initialize the fully walled grid."""
        if width is None or height is None or width < 2 or height < 2:
            raise ValueError("Dimensions must be at least 2x2")
        if not (0 <= entry[0] < width and 0 <= entry[1] < height):
            raise ValueError("Entry is out of bounds")
        if not (0 <= exit[0] < width and 0 <= exit[1] < height):
            raise ValueError("Exit is out of bounds")
        if entry == exit:
            raise ValueError("Entry and exit cannot be the same")

        self.exit = exit
        self.output_file = output_file
        self.perfect = perfect
        self.width = width
        self.height = height
        self.entry = entry
        self.seed = seed
        self.algorithm = algorithm
        self.grid = np.full((self.height, self.width), 15, dtype=np.uint8)
