.PHONY: help setup verify build up down logs clean test lint format

help:
	@echo "College AI Chatbot System - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup      - Set up development environment"
	@echo "  make verify     - Verify project setup"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View service logs"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"

setup:
	@echo "Setting up development environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  Windows: venv\\Scripts\\activate"
	@echo "  Unix/Mac: source venv/bin/activate"
	@echo "Then run: pip install -r requirements.txt"

verify:
	@echo "Verifying project setup..."
	python verify_setup.py

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services started. Access them at:"
	@echo "  Auth Service: http://localhost:8000"
	@echo "  Chat Service: http://localhost:8001"
	@echo "  RAG Service: http://localhost:8002"
	@echo "  Document Service: http://localhost:8003"
	@echo "  Notification Service: http://localhost:8004"
	@echo "  Admin Service: http://localhost:8005"
	@echo "  Analytics Service: http://localhost:8006"

down:
	@echo "Stopping all services..."
	docker-compose down

logs:
	@echo "Viewing service logs..."
	docker-compose logs -f

clean:
	@echo "Cleaning up containers and volumes..."
	docker-compose down -v
	@echo "Cleanup complete."

test:
	@echo "Running tests..."
	pytest --cov=. --cov-report=html

lint:
	@echo "Running linting..."
	flake8 .
	mypy .

format:
	@echo "Formatting code..."
	black .
	isort .
	@echo "Code formatted."
