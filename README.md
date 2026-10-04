# Decision Intelligence Platform

Professional README for GitHub publication. Screenshots and results will be
added as features are implemented.

---

## Related Azure lab

This repo also includes a small event-driven Azure security lab under [`azure-sec-logs-lab/`](azure-sec-logs-lab/):

**Blob Storage (`logs`) → Event Grid → Azure Function (`AnalyzeLoginLog`) → Blob Storage (`reports`)**

See that folder’s README for the interview pitch, GCP↔Azure mapping, deploy/teardown scripts, and sample logs. Live deploy needs Azure credentials in the environment (not stored in git).

---

## Overview

Enterprise **AI forecasting and decision intelligence** platform in Python for:

1. **Customer churn prediction** — Logistic Regression, Random Forest, XGBoost with accuracy, precision, recall, F1, and ROC-AUC comparison  
2. **Customer segmentation** — K-Means clustering to identify meaningful customer groups  
3. **Revenue forecasting** — baseline model, then a PyTorch neural-network forecaster  
4. **Explainable AI** — SHAP explanations of model predictions  
5. **Experiment tracking** — MLflow  
6. **API** — FastAPI backend for predictions  
7. **Dashboard** — Streamlit UI for predictions, clusters, forecasts, and SHAP  
8. **Azure integration** — raw datasets in Azure Blob Storage; future train/deploy with Azure Machine Learning (credentials via environment variables / Azure auth only)

> **Current status:** core platform implemented end-to-end on synthetic data, with artifacts uploaded to Azure Blob Storage (`rg-decision-intelligence` / `stdipfd2177`). Run `python scripts/run_pipeline.py --upload-azure` to retrain and refresh cloud files.

---

## Project architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Streamlit App  │────▶│  FastAPI Backend │────▶│  Trained Models     │
│  (app/)         │     │  (api/)          │     │  (models/ + MLflow) │
└─────────────────┘     └────────┬─────────┘     └──────────▲──────────┘
                                 │                          │
                                 ▼                          │
                        ┌────────────────┐         ┌────────┴────────┐
                        │  src/ pipelines│────────▶│  MLflow Tracking│
                        │  churn / seg / │         └─────────────────┘
                        │  forecast /    │
                        │  explain / util│
                        └────────┬───────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       data/raw|processed   Azure Blob Storage   Azure ML (future)
```

| Path | Role |
|------|------|
| `data/` | Local raw / processed / external datasets (gitignored contents) |
| `notebooks/` | Exploratory analysis and prototyping |
| `src/` | Core ML and utility packages (churn, segmentation, forecasting, explainability, utils) |
| `models/` | Serialized model artifacts (gitignored except `.gitkeep`) |
| `api/` | FastAPI application and routers |
| `app/` | Streamlit dashboard |
| `tests/` | Unit and integration tests |
| `requirements.txt` | Python dependencies |
| `.env.example` | Documented environment variables (no secrets) |
| `.gitignore` | Python, venvs, models, datasets, secrets |

---

## Technologies used

| Area | Technology |
|------|------------|
| Language | Python 3.10+ |
| Data / classical ML | NumPy, pandas, scikit-learn, XGBoost |
| Deep learning | PyTorch |
| Explainability | SHAP, Matplotlib, Seaborn |
| Experiment tracking | MLflow |
| API | FastAPI, Uvicorn, Pydantic |
| Dashboard | Streamlit, Plotly |
| Cloud | Azure Blob Storage, Azure Identity, Azure ML SDK |
| Config | python-dotenv, pydantic-settings |
| Testing | pytest, httpx, ruff |

---

## Setup

### Prerequisites

- Python 3.10 or later  
- Git  
- (Optional) Azure CLI for `az login` / DefaultAzureCredential  
- (Optional) Docker if you containerize later  

### 1. Clone the repository

```bash
git clone <your-github-repo-url>
cd <repo-name>
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with local paths and Azure settings as needed.
# Never commit .env or real credentials.
```

### 5. Generate data, train models, upload to Azure

```bash
python scripts/run_pipeline.py --upload-azure
pytest
```

---

## Run instructions

### FastAPI

```bash
PYTHONPATH=. uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- Root: http://127.0.0.1:8000/  
- Health: http://127.0.0.1:8000/health  
- Docs: http://127.0.0.1:8000/docs  
- Churn metrics: http://127.0.0.1:8000/churn/metrics  
- Segments: http://127.0.0.1:8000/segmentation/profiles  
- Forecasts: http://127.0.0.1:8000/forecast/pytorch  
- SHAP: http://127.0.0.1:8000/explain/shap  

### Streamlit dashboard

```bash
PYTHONPATH=. streamlit run app/dashboard.py
```

Open the URL shown in the terminal (default http://127.0.0.1:8501).

### MLflow UI

```bash
mlflow ui --backend-store-uri ./mlruns --port 5000
```

---

## Azure credentials (no secrets in source)

- **Do not** put API keys, connection strings, or passwords in code or in committed files.  
- Copy `.env.example` → `.env` and fill values locally; `.env` is gitignored.  
- Prefer **Azure CLI** (`az login`) or **managed identity** with `DefaultAzureCredential`.  
- For CI, use service principal env vars (`AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`) injected by the secret store — never checked into Git.  
- Optional local Blob access: `AZURE_STORAGE_CONNECTION_STRING` in `.env` only.  

### Azure platform resources

See [`docs/azure.md`](docs/azure.md) for the live resource group / Blob Storage setup used by this project:

```bash
./scripts/provision_azure_platform.sh   # RG + storage + raw/processed containers
python -m src.utils.azure_storage smoke # upload smoke test to raw-datasets
./scripts/teardown_azure_platform.sh    # delete the whole RG when done
```

---

## Roadmap (phased delivery)

| Phase | Scope | Status |
|-------|--------|--------|
| **0** | Structure, README, requirements, `.env.example`, `.gitignore` | Done |
| **1** | Synthetic data + churn model comparison | Done |
| **2** | K-Means segmentation | Done |
| **3** | Baseline + PyTorch revenue forecasting | Done |
| **4** | SHAP explanations | Done |
| **5** | MLflow experiment tracking | Done |
| **6** | FastAPI prediction endpoints | Done |
| **7** | Streamlit dashboard (metrics + interactive scoring) | Done |
| **8** | Azure Blob + minimal Azure ML workspace (no paid compute) | Done |

---

## Screenshots

Run locally and capture from:

- Streamlit: `make dashboard` → http://127.0.0.1:8501  
- API docs: `make api` → http://127.0.0.1:8000/docs  
- Azure ML Studio: see [`docs/azure.md`](docs/azure.md)

| View | Description |
|------|-------------|
| Dashboard Overview | Artifact readiness table |
| Churn | Metrics chart + interactive scorer |
| Segmentation | Cluster profiles + assignment |
| Forecasting | Baseline vs PyTorch charts |
| SHAP | Feature importance + summary plot |

---

## Results

Synthetic demo run (2,000 customers, 48 months revenue). Best churn model by ROC-AUC: **logistic_regression**.

### Churn model comparison

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | 0.690 | 0.241 | 0.714 | 0.361 | **0.772** |
| Random Forest | 0.858 | 0.375 | 0.245 | 0.296 | 0.733 |
| XGBoost | 0.808 | 0.294 | 0.408 | 0.342 | 0.730 |

### Segmentation (K=4)

| Segment | Customers | Avg tenure | Avg monthly $ | Churn rate |
|---------|-----------|------------|---------------|------------|
| high_value_at_risk | 596 | 16.4 | 82.2 | 0.232 |
| loyal_premium | 656 | 55.7 | 82.8 | 0.070 |
| value_seekers | 559 | 34.0 | 42.7 | 0.052 |
| steady_core | 189 | 35.5 | 63.3 | 0.175 |

### Revenue forecasting

| Model | MAE | MAPE |
|-------|-----|------|
| Baseline (seasonal naive) | 23,457 | 12.02% |
| PyTorch LSTM | **13,032** | **6.72%** |

Artifacts also live in Azure `processed-datasets/` (see [`docs/azure.md`](docs/azure.md)).

---

## Security & GitHub readiness

- [x] `.gitignore` for Python, venvs, models, datasets, secrets  
- [x] `.env.example` without real credentials  
- [x] No API keys or connection strings in the repository  
- [x] Professional README with architecture and setup  
- [x] MIT `LICENSE`  
- [x] Azure resources use CLI / `DefaultAzureCredential` patterns  
- [x] Azure ML workspace created **without** paid compute VMs  

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Contributing

Use `make help` for common tasks. Keep secrets out of commits, prefer `scripts/run_pipeline.py` for retraining, and add tests with each feature.
