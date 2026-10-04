#!/usr/bin/env make
.PHONY: help install data train upload test api dashboard all clean-azure-lab

help:
	@echo "Decision Intelligence Platform"
	@echo "  make install    - pip install requirements"
	@echo "  make data       - generate synthetic datasets"
	@echo "  make train      - train all models locally"
	@echo "  make upload     - train + upload artifacts to Azure Blob"
	@echo "  make test       - run pytest"
	@echo "  make api        - run FastAPI on :8000"
	@echo "  make dashboard  - run Streamlit on :8501"
	@echo "  make all        - install, upload pipeline, test"

install:
	pip install -r requirements.txt

data:
	PYTHONPATH=. python -c "from src.utils.data_generation import write_datasets; print(write_datasets())"

train:
	PYTHONPATH=. python scripts/run_pipeline.py

upload:
	PYTHONPATH=. python scripts/run_pipeline.py --upload-azure

test:
	PYTHONPATH=. pytest -q

api:
	PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	PYTHONPATH=. streamlit run app/dashboard.py --server.port 8501

all: install upload test
