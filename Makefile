.DEFAULT_GOAL := help
.PHONY: help setup install setup-dev setup-wsl setup-gh check-poetry check-apt check-wsl check-gh gh-auth issue pr

GH_KEYRING := /etc/apt/keyrings/githubcli-archive-keyring.gpg
GH_SOURCE := /etc/apt/sources.list.d/github-cli.list

help:
	@echo "make install    -> instalar dependencias principales"
	@echo "make setup-dev -> instalar dependencias dev y hooks"
	@echo "make setup-wsl -> instalar dependencias nativas de MiniLibX en Ubuntu/WSL"
	@echo "make setup-gh  -> instalar/actualizar gh y autenticarlo"
	@echo "make issue     -> crear una issue interactiva (requiere gh autenticado)"
	@echo "make pr        -> crear un pull request (requiere gh autenticado)"

setup: setup-dev

check-poetry:
	@command -v poetry >/dev/null || { echo "Falta Poetry: https://python-poetry.org/docs/#installation"; exit 1; }

check-apt:
	@command -v apt-get >/dev/null || { echo "Este target requiere Ubuntu o Debian con APT."; exit 1; }
	@. /etc/os-release; \
	case "$$ID" in ubuntu|debian) ;; *) echo "Distribucion no soportada: $$ID."; exit 1 ;; esac

check-wsl: check-apt
	@grep -qi microsoft /proc/sys/kernel/osrelease || { echo "Este target debe ejecutarse dentro de WSL."; exit 1; }
	@. /etc/os-release; \
	[ "$$ID" = ubuntu ] || { echo "Este target requiere Ubuntu en WSL; detectado: $$ID."; exit 1; }

install: check-poetry
	poetry install --only main

setup-dev: check-poetry
	poetry install --with dev
	poetry run pre-commit install
	@echo "Entorno de desarrollo listo."

setup-wsl: check-wsl
	sudo apt-get update
	sudo apt-get install -y libxcb-keysyms1 libvulkan1
	@echo "Dependencias nativas de MiniLibX instaladas."

setup-gh: check-apt
	sudo apt-get update
	sudo apt-get install -y ca-certificates curl
	sudo install -d -m 755 /etc/apt/keyrings
	sudo curl -fsSL -o $(GH_KEYRING) https://cli.github.com/packages/githubcli-archive-keyring.gpg
	sudo chmod go+r $(GH_KEYRING)
	printf 'deb [arch=%s signed-by=%s] https://cli.github.com/packages stable main\n' "$$(dpkg --print-architecture)" "$(GH_KEYRING)" | sudo tee $(GH_SOURCE) >/dev/null
	sudo apt-get update
	sudo apt-get install -y gh
	@installed=$$(gh version | awk 'NR == 1 { print $$3 }'); \
	candidate=$$(apt-cache policy gh | awk '/Candidate:/ { print $$2 }'); \
	if ! dpkg --compare-versions "$$installed" ge "$$candidate"; then \
		echo "Aviso: gh $$installed es anterior a la version APT disponible $$candidate."; \
	else \
		echo "gh $$installed esta actualizado segun APT."; \
	fi
	$(MAKE) gh-auth

gh-auth:
	@if ! gh auth status >/dev/null 2>&1; then \
		echo "Autenticando gh con scopes repo y project..."; \
		gh auth login --scopes repo,project; \
	else \
		status="$$(gh auth status 2>&1)"; \
		if ! printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'repo'" \
			|| ! printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'project'"; then \
			echo "Actualizando scopes de gh a repo,project..."; \
			gh auth refresh --scopes repo,project; \
		else \
			echo "gh ya esta autenticado con los scopes necesarios."; \
		fi; \
	fi

check-gh:
	@command -v gh >/dev/null || { echo "Falta gh; ejecuta 'make setup-gh'."; exit 1; }
	@gh auth status >/dev/null 2>&1 || { echo "gh no esta autenticado; ejecuta 'make setup-gh'."; exit 1; }
	@status="$$(gh auth status 2>&1)"; \
	printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'repo'" \
		|| { echo "Falta el scope repo; ejecuta 'make setup-gh'."; exit 1; }; \
	printf '%s\n' "$$status" | grep "Token scopes" | grep -q "'project'" \
		|| { echo "Falta el scope project; ejecuta 'make setup-gh'."; exit 1; }

issue: check-gh
	@./scripts/new_issue.sh

pr: check-gh
	@./scripts/new_pull_request.sh