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