# Makefile for Video Upscaling Application

# Default target
.PHONY: help
help:
	@echo "Video Upscaling Application Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make setup          - Install dependencies"
	@echo "  make run            - Run the upscaling application"
	@echo "  make server         - Start the API server"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Clean temporary files"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make help           - Show this help message"

# Install dependencies
.PHONY: setup
setup:
	./setup.sh

# Run the upscaling application (example)
.PHONY: run
run:
	python upscale_app.py

# Start the API server
.PHONY: server
server:
	python server.py

# Run tests
.PHONY: test
test:
	python test_upscale.py

# Clean temporary files
.PHONY: clean
clean:
	rm -f *.mp4
	rm -f *.log
	rm -rf temp_*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Build Docker image
.PHONY: docker-build
docker-build:
	docker build -t video-upscale .

# Run Docker container
.PHONY: docker-run
docker-run:
	docker run --gpus all -it video-upscale

# Show file structure
.PHONY: tree
tree:
	ls -la

# Install Python dependencies only
.PHONY: install-deps
install-deps:
	pip install -r requirements.txt