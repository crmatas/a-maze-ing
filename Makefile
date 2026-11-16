.DEFAULT_GOAL := help
.PHONY: help setup install setup-dev setup-wsl setup-gh check-poetry check-apt check-wsl check-gh gh-auth issue pr lint lint-strict debug run clean

GH_KEYRING := /etc/apt/keyrings/githubcli-archive-keyring.gpg
GH_SOURCE := /etc/apt/sources.list.d/github-cli.list
LOCAL_BIN := $(HOME)/.local/bin

export PATH := $(LOCAL_BIN):$(PATH)

help:
	@echo "make install     -> install Python 3.12 and runtime dependencies without sudo"
	@echo "make setup-dev   -> install runtime, dev, and hook dependencies"
	@echo "make setup-wsl   -> install native MiniLibX dependencies on Ubuntu/WSL"
	@echo "make setup-gh    -> install/update gh and authenticate it"
	@echo "make issue       -> create an interactive issue (requires authenticated gh)"
	@echo "make pr          -> create a pull request (requires authenticated gh)"
	@echo "make lint        -> run flake8 and mypy with the required flags"
	@echo "make lint-strict -> run flake8 and mypy --strict"
	@echo "make run         -> run the application with config.txt"
	@echo "make debug       -> run a_maze_ing.py with pdb"
	@echo "make clean       -> clean generated files"


clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ *.pyc *.pyo .pytest_cache
	@echo "Cleanup complete."

check-poetry:
	@command -v poetry >/dev/null || { echo "Poetry is missing: https://python-poetry.org/docs/#installation"; exit 1; }

check-apt:
	@command -v apt-get >/dev/null || { echo "This target requires Ubuntu or Debian with APT."; exit 1; }
	@. /etc/os-release; \
	case "$$ID" in ubuntu|debian) ;; *) echo "Unsupported distribution: $$ID."; exit 1 ;; esac

check-wsl: check-apt
	@grep -qi microsoft /proc/sys/kernel/osrelease || { echo "This target must be run inside WSL."; exit 1; }
	@. /etc/os-release; \
	[ "$$ID" = ubuntu ] || { echo "This target requires Ubuntu on WSL; detected: $$ID."; exit 1; }

install:
	@if ! command -v uv >/dev/null 2>&1; then \
		command -v curl >/dev/null 2>&1 || { echo "curl is required to install uv without sudo."; exit 1; }; \
		echo "Installing uv in $(LOCAL_BIN)..."; \
		curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$(LOCAL_BIN)" sh; \
	fi
	uv python install 3.12
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "Installing Poetry for the current user..."; \
		uv tool install poetry --python 3.12; \
	fi
	poetry env use "$$(uv python find 3.12)"
	@echo "Installing runtime dependencies..."
	poetry install --only main,app

lint: check-poetry
	poetry run flake8 .
	poetry run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict: check-poetry
	poetry run flake8 .
	poetry run mypy . --strict

debug: check-poetry
	@echo "Running a_maze_ing.py with pdb..."
	poetry run python -m pdb a_maze_ing.py config.txt

run: check-poetry
	poetry run python a_maze_ing.py config.txt

setup-dev: check-poetry
	@echo "Setting up the development environment..."
	poetry install --with app,dev
	poetry run pre-commit install
	@echo "Development environment is ready."

setup-wsl: check-wsl
	@echo "Setting up the WSL environment..."
	sudo apt-get update
	sudo apt-get install -y libxcb-keysyms1 libvulkan1
	@echo "Native MiniLibX dependencies installed."

setup-gh:
	@./dev-utils/scripts/setup_gh.sh
	PATH="$$HOME/.local/bin:$$PATH" $(MAKE) gh-auth

gh-auth:
	@if ! gh auth status >/dev/null 2>&1; then \
		echo "Authenticating gh with repo and project scopes..."; \
		gh auth login --scopes repo,project; \
	else \
		status="$$(gh auth status 2>&1)"; \
		if ! printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'repo'" \
			|| ! printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'project'"; then \
			echo "Updating gh scopes to repo,project..."; \
			gh auth refresh --scopes repo,project; \
		else \
			echo "gh is already authenticated with the required scopes."; \
		fi; \
	fi

check-gh:
	@command -v gh >/dev/null || { echo "gh is missing; run 'make setup-gh'."; exit 1; }
	@gh auth status >/dev/null 2>&1 || { echo "gh is not authenticated; run 'make setup-gh'."; exit 1; }
	@status="$$(gh auth status 2>&1)"; \
	printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'repo'" \
		|| { echo "Missing the repo scope; run 'make setup-gh'."; exit 1; }; \
	printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'project'" \
		|| { echo "Missing the project scope; run 'make setup-gh'."; exit 1; }

issue: check-gh
	@./dev-utils/scripts/new_issue.sh

pr: check-gh
	@./dev-utils/scripts/new_pull_request.sh
