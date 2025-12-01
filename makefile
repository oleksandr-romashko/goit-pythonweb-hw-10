# ----------------------------------
# Makefile for Docker Compose project
# ----------------------------------

COMPOSE=docker compose
BASE_COMPOSE=-f compose.yaml
DEV_COMPOSE=$(BASE_COMPOSE) -f compose.dev.override.yml
PROFILE=--profile tools

.PHONY: dev prod clean logs stop rebuild restart shell migrate

## Run development environment
dev:
	$(COMPOSE) $(DEV_COMPOSE) $(PROFILE) up --build

## Run production environment (detached)
prod:
	$(COMPOSE) $(BASE_COMPOSE) $(PROFILE) up --build -d

## Stop and remove containers + volumes
clean:
	$(COMPOSE) $(PROFILE) down -v

## Show logs
logs:
	$(COMPOSE) logs -f

## Stop all containers
stop:
	$(COMPOSE) $(PROFILE) down

## Rebuild containers
rebuild:
	$(COMPOSE) $(DEV_COMPOSE) $(PROFILE) up --build --force-recreate

## Restart environment
restart: stop dev

## Open API service shell
shell:
	$(COMPOSE) exec api sh

## Run alembic migrations
migrate:
	$(COMPOSE) exec api poetry run alembic upgrade head