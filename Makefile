.PHONY: help setup check-tools install hooks gh-auth issue
GH_BIN := $(HOME)/.local/bin

help:
	@echo "make setup  -> entorno poetry + hooks de pre-commit + autenticacion de gh"
	@echo "make issue  -> crear una issue (script interactivo)"

setup: check-tools install hooks gh-auth install-gh
	@echo "Entorno listo."

check-tools:
	@command -v poetry >/dev/null || { echo "Falta poetry: https://python-poetry.org/docs/#installation"; exit 1; }
	@command -v gh >/dev/null || { echo "Falta gh: https://cli.github.com"; exit 1; }

install:
	poetry install

hooks:
	poetry run pre-commit install

install-gh:
	@if command -v gh >/dev/null 2>&1; then \
		echo "gh ya esta instalado."; \
	else \
		echo "Instalando gh en $(GH_BIN)..."; \
		mkdir -p $(GH_BIN); \
		VER=$$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep -m1 '"tag_name"' | sed 's/.*"v\([^"]*\)".*/\1/'); \
		curl -sL https://github.com/cli/cli/releases/download/v$$VER/gh_$${VER}_linux_amd64.tar.gz \
			| tar -xz -C /tmp; \
		cp /tmp/gh_$${VER}_linux_amd64/bin/gh $(GH_BIN)/gh; \
		echo "Asegurate de que $(GH_BIN) esta en tu PATH."; \
	fi

gh-auth:
	@if ! gh auth status >/dev/null 2>&1; then \
		echo "Autenticando gh (se abrira el flujo interactivo)..."; \
		gh auth login --scopes project; \
	elif ! gh auth status 2>&1 | grep -q "project"; then \
		echo "Anadiendo el scope 'project' a tu sesion de gh..."; \
		gh auth refresh --scopes project; \
	else \
		echo "gh ya esta autenticado con el scope 'project'."; \
	fi

issue: check-tools
	@./scripts/new_issue.sh