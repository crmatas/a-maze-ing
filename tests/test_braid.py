import pytest

from mazegen.constants import NORTH, EAST, SOUTH, WEST, WALL_DIRECTIONS
from mazegen.maze_generator import MazeGenerator

SIZES = [(15, 11), (16, 12), (21, 15), (30, 20)]
SEEDS = [1, 2, 3, 42]
MAX_DEAD_ENDS = 2   # el subject tolera un par; el ideal es 0


def build(w, h, seed=1, perfect=False, generate=True):
    maze = MazeGenerator(
        width=w, height=h, entry=(0, 0), exit=(w - 1, h - 1),
        seed=seed, perfect=perfect, output_file="",
    )
    if generate:
        maze.generate()
    return maze


# ---------- medidas independientes del generador ----------

def open_dirs(grid, x, y):
    return [
        (x + dx, y + dy)
        for (dx, dy), (wall, _) in WALL_DIRECTIONS.items()
        if not int(grid[y, x]) & wall
    ]


def free_cells(maze):
    return [
        (x, y)
        for y in range(maze.height)
        for x in range(maze.width)
        if (x, y) not in maze.blocked
    ]


def count_loops(maze):
    cells = free_cells(maze)
    edges = sum(len(open_dirs(maze.grid, x, y)) for x, y in cells) // 2
    return edges - len(cells) + 1


def dead_ends(maze):
    return [c for c in free_cells(maze)
            if len(open_dirs(maze.grid, *c)) == 1]


def is_connected(maze):
    seen = {maze.entry}
    todo = [maze.entry]
    while todo:
        x, y = todo.pop()
        for nxt in open_dirs(maze.grid, x, y):
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return len(seen) == len(free_cells(maze))


def has_open_3x3(maze):
    g = maze.grid
    for ty in range(maze.height - 2):
        for tx in range(maze.width - 2):
            horizontal = all(
                not int(g[ty + j, tx + i]) & EAST
                for j in range(3) for i in range(2)
            )
            vertical = all(
                not int(g[ty + j, tx + i]) & SOUTH
                for j in range(2) for i in range(3)
            )
            if horizontal and vertical:
                return True
    return False


def open_wall(grid, x1, y1, x2, y2):
    """Abre a mano la pared entre dos celdas vecinas (para armar rejillas)."""
    wall_a, wall_b = WALL_DIRECTIONS[(x2 - x1, y2 - y1)]
    grid[y1, x1] &= 0xFF ^ wall_a
    grid[y2, x2] &= 0xFF ^ wall_b


# ---------- el braid mejora el árbol del DFS ----------

@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("w,h", SIZES)
class TestBraidResult:
    def test_default_mode_runs_braid(self, w, h, seed):
        # perfect=False por defecto: el árbol deja de ser un árbol
        assert count_loops(build(w, h, seed)) >= 2

    def test_braid_creates_loops_where_perfect_has_none(self, w, h, seed):
        assert count_loops(build(w, h, seed, perfect=True)) == 0
        assert count_loops(build(w, h, seed, perfect=False)) >= 2

    def test_braid_reduces_dead_ends(self, w, h, seed):
        before = len(dead_ends(build(w, h, seed, perfect=True)))
        after = len(dead_ends(build(w, h, seed, perfect=False)))
        assert after < before

    def test_few_dead_ends(self, w, h, seed):
        found = dead_ends(build(w, h, seed))
        assert len(found) <= MAX_DEAD_ENDS, found

    def test_no_open_3x3(self, w, h, seed):
        assert not has_open_3x3(build(w, h, seed))

    def test_still_connected(self, w, h, seed):
        assert is_connected(build(w, h, seed))

    def test_blocked_cells_untouched(self, w, h, seed):
        m = build(w, h, seed)
        for x, y in m.blocked:
            assert int(m.grid[y, x]) == 15

    def test_borders_still_closed(self, w, h, seed):
        g = build(w, h, seed).grid
        for x in range(w):
            assert g[0, x] & NORTH
            assert g[h - 1, x] & SOUTH
        for y in range(h):
            assert g[y, 0] & WEST
            assert g[y, w - 1] & EAST

    def test_wall_coherence(self, w, h, seed):
        g = build(w, h, seed).grid
        for y in range(h):
            for x in range(w):
                if x + 1 < w:
                    assert bool(g[y, x] & EAST) == bool(g[y, x + 1] & WEST)
                if y + 1 < h:
                    assert bool(g[y, x] & SOUTH) == bool(g[y + 1, x] & NORTH)

    def test_corners_and_center_open(self, w, h, seed):
        m = build(w, h, seed)
        for x, y in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                     (w // 2, h // 2)]:
            assert (x, y) not in m.blocked
            assert int(m.grid[y, x]) != 15


# ---------- los pasos "braid" ----------

class TestBraidSteps:
    def test_braid_steps_only_in_non_perfect(self):
        np_kinds = {s[0] for s in build(15, 11, 1, generate=False)
                    .generate_steps()}
        p_kinds = {s[0] for s in build(15, 11, 1, perfect=True,
                                       generate=False).generate_steps()}
        assert "braid" in np_kinds
        assert "braid" not in p_kinds

    def test_braid_steps_come_after_dfs(self):
        kinds = [s[0] for s in build(15, 11, 1, generate=False)
                 .generate_steps()]
        first_braid = kinds.index("braid")
        assert "carve" not in kinds[first_braid:]
        assert "backtrack" not in kinds[first_braid:]

    def test_each_braid_step_is_between_neighbors(self):
        for kind, x1, y1, x2, y2 in build(
                15, 11, 2, generate=False).generate_steps():
            if kind == "braid":
                assert abs(x1 - x2) + abs(y1 - y2) == 1

    def test_each_braid_step_opens_a_closed_wall(self):
        # Reproduce el DFS y, antes de cada braid, la pared debía estar
        # cerrada; después, abierta en las dos celdas.
        m = build(15, 11, 3, generate=False)
        replay = m.grid.copy()
        replay[:] = 15
        braids = 0
        for kind, x1, y1, x2, y2 in m.generate_steps():
            if kind in ("carve", "braid"):
                wall_a, wall_b = WALL_DIRECTIONS[(x2 - x1, y2 - y1)]
                if kind == "braid":
                    assert replay[y1, x1] & wall_a
                    assert replay[y2, x2] & wall_b
                    braids += 1
                replay[y1, x1] &= 0xFF ^ wall_a
                replay[y2, x2] &= 0xFF ^ wall_b
        assert braids > 0
        assert (replay == m.grid).all()

    def test_braid_never_targets_blocked_cells(self):
        m = build(15, 11, 4, generate=False)
        for kind, x1, y1, x2, y2 in m.generate_steps():
            if kind == "braid":
                assert (x1, y1) not in m.blocked
                assert (x2, y2) not in m.blocked


# ---------- semilla ----------

@pytest.mark.parametrize("seed", SEEDS)
def test_braid_is_reproducible(seed):
    a = build(21, 15, seed)
    b = build(21, 15, seed)
    assert (a.grid == b.grid).all()


def test_braid_differs_between_seeds():
    assert not (build(21, 15, 1).grid == build(21, 15, 2).grid).all()


# ---------- _braid sobre rejillas hechas a mano ----------
# Estos tests llaman a un método privado (_braid): si lo mueves a
# braid.py, solo hay que cambiar la llamada.

def test_braid_closes_the_only_dead_end_of_a_snake():
    # Serpiente 4x2: (0,0)-(1,0)-(2,0)-(3,0)-(3,1)-(2,1)-(1,1)-(0,1)
    # Callejones: (0,0) y (0,1). Al unirlos queda 1 bucle y 0 callejones.
    m = build(4, 2, generate=False)
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (2, 1), (1, 1), (0, 1)]
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        open_wall(m.grid, x1, y1, x2, y2)
    assert sorted(dead_ends(m)) == [(0, 0), (0, 1)]
    assert count_loops(m) == 0

    steps = list(m._braid())

    assert len(steps) == 1
    assert dead_ends(m) == []
    assert count_loops(m) == 1


def test_braid_does_not_open_wall_that_makes_3x3():
    # 3x3 con todas las paredes internas abiertas salvo (0,0)-(1,0).
    # (0,0) es el único callejón (solo abre al sur), pero abrir su pared
    # este formaría un 3x3 abierto, así que el braid debe dejarlo.
    m = build(3, 3, generate=False)
    for y in range(3):
        for x in range(2):
            open_wall(m.grid, x, y, x + 1, y)
    for y in range(2):
        for x in range(3):
            open_wall(m.grid, x, y, x, y + 1)
    wall_a, wall_b = WALL_DIRECTIONS[(1, 0)]
    m.grid[0, 0] |= wall_a
    m.grid[0, 1] |= wall_b
    assert dead_ends(m) == [(0, 0)]

    steps = list(m._braid())

    assert steps == []
    assert m.grid[0, 0] & EAST          # la pared sigue puesta
    assert m.grid[0, 1] & WEST
    assert not has_open_3x3(m)


def test_braid_does_nothing_on_grid_without_dead_ends():
    m = build(4, 2, generate=False)
    for y in range(2):
        for x in range(3):
            open_wall(m.grid, x, y, x + 1, y)
    for x in range(4):
        open_wall(m.grid, x, 0, x, 1)
    before = m.grid.copy()
    assert list(m._braid()) == []
    assert (m.grid == before).all()
