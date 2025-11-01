# Makefile for Jupyter Book

.PHONY: help build clean serve install

help:
	@echo "Systematic Trading Book - Make commands:"
	@echo ""
	@echo "  make install    Install all dependencies"
	@echo "  make build      Build the book"
	@echo "  make clean      Clean build artifacts"
	@echo "  make serve      Build and serve the book locally"
	@echo "  make pdf        Build PDF version (requires LaTeX)"
	@echo "  make test       Test all notebooks execute"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt

build:
	@echo "Building Jupyter Book..."
	jupyter-book build .

clean:
	@echo "Cleaning build artifacts..."
	jupyter-book clean . --all

serve: build
	@echo "Starting local server..."
	@echo "Open http://localhost:8000 in your browser"
	cd _build/html && python -m http.server 8000

pdf:
	@echo "Building PDF (requires LaTeX installation)..."
	jupyter-book build . --builder pdflatex

test:
	@echo "Testing all notebooks..."
	pytest --nbmake part*/*.ipynb -v
