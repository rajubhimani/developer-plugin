# Install developer-plugin into Claude Code, Codex, Gemini CLI and/or GitHub Copilot.
#
#   make help              show targets
#   make install-claude    install for Claude Code
#   make install-codex     install for Codex
#   make install-gemini    link into Gemini CLI
#   make install-copilot   print Copilot steps (no CLI install command verified)
#   make install-all       run every installer; tools that are missing are skipped
#   make uninstall-claude  remove the Claude Code install
#   make validate          check manifests and skills

ROOT     := $(abspath .)
STAGE    := $(ROOT)/build/codex-marketplace
PLUGIN   := developer-plugin
MKT_NAME := developer-plugin-local

.DEFAULT_GOAL := help
.PHONY: help validate install-claude uninstall-claude install-codex install-gemini install-copilot install-all

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-20s %s\n", $$1, $$2}'

validate: ## Check manifests and skill frontmatter
	@python3 scripts/validate.py

install-claude: validate ## Install into Claude Code (user scope)
	@if command -v claude >/dev/null 2>&1; then \
	  claude plugin marketplace add "$(ROOT)" || true; \
	  claude plugin install "$(PLUGIN)@$(MKT_NAME)" && \
	  echo "claude: installed. Start a new session and run /plugin to confirm."; \
	else echo "claude: not installed, skipping"; fi

uninstall-claude: ## Remove the Claude Code install
	@if command -v claude >/dev/null 2>&1; then \
	  claude plugin uninstall "$(PLUGIN)@$(MKT_NAME)" || true; \
	  claude plugin marketplace remove "$(MKT_NAME)" || true; \
	else echo "claude: not installed, nothing to remove"; fi

install-codex: validate ## Stage a Codex marketplace and register it
	@if command -v codex >/dev/null 2>&1; then \
	  rm -rf "$(STAGE)" && mkdir -p "$(STAGE)/plugins/$(PLUGIN)" "$(STAGE)/.agents/plugins" && \
	  rsync -a --exclude build --exclude .git --exclude scripts "$(ROOT)/" "$(STAGE)/plugins/$(PLUGIN)/" && \
	  printf '%s\n' '{' '  "name": "$(MKT_NAME)",' '  "plugins": [' '    {' '      "name": "$(PLUGIN)",' '      "source": { "source": "local", "path": "./plugins/$(PLUGIN)" },' '      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },' '      "category": "Developer"' '    }' '  ]' '}' > "$(STAGE)/.agents/plugins/marketplace.json" && \
	  codex plugin marketplace add "$(STAGE)" && \
	  echo "codex: marketplace registered. Enable it in .codex/config.toml:" && \
	  echo '  [plugins."$(PLUGIN)@$(MKT_NAME)"]' && echo '  enabled = true'; \
	else echo "codex: not installed, skipping"; fi

install-gemini: validate ## Link this folder into Gemini CLI
	@if command -v gemini >/dev/null 2>&1; then \
	  gemini extensions link "$(ROOT)" && echo "gemini: linked. Restart the CLI session."; \
	else echo "gemini: not installed, skipping"; fi

install-copilot: validate ## Print GitHub Copilot install steps
	@echo "GitHub Copilot (VS Code):"
	@echo "  1. Enable the setting chat.plugins.enabled"
	@echo "  2. Run 'Chat: Install Plugin from Source' and choose: $(ROOT)"
	@echo "  3. Start a fresh Copilot chat session to load it."
	@echo "GitHub Copilot CLI: inside a session run  /plugin install $(ROOT)"

install-all: ## Run every installer; skip tools that are missing
	@failed=0; \
	  for t in install-claude install-codex install-gemini; do \
	    $(MAKE) --no-print-directory $$t || failed=1; \
	  done; \
	  $(MAKE) --no-print-directory install-copilot; \
	  exit $$failed
