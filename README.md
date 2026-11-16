*This project has been created as part of the 42 curriculum by crmatas-.*

# A-Maze-ing

## Overview

A-Maze-ing is a Python project to generate and display mazes from a configuration file. The generator will support perfect mazes, with a unique path between cells, and non-perfect mazes, with loops for more flexible navigation. A generated maze will be written to an output file and shown in a visual representation.

The project is currently in the architecture and practices definition stage. The generation algorithm, module boundaries, and task distribution are still to be decided; this README will be updated as those decisions are made.

## Commit Convention

Commit messages use an uppercase prefix in square brackets, followed by a short description:

```text
[PREFIX] Short description
```

Use one focused change per commit and choose the prefix that best describes it:

| Prefix | Use |
| --- | --- |
| `[FEAT]` | Add functionality |
| `[FIX]` | Fix a bug |
| `[REFACTOR]` | Improve the internal structure without changing behavior |
| `[STYLE]` | Make formatting-only changes |
| `[DOCS]` | Add or update documentation |
| `[TEST]` | Add or update tests |
| `[CHORE]` | Handle maintenance tasks |

Examples:

```text
[FEAT] Add maze generation
[FIX] Keep shared walls consistent
[DOCS] Describe the configuration format
```

## Project summary

A-Maze-ing is a Python maze generator and graphical visualizer. The project builds mazes from configuration files, supports perfect and braided variants, and can render the generation process and the shortest path in a MiniLibX window.

## Main features

- Randomized maze generation with depth-first search.
- Perfect mazes and braided mazes with loops.
- Visual generation and menu-based runtime configuration.
- Shortest-path visualization using breadth-first search.
- Optional centered "42" pattern on larger boards.
- Maze serialization through the project API.

## Installation and execution

The project requires Python 3.12 or newer and Poetry. From the repository root, install the development dependencies with:

```bash
make setup-dev
```

On Ubuntu under WSL, install MiniLibX's native dependencies first if you need the graphical backend:

```bash
make setup-wsl
```

Generate and export a maze using the available Python API:

```bash
poetry run python -c "from mazegen.maze_generator import MazeGenerator; maze = MazeGenerator(width=20, height=15, entry=(0, 0), exit=(19, 14), output_file='maze.txt', perfect=True); maze.generate(); maze.export_to_file()"
```

This writes the maze and its shortest solution to `maze.txt`. Run the test suite with:

```bash
poetry run pytest
```

The graphical application does not currently have a project entry-point script, so there is no runnable command for launching its menu yet.

## Building and installing the wheel

Build the distributable wheel from the repository root with Poetry:

```bash
poetry build --format wheel
```

The wheel is written to `dist/`. With the current project version, its filename is `mazegen-1.0.0-py3-none-any.whl`; the version in the filename changes when the package version is updated.

To install and check the wheel in a separate Python 3.12 virtual environment:

```bash
python3 -m venv /tmp/eval_env
source  /tmp/bin/activate
pip install dist/mazagen-1.0.0-py3-none-any.whl

python -m pip install dist/mazegen-1.0.0-py3-none-any.whl

python -c "from mazegen.maze_generator import MazeGenerator; print('mazegen installed')"
```

Pip installs the wheel's declared runtime dependencies into this virtual environment. The wheel packages the reusable `mazegen` library, not the graphical application.

## Visualization and options

The project includes a graphical interface built with MiniLibX where the maze is generated and displayed in a dedicated window.

### Settings menu

The startup menu lets the user adjust the app before rendering the maze:

- Theme: changes the color palette of the interface.
- Speed: controls the generation animation rate.
- Seed: changes the random maze pattern.
- Perfect: toggles between a perfect maze and a braided maze with loops.
- Render maze: starts the generation and opens the maze view.

Keyboard controls in the menu:

- Up / Down: move between options.
- Left / Right: change the selected value.
- Enter: confirm and render the maze.
- Esc: quit the application.

### Maze view

Once the maze is generated, the player can interact with it directly:

- `R`: regenerate the maze with the current configuration.
- `S` or `Enter`: show or hide the shortest solution path.
- `Esc`: return to the settings menu.

This makes the visualization useful both for previewing generation and for checking the optimized route through the maze.

## Generation algorithm

The generator uses depth-first search (DFS) with backtracking to create a maze with a single connected path between cells and no loops by default.

Why this algorithm was chosen:

- It is simple and reliable for creating perfect mazes with a clear tree structure.
- It guarantees that every reachable cell is visited exactly once while carving passages.
- It naturally supports animated generation: each step can be traced as a cell is visited and then backtracked.
- In the implementation, the generator keeps a stack of active cells and removes the wall between the current cell and a random unvisited neighbor. When no neighbors remain, it backtracks until it finds another branch.

This produces a well-formed maze quickly and matches the intended visual generation flow in the application.

For braided mazes, the same base generator is followed by a controlled wall-removal pass that opens extra passages at dead ends, creating loops without breaking the overall structure. This is useful when the project needs a less strict maze while still preserving navigability.

### How "perfect" works

The `PERFECT` option controls whether the maze remains a strict tree-like maze or is expanded with extra loops.

- When `PERFECT = True`, the generator keeps the classic DFS maze shape: every cell is reachable, and there is exactly one simple path between any two cells. This creates a minimal, clean maze without cycles.
- When `PERFECT = False`, the generator performs an additional braiding step after DFS. It identifies dead ends, tries to open an extra connection, and keeps the modification only when it does not create a problematic 3x3 open block. The result is a maze with loops and a more organic structure while still remaining valid and navigable.

This distinction is useful because the project supports both a mathematically clean perfect maze and a more game-like braided maze with more route choices.

## Solution algorithm

The shortest path is computed with breadth-first search (BFS), which is implemented in the solver layer.

Why this algorithm was chosen:

- BFS explores cells level by level, so the first time it reaches the exit it has already found the shortest path in terms of steps.
- This is ideal for maze navigation, where the goal is not just any valid route, but the minimal route.
- The solver stores the predecessor of each visited cell and reconstructs the path backward once the exit is found.

In this project, BFS is a better fit than DFS for the solution phase because the app explicitly wants the shortest solution path to be shown to the user. The result is both clear and consistent with the user-facing visual feedback.

## Project structure

- `app/` — application flow, scenes, rendering, themes, and configuration parsing.
- `mazegen/` — maze generation, grid logic, and solving utilities.
- `tests/` — automated test coverage for the generator and app behavior.
- `config.txt` — example runtime configuration.
- `DEVELOPMENT.md` — setup and development instructions.

## Reusable package

The project is structured as an importable Python package so its maze-generation logic can be reused by other projects or game systems, including a Pacman-style game that needs a maze, pathfinding, and consistent runtime configuration.

The reusable pieces are organized around clear responsibilities:

- `mazegen` exposes the maze model and generation logic as a library. A different project can create a `MazeGenerator`, configure dimensions, entry/exit coordinates, and maze mode, and then import the ready-to-use grid and path information without needing the full graphical app.
- `mazegen.solutions` provides path-solving functionality independently of the renderer. This allows another project to request the shortest route between two cells and use it for AI enemies, player navigation, or route previews.
- `app` contains the application layer, but it is deliberately separated from the core algorithmic logic. The maze generation and solver are not tied to the MiniLibX interface, so they can be reused in a game loop or console-based simulator.
- `RuntimeSettings` and configuration parsing are also reusable building blocks: the same values that drive the menu and rendering can also feed a game with fixed settings, different themes, or custom generation seeds.

This design makes the project more than a single executable: it becomes a library that can generate mazes, solve them, and provide the data needed by a larger game or simulation. In a Pacman-like context, the same package could supply the maze map, the shortest-path logic, and the reusable generation rules without duplicating code.

## Contributions

The project was developed collaboratively. The following summarizes each contributor's main areas of work:

- **crmatas- (Cristina Matas)** — focused mainly on the maze-generation core: the `MazeGenerator` API, DFS generation, perfect and braided maze behavior, the centered "42" pattern, maze output, and related tests.
- **lupin (Lucas Pin)** — focused mainly on the application and visualization: the MiniLibX renderer, maze interpreter, menu and maze scenes, themes, runtime settings, and related tests. He also set up the development environment and automated project workflows with GitHub.

Both contributors worked within the shared project structure, and the areas above describe the primary focus of their contributions rather than exclusive ownership of every related file.

## Project reflection

### Planning and how it evolved

The initial work focused on defining the project structure, agreeing on development practices, and dividing responsibilities. As implementation progressed, the scope developed into two connected parts: a reusable maze-generation and solving package, and a graphical application for configuring and visualizing mazes. The algorithmic work grew to include DFS generation, BFS shortest-path solving, and braided mazes, while the application work added the menu, themes, and interactive maze view.

### What worked well and what could be improved

Separating the maze logic from the graphical application made the generator and solver reusable and easier to test independently. Splitting the work across the core logic and the visualization also helped develop both parts in parallel.

The development and usage instructions could be kept more closely aligned with the actual application entry point and environment requirements. The graphical MiniLibX setup also depends on native system libraries, so documenting and validating that setup across supported environments remains an area for improvement.

### Tools used

- Python 3.12+ and Poetry for the project and dependency management.
- MiniLibX for the graphical interface.
- pytest for automated tests; flake8 and mypy for code quality and type checks.
- pre-commit for Git hooks, and Git/GitHub CLI for version control and project workflows.

## Resources

- [Python documentation](https://docs.python.org/3/) — language and standard library reference.
- [Poetry documentation](https://python-poetry.org/docs/) — dependency and project management.
- [MiniLibX for Linux](https://github.com/42Paris/minilibx-linux) — graphics library used by the application.
- [Depth-first search](https://cp-algorithms.com/graph/depth-first-search.html) and [breadth-first search](https://cp-algorithms.com/graph/breadth-first-search.html) — algorithm references.
- [pytest documentation](https://docs.pytest.org/en/stable/) — testing framework reference.

## AI usage

For this README update, AI assistance was used to help draft and refine documentation, including the project reflection and this resources section. The project code and its test results were not generated or validated as part of this documentation task.
