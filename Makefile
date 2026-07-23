# Admin shortcuts for the DMOJ stack. All targets delegate to manage.sh.
#
# Usage:
#   make up                     # build + start everything
#   make down                   # stop everything (data preserved)
#   make logs SVC=judge         # follow logs of one service
#   make restore FILE=dump.sql  # restore a database backup
#   make deploy-scheme PROBLEM=max-of-list

MANAGE := ./manage.sh
SVC ?=

.DEFAULT_GOAL := help

.PHONY: help init up down restart rebuild status health logs gen-cert check-django verify \
        create-admin migrate collectstatic shell dbshell backup restore \
        deploy-scheme destroy

help: ## Show available targets
	@grep -E '^[a-zA-Z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

# --- Lifecycle ----------------------------------------------------------------

init: ## First-time setup: .env, secrets, cert, build, start
	$(MANAGE) init

up: ## Build (if needed) and start all services
	$(MANAGE) start

down: ## Stop all services (data preserved)
	$(MANAGE) stop

restart: ## Restart all services, or one with SVC=<name>
	$(MANAGE) restart $(SVC)

rebuild: ## Rebuild and restart all services, or one with SVC=<name>
	$(MANAGE) rebuild $(SVC)

status: ## Show service status
	$(MANAGE) status

health: ## Show health of all services
	$(MANAGE) health

logs: ## Follow logs (one service with SVC=<name>)
	$(MANAGE) logs $(SVC)

destroy: ## Stop and remove all volumes (CAUTION: deletes data)
	$(MANAGE) destroy

# --- Setup / checks -----------------------------------------------------------

gen-cert: ## (Re)generate self-signed TLS certificate for HOST_IP
	$(MANAGE) gen-cert

check-django: ## Run Django system checks
	$(MANAGE) check

verify: ## End-to-end check: endpoints + judge a reference solution (PROBLEM=<code>)
	$(MANAGE) verify $(PROBLEM)

# --- Django -------------------------------------------------------------------

create-admin: ## Create a superuser account interactively
	$(MANAGE) create-admin

migrate: ## Run database migrations
	$(MANAGE) migrate

collectstatic: ## Collect static files and restart nginx
	$(MANAGE) collectstatic

shell: ## Open Django interactive shell
	$(MANAGE) shell

# --- Database -----------------------------------------------------------------

dbshell: ## Open MySQL shell
	$(MANAGE) dbshell

backup: ## Dump database (optional FILE=<name.sql>)
	$(MANAGE) backup $(FILE)

restore: ## Restore database from FILE=<name.sql>
	$(MANAGE) restore $(FILE)

# --- Problems -----------------------------------------------------------------

deploy-scheme: ## Deploy R5RS unit-test problem: PROBLEM=<code>
	$(MANAGE) deploy-scheme-problem $(PROBLEM)
