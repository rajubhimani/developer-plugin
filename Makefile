# developer-plugin: developer commands for macOS and Linux.
# Windows: run the same steps with python directly, e.g. `python scripts/check.py`
# and `python scripts/install.py claude`. See README.md.
#
#   make help                     show targets
#   make check                    validate and test (same as python scripts/check.py)
#   make install-claude           install for Claude Code (REF=vX.Y.Z for a tagged version,
#                                 DRY=1 to preview, CONFIRM=1 to allow a downgrade or major step)
#   make check-install            report installed copies that drifted from this checkout
#   make install-codex            install for Codex
#   make install-antigravity      copy into Antigravity's plugin folder
#   make install-copilot          install into Copilot CLI from the git remote
#   make install-all              every installer; missing clients are skipped
#   make uninstall-claude         remove the Claude Code install and its copy
#   make uninstall-codex          remove the Codex install and its copy
#   make uninstall-antigravity    remove the Antigravity copy
#   make release LEVEL=minor      bump the version and close the changelog section
#   make releases                 list released versions (git tags)
#   make navigator PROJECTS=...   rewrite the projects docs
#   make workspace PROJECTS=...   create or refresh project docs
#   make init-project REPO=... LANG=... [KIND=... NAME=... MEMBERS=a:kind,b:kind MODULE=... STRUCTURE=best-practice|own]
#   make structure-check REPO=... check a project's layout against its recorded kind
#   make versions                 print the current stable release of common tools
#   make token-cost               estimate what the plugin costs in context

PY       := python3
PLUGIN   := developer-plugin
REF_ARG   = $(if $(REF),--ref $(REF),) $(if $(DRY),--dry-run,) $(if $(CONFIRM),--confirm-update,)
PROJECTS ?=

.DEFAULT_GOAL := help
.PHONY: help test check validate sync-rules release releases install-claude uninstall-claude \
	install-codex uninstall-codex install-antigravity uninstall-antigravity install-copilot \
	install-all update-clis check-install navigator workspace versions init-project structure-check token-cost

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-22s %s\n", $$1, $$2}'

validate: ## Check manifests, skills and generated rule copies
	@$(PY) scripts/validate.py
	@$(PY) scripts/sync_rules.py --check

test: ## Run the plugin's tests (manifests, skills, templates, generators)
	@$(PY) -m unittest discover -s tests -v

check: ## Validate and test (the gate before a commit or release)
	@$(PY) scripts/check.py

sync-rules: ## Regenerate the skill and rules/AGENTS.md from rules/coding-standards.md
	@$(PY) scripts/sync_rules.py

release: validate test ## Bump the version: make release LEVEL=patch|minor|major
	@$(PY) scripts/release.py bump $(LEVEL)

releases: ## List released versions (git tags)
	@git tag -l 'v*' --sort=-v:refname

install-claude: validate ## Install into Claude Code from its own copy (REF=vX.Y.Z optional)
	@$(PY) scripts/install.py claude $(REF_ARG)

uninstall-claude: ## Remove the Claude Code install and its copy
	@$(PY) scripts/install.py uninstall claude

install-codex: validate ## Install into Codex from its own copy (REF=vX.Y.Z optional)
	@$(PY) scripts/install.py codex $(REF_ARG)

uninstall-codex: ## Remove the Codex install and its copy
	@$(PY) scripts/install.py uninstall codex

install-antigravity: validate ## Copy into Antigravity's plugin folder (REF=vX.Y.Z optional)
	@$(PY) scripts/install.py antigravity $(REF_ARG)

uninstall-antigravity: ## Remove the Antigravity copy
	@$(PY) scripts/install.py uninstall antigravity

install-copilot: validate ## Install into Copilot CLI from the git remote
	@$(PY) scripts/install.py copilot

install-all: validate ## Run every installer; missing clients are skipped
	@$(PY) scripts/install.py all $(REF_ARG)

check-install: ## Read-only: report installed copies that drifted from this checkout
	@$(PY) scripts/install.py check-install

update-clis: ## Upgrade the npm-installed Codex CLI to latest
	@$(PY) scripts/install.py update-clis

navigator: ## Rewrite the docs for PROJECTS (set PROJECTS=<folder>)
	@test -n "$(PROJECTS)" || { echo "set PROJECTS=<folder that holds your repos>"; exit 1; }
	@$(PY) scripts/init_workspace.py "$(PROJECTS)"

workspace: ## Create or refresh project docs for PROJECTS (umbrella or single repo)
	@test -n "$(PROJECTS)" || { echo "set PROJECTS=<folder that holds your repos>"; exit 1; }
	@$(PY) scripts/init_workspace.py "$(PROJECTS)"

versions: ## Print the current stable release of common tools (live lookup)
	@$(PY) scripts/check_versions.py

init-project: ## Copy standard files into REPO (LANG=python|go|rust|node|c|cpp|java; KIND=library|webapp|... asks once in a terminal)
	@test -n "$(REPO)" -a -n "$(LANG)" || { echo "usage: make init-project REPO=<folder> LANG=<language> [KIND=<kind> NAME=<name> MEMBERS=a:kind,b:kind MODULE=<go module> STRUCTURE=best-practice|own]"; exit 1; }
	@$(PY) scripts/init_project.py "$(REPO)" "$(LANG)" $(if $(KIND),--kind "$(KIND)",) $(if $(NAME),--name "$(NAME)",) $(if $(MEMBERS),--members "$(MEMBERS)",) $(if $(MODULE),--module "$(MODULE)",) $(if $(STRUCTURE),--structure "$(STRUCTURE)",)

structure-check: ## Check REPO's layout against its recorded project kind (read-only)
	@test -n "$(REPO)" || { echo "usage: make structure-check REPO=<folder>"; exit 1; }
	@$(PY) scripts/check_structure.py "$(REPO)"

token-cost: ## Estimate what the plugin costs in context (always loaded versus on use)
	@$(PY) scripts/token_cost.py
