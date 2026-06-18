.PHONY: dev migrate seed mongoseed install setup

DB_USER ?= root
DB_NAME ?= pokezoo

dev:
	python -m uvicorn app.main:app --reload

migrate:
	@echo "Running MySQL schema migration..."
	mysql -u $(DB_USER) -p $(DB_NAME) < database/schema.sql

seed:
	@echo "Seeding MySQL data..."
	mysql -u $(DB_USER) -p $(DB_NAME) < database/seed.sql

mongoseed:
	@echo "Seeding MongoDB data..."
	mongosh $(DB_NAME) database/mongo_seed.js

install:
	pip install -r requirements.txt --break-system-packages

setup: install migrate seed mongoseed
	@echo "Setup complete! You can now run 'make dev' to start the server."
