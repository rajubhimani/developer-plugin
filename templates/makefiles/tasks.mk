# tasks: start (added by developer-plugin; safe to edit)
.PHONY: tasks task-new task-move decide decisions-sync

tasks: ## List tasks by status with start and completion times (UTC)
	@python3 scripts/tasks.py list --times

task-new: ## New task: make task-new FEATURE=<slug> TITLE="..." REQ=REQ-001
	@test -n "$(FEATURE)" -a -n "$(TITLE)" || { echo 'usage: make task-new FEATURE=<slug> TITLE="..." [REQ=REQ-001]'; exit 1; }
	@python3 scripts/tasks.py new "$(FEATURE)" "$(TITLE)" $(if $(REQ),--req $(REQ),)

task-move: ## Move a task: make task-move TASK=<id> STATUS=<status> [REASON="..."]
	@test -n "$(TASK)" -a -n "$(STATUS)" || { echo 'usage: make task-move TASK=<id> STATUS=<backlog|in-progress|completed|rejected> [REASON="..."]'; exit 1; }
	@python3 scripts/tasks.py move "$(TASK)" "$(STATUS)" $(if $(REASON),--reason "$(REASON)",)
decide: ## Record a decision you made: make decide TEXT="..."
	@test -n "$(TEXT)" || { echo 'usage: make decide TEXT="what you decided"'; exit 1; }
	@python3 scripts/tasks.py decide "$(TEXT)"
decisions-sync: ## Refresh the standing decisions in AGENTS.md
	@python3 scripts/tasks.py sync
# tasks: end
