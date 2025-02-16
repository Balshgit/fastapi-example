# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
WHITE  := $(shell tput -Txterm setaf 7)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

.DEFAULT_GOAL := help
.PHONY: help app format lint check-style lint-typing lint-complexity lint-deps up-dependencies down-dependencies

PYTHON_TARGETS = app tests
PORT=8000

## Запустить приложение
app:
	poetry run uvicorn --host 0.0.0.0 --factory app.main:create_app --port $(PORT) --reload --reload-dir=bot_microservice --reload-dir=settings

## Запустить зависимости
up-dependencies:
	docker compose up -d

## Остановить зависимости
down-dependencies:
	docker compose down -v

## Отформатировать код
format:
	black $(PYTHON_TARGETS) && ruff check --fix $(PYTHON_TARGETS)

## Проверить стилистику кода
style:
	ruff check $(PYTHON_TARGETS) && black --check $(PYTHON_TARGETS)


## Проверить типизацию
lint-typing:
	mypy $(PYTHON_TARGETS)

## Проверить код на сложность
lint-complexity:
	flake8 $(PYTHON_TARGETS)

## Запустить линтер ruff
lint-ruff:
	ruff check $(PYTHON_TARGETS)


## Запустить все линтеры
lint: style lint-typing lint-complexity lint-ruff

## Show help
help:
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-_0-9]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = $$1; sub(/:$$/, "", helpCommand); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf "  ${YELLOW}%-$(TARGET_MAX_CHAR_NUM)25s${RESET} ${GREEN}%s${RESET}\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)
	@echo ''
