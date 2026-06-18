.PHONY: dev createdb migrate seed mongoseed install setup

DB_USER ?= root
DB_NAME ?= pokezoo
MONGO_DB_NAME ?= pokezoo

dev:
	uvicorn app.main:app --reload

pdev:
	python3 -m uvicorn app.main:app --reload

createdb:
	mysql -u $(DB_USER) -p -e "CREATE DATABASE IF NOT EXISTS $(DB_NAME);"

migrate:
	@echo "Running MySQL schema migration..."
	mysql -u $(DB_USER) -p $(DB_NAME) < database/schema.sql

seed:
	@echo "Seeding MySQL data..."
	mysql -u $(DB_USER) -p $(DB_NAME) < database/seed.sql

mongoseed:
	@echo "Seeding MongoDB data..."
	mongosh $(MONGO_DB_NAME) database/mongo_seed.js

install:
	pip install -r requirements.txt --break-system-packages

setup: install createdb migrate seed mongoseed
	@echo "Setup complete! You can now run 'make dev' to start the server."
