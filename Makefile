# Tasq Makefile
# Lint, format, and style checks for the ZMQ-based distributed task queue.

.PHONY: help lint fix format style clean

# ============================================================================
# Shared Variables
# ============================================================================

PY     ?= /home/iam/devcode/.env/tasq/bin/python3
RUFF   := $(dir $(PY))ruff
STYLE_DIRS := tasq tests

# Colors
GREEN  := \033[0;32m
YELLOW := \033[1;33m
NC     := \033[0m

# ============================================================================
# Help
# ============================================================================

help:
	@echo "$(GREEN)Tasq Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Style:$(NC)"
	@echo "  make lint                     ruff check (no fixes)"
	@echo "  make fix                      ruff check --fix + except-tuple fix"
	@echo "  make format                   ruff format"
	@echo "  make style                    fix -> format -> format --check"
	@echo "  make clean                    wipe __pycache__ and .ruff_cache"
	@echo ""

# ============================================================================
# Style pipeline
# ============================================================================

lint:
	$(RUFF) check --extend-select I $(STYLE_DIRS)
	@! grep -rnE 'except [A-Za-z_][A-Za-z_.]*, *[A-Za-z_.]' $(STYLE_DIRS) \
	  || (echo "ERROR: unparenthesized except tuple found" && exit 1)
	@echo "except-tuple check OK"

fix:
	@for f in $$(find $(STYLE_DIRS) -name '*.py' -type f); do \
		if grep -qE 'except\s+[A-Za-z_]\w*(\s*,\s*[A-Za-z_]\w*)+\s*:' "$$f"; then \
			sed -i -E 's/except\s+(\w+)\s*,\s*([^:]+)\s*:/except (\1, \2):/g' "$$f"; \
			echo "  fixed except syntax: $$f"; \
		fi; \
	done
	$(RUFF) check --fix --extend-select I $(STYLE_DIRS)

format:
	$(RUFF) format $(STYLE_DIRS)

style: fix format
	$(RUFF) format --check $(STYLE_DIRS)
	@echo "$(GREEN)style: clean$(NC)"

# ============================================================================
# Clean
# ============================================================================

clean:
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .ruff_cache
	@echo "$(GREEN)Clean$(NC)"
