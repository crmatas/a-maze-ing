# Development Guide

This document explains how to prepare the development environment, run the project checks, and configure pre-commit hooks.
Run the commands below from the repository root.

## Requirements

- Python 3.12 or newer.
- Poetry.
- Ubuntu on WSL for installing MiniLibX's native dependencies.

The graphical MiniLibX setup is optional if you are only working on code that does not use its display backend.

## First-time setup

On Ubuntu under WSL, install the native MiniLibX dependencies:

```bash
make setup-wsl
```

Install the project and development tools, and configure the Git hooks:

```bash
make setup-dev
```

`setup-dev` runs `poetry install --with dev` and `poetry run pre-commit install`. The WSL target uses `sudo apt-get` to install `libxcb-keysyms1` and `libvulkan1`.

To install only the main dependency group, use:

```bash
make install
```

## Poetry configuration

Project and tool configuration lives in `pyproject.toml`; this repository does not use a `poetry.toml` file.

- `[project]` contains package metadata, sets the minimum Python version to 3.12, and declares NumPy as a runtime dependency.
- `[tool.poetry.group.dev.dependencies]` contains development dependencies: `pytest`, `mypy`, `flake8`, `pre-commit`, and the local Ubuntu MiniLibX wheel. `pydantic-settings` is a runtime dependency because the application parser imports it.
- `[tool.mypy]` enables the Pydantic plugin.
- `[[tool.mypy.overrides]]` ignores missing type stubs for `mlx` when mypy is run with the project configuration alone. The `make lint` target also passes `--ignore-missing-imports`, which suppresses missing-import diagnostics globally for that command.
- `[tool.pydantic-mypy]` configures the Pydantic mypy plugin.
- `[tool.pytest.ini_options]` sets `testpaths = ["tests"]`; normal pytest discovery is therefore limited to the `tests/` directory.

`poetry.lock` records the resolved dependency versions. Change dependencies through Poetry rather than editing the lock file by hand. For example, add a development dependency with:

```bash
poetry add --group dev package-name
```

## Running the project

The subject specifies this invocation:

```bash
poetry run python a_maze_ing.py config.txt
```

The repository currently has no `a_maze_ing.py` at its root, so this command is not runnable until the application entry point is added or the command is updated to its actual location. The `make debug` target currently expects that same root-level script.

## Tests

Run all discovered tests with:

```bash
poetry run pytest
```

Pytest reads `testpaths` from `pyproject.toml`, so it searches under `tests/` rather than collecting example scripts elsewhere in the repository. Test files should be named `test_*.py` or `*_test.py`, and test functions should start with `test_`.

Run one test module with verbose output:

```bash
poetry run pytest tests/test_config.py -v
```

## Make targets

Run `make` to print the Makefile help. The current targets are:

| Command | Purpose |
| --- | --- |
| `make install` | Install only main dependencies. |
| `make setup-dev` | Install development dependencies and Git hooks. |
| `make setup-wsl` | Install MiniLibX native dependencies on Ubuntu under WSL. |
| `make lint` | Run flake8 and mypy with the required lint flags. |
| `make lint-strict` | Run flake8 and mypy in strict mode. |
| `make debug` | Start `a_maze_ing.py config.txt` under Python's debugger. |
| `make clean` | Remove the generated files listed in the Makefile. |
| `make setup-gh` | Install GitHub CLI and authenticate it. |
| `make issue` | Create an issue using GitHub CLI. |
| `make pr` | Create a pull request using GitHub CLI. |

The `issue` and `pr` targets require GitHub CLI authentication. The `clean` target currently removes root-level Python bytecode/cache files and `.pytest_cache`; it does not remove `.venv` or `.git`.

## pre-commit

The hook configuration is in `.pre-commit-config.yaml`. It uses local hooks, so tools are run from the Poetry environment rather than a separate pre-commit environment.

- `default_install_hook_types: [pre-commit, pre-push]` asks `pre-commit install` to install both Git hooks.
- The global `exclude: ^dev-utils/` skips files under `dev-utils/` for all configured hooks.
- `flake8` runs on Python files at the `pre-commit` stage, normally when committing.
- `mypy` runs on Python files at the `pre-push` stage. `pass_filenames: true` passes the changed files to mypy.

Run the commit-stage hook manually on all eligible files:

```bash
poetry run pre-commit run --all-files
```

Run the push-stage hook manually:

```bash
poetry run pre-commit run --hook-stage pre-push --all-files
```

Validate changes to the hook configuration with:

```bash
poetry run pre-commit validate-config
```

### Configuring hooks and exclusions

Use a top-level `exclude` when a path should be skipped by every hook. For example, the current `^dev-utils/` pattern excludes the entire `dev-utils/` tree. To exempt one exact file from that global exclusion, use a negative lookahead:

```yaml
exclude: ^dev-utils/(?!scripts/keep_this\.py$)
```

This permits `dev-utils/scripts/keep_this.py` to be considered by all hooks while excluding the rest of `dev-utils/`.

Use `exclude` inside a hook when a different exclusion should apply only to that hook. A hook-level value replaces the top-level default for that hook, so include the global pattern again if it should remain excluded there. For example, to keep excluding `dev-utils/` and also skip generated files for flake8 only:

```yaml
			- id: flake8
				name: flake8
				entry: poetry run flake8
				language: system
				types: [python]
				exclude: ^(?:dev-utils/|app/generated/)
				stages: [pre-commit]
```

Other useful hook options include:

- `files`: limit a hook to paths matching a regular expression, for example `^app/`.
- `types`: select file types, such as `[python]`.
- `stages`: choose when it runs, such as `[pre-commit]` or `[pre-push]`.
- `args`: pass extra command-line arguments to the hook's `entry` command.
- `pass_filenames`: control whether pre-commit appends matched filenames to the command. It is `true` by default.

To add another local hook, first add its tool to the appropriate Poetry dependency group, then add an entry under `repo: local`:

```yaml
			- id: example-check
				name: example check
				entry: poetry run example-check
				language: system
				types: [python]
				stages: [pre-commit]
```

Use `SKIP=hook-id` only for a one-off invocation when necessary, for example `SKIP=flake8 git commit`. Prefer fixing the code or configuring a narrow exclusion over routinely skipping checks.
