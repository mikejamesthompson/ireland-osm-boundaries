DEFAULT_GOAL := .venv

.venv: .venv/sentinel

.venv/sentinel: requirements.txt
	@echo "Creating virtual environment"
	@test -d .venv || python3 -m venv .venv
	@echo "Installing requirements"
	@source .venv/bin/activate && pip install -r requirements.txt
	@touch .venv/sentinel

requirements.txt: pyproject.toml
	@echo "Compiling requirements.txt from pyproject.toml"
	@pip-compile --generate-hashes --output-file requirements.txt pyproject.toml