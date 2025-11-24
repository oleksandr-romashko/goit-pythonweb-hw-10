dev:
	docker compose -f compose.yaml -f compose.dev.override.yml --profile tools up --build

dev-full-reset:
	docker compose --profile tools down -v

prod:
	docker compose -f compose.yaml --profile tools up --build -d