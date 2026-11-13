
# Coordinate in (x, y) order.
Coord = tuple[int, int]
# Generation event: (type, source_x, source_y, destination_x, destination_y).
Step = tuple[str, int, int, int, int]
# Generation event: (type, x, y)
SolveSteps = tuple[str, int, int]

# Wall bitmasks, stored in each cell.
NORTH: int = 1  # 0b0001 (bit 0)
EAST: int = 2  # 0b0010 (bit 1)
SOUTH: int = 4  # 0b0100 (bit 2)
WEST: int = 8  # 0b1000 (bit 3)

# For each movement offset, map the source and neighboring cell walls.
WALL_DIRECTIONS: dict[tuple[int, int], tuple[int, int]] = {
    (0, -1): (NORTH, SOUTH),  # Move north; remove south from the neighbor.
    (1, 0): (EAST, WEST),  # Move east; remove west from the neighbor.
    (0, 1): (SOUTH, NORTH),  # Move south; remove north from the neighbor.
    (-1, 0): (WEST, EAST),  # Move west; remove east from the neighbor.
}

# Map movement offsets to letters used in the exported solution.
DIRECTION_LETTERS: dict[Coord, str] = {
    (0, -1): "N",
    (1, 0): "E",
    (0, 1): "S",
    (-1, 0): "W",
}

PATTERN_42_ASCII: list[str] = [
    "X...XXX",
    "X.....X",
    "XXX.XXX",
    "..X.X..",
    "..X.XXX",
]

#  Calculate the relative coordinate of PATTERN_42_ASCII.

PATTERN_42: frozenset[Coord] = frozenset(
    (x, y)
    for y, row in enumerate(PATTERN_42_ASCII)
    for x, char in enumerate(row)
    if char == "X"
)

PATTERN_HEIGHT: int = len(PATTERN_42_ASCII)
PATTERN_WIDTH: int = max(len(row) for row in PATTERN_42_ASCII)
PATTERN_CENTERED_COL: int = 3
