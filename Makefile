# Makefile for SplitNotes cross-platform builds

# Variables
PYTHON := python3
PIP := pip3
APP_NAME := SplitNotes
VERSION := 1.0.0

# Default target
.PHONY: help
help:
	@echo "SplitNotes Build System"
	@echo "======================"
	@echo ""
	@echo "Available targets:"
	@echo "  setup          - Install build dependencies"
	@echo "  run            - Run from source"
	@echo "  clean          - Clean build artifacts"
	@echo "  build-windows  - Build Windows executable"
	@echo "  build-macos    - Build macOS application"
	@echo "  build-linux    - Build Linux executable"
	@echo "  build-all      - Build for all platforms (if tools available)"
	@echo "  package-linux  - Create Linux package structure"
	@echo "  test           - Run basic tests"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code with black"
	@echo ""

# Setup development environment
.PHONY: setup
setup:
	@echo "Setting up development environment..."
	$(PIP) install --upgrade pip
	@echo "Basic setup complete."
	@echo ""
	@echo "For building, install platform-specific tools:"
	@echo "  Windows: pip install cx_Freeze py2exe"
	@echo "  macOS:   pip install py2app"
	@echo "  Linux:   pip install cx_Freeze"

# Run from source
.PHONY: run
run:
	@echo "Running SplitNotes from source..."
	$(PYTHON) main_window.py

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf __pycache__/
	rm -rf resources/__pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	@echo "Clean complete."

# Build Windows executable
.PHONY: build-windows
build-windows:
	@echo "Building Windows executable..."
	@if command -v python >/dev/null 2>&1; then \
		python setup_windows.py build; \
	else \
		echo "Error: Python not found. Install Python for Windows."; \
		exit 1; \
	fi
	@echo "Windows build complete. Check build/ directory."

# Build macOS application
.PHONY: build-macos
build-macos:
	@echo "Building macOS application..."
	@if [ "$$(uname)" = "Darwin" ]; then \
		$(PYTHON) setup_mac.py py2app; \
		echo "macOS build complete. Check dist/ directory."; \
	else \
		echo "Error: macOS build must be run on macOS."; \
		exit 1; \
	fi

# Build Linux executable  
.PHONY: build-linux
build-linux:
	@echo "Building Linux executable..."
	$(PYTHON) setup_linux.py build
	@echo "Linux build complete. Check build/ directory."

# Create Linux package structure
.PHONY: package-linux
package-linux: build-linux
	@echo "Creating Linux package..."
	$(PYTHON) setup_linux.py package
	@echo "Linux package complete."

# Build for all platforms (if tools are available)
.PHONY: build-all
build-all:
	@echo "Building for all available platforms..."
	@if command -v python >/dev/null 2>&1 && python -c "import cx_Freeze" 2>/dev/null; then \
		echo "Building Windows..."; \
		make build-windows; \
	else \
		echo "Skipping Windows build (cx_Freeze not available)"; \
	fi
	@if [ "$$(uname)" = "Darwin" ] && $(PYTHON) -c "import py2app" 2>/dev/null; then \
		echo "Building macOS..."; \
		make build-macos; \
	else \
		echo "Skipping macOS build (not on macOS or py2app not available)"; \
	fi
	@if $(PYTHON) -c "import cx_Freeze" 2>/dev/null; then \
		echo "Building Linux..."; \
		make build-linux; \
	else \
		echo "Skipping Linux build (cx_Freeze not available)"; \
	fi

# Basic functionality test
.PHONY: test
test:
	@echo "Running basic tests..."
	@echo "Testing imports..."
	$(PYTHON) -c "import config; import ls_connection; import note_reader; import setting_handler; print('All modules imported successfully')"
	@echo "Testing configuration..."
	$(PYTHON) -c "import config; print(f'App: {config.APP_NAME} v{config.APP_VERSION}')"
	@echo "Testing note parsing..."
	@echo "Test note 1\n\nTest note 2" > test_notes.txt
	$(PYTHON) -c "import note_reader; notes = note_reader.get_notes('test_notes.txt', 'new_line'); print(f'Parsed {len(notes)} notes')"
	rm -f test_notes.txt
	@echo "Basic tests passed."

# Code linting (if flake8 is available)
.PHONY: lint
lint:
	@if $(PYTHON) -c "import flake8" 2>/dev/null; then \
		echo "Running flake8 linting..."; \
		$(PYTHON) -m flake8 *.py --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "flake8 not available. Install with: pip install flake8"; \
	fi

# Code formatting (if black is available)
.PHONY: format
format:
	@if $(PYTHON) -c "import black" 2>/dev/null; then \
		echo "Formatting code with black..."; \
		$(PYTHON) -m black *.py --line-length=100; \
	else \
		echo "black not available. Install with: pip install black"; \
	fi

# Create resources directory with placeholder files
.PHONY: setup-resources
setup-resources:
	@echo "Setting up resources directory..."
	@mkdir -p resources
	@if [ ! -f resources/green.png ]; then \
		echo "Creating placeholder green.png..."; \
		touch resources/green.png; \
	fi
	@if [ ! -f resources/red.png ]; then \
		echo "Creating placeholder red.png..."; \
		touch resources/red.png; \
	fi
	@if [ ! -f resources/settings_icon.png ]; then \
		echo "Creating placeholder settings_icon.png..."; \
		touch resources/settings_icon.png; \
	fi
	@echo "Resources directory ready. Replace placeholder files with actual icons."

# Development server (just runs the app)
.PHONY: dev
dev: run

# Show system information
.PHONY: info
info:
	@echo "System Information:"
	@echo "=================="
	@echo "OS: $$(uname -s)"
	@echo "Architecture: $$(uname -m)"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Python Path: $$(which $(PYTHON))"
	@echo ""
	@echo "Python Modules:"
	@$(PYTHON) -c "import sys; print('tkinter:', 'available' if 'tkinter' in sys.modules or __import__('tkinter') else 'missing')" 2>/dev/null || echo "tkinter: missing"
	@$(PYTHON) -c "import socket; print('socket: available')" 2>/dev/null || echo "socket: missing"
	@$(PYTHON) -c "import threading; print('threading: available')" 2>/dev/null || echo "threading: missing"