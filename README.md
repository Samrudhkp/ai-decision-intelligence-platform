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

> **Current status:** repository scaffold only. Machine learning models are **not** implemented yet. This phase establishes structure, dependencies, configuration templates, and documentation for GitHub publication.

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

### 5. Verify the scaffold

```bash
pytest
```

---

## Run instructions

### FastAPI (scaffold)

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- Root: http://127.0.0.1:8000/  
- Health: http://127.0.0.1:8000/health  
- Interactive docs: http://127.0.0.1:8000/docs  

### Streamlit dashboard (scaffold)

```bash
streamlit run app/dashboard.py
```

Open the URL shown in the terminal (default http://127.0.0.1:8501).

### MLflow UI (when experiments exist)

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

| Phase | Scope |
|-------|--------|
| **0 (this)** | Structure, README, requirements, `.env.example`, `.gitignore`, API/dashboard stubs |
| **1** | Sample/synthetic data contracts + churn model training & comparison |
| **2** | K-Means segmentation |
| **3** | Baseline + PyTorch revenue forecasting |
| **4** | SHAP explanations |
| **5** | MLflow experiment tracking end-to-end |
| **6** | FastAPI prediction endpoints |
| **7** | Streamlit dashboard views |
| **8** | Azure Blob + Azure ML wiring |

---

## Screenshots

> Placeholder — add UI captures after the dashboard and API are implemented.

| View | Description | Image |
|------|-------------|-------|
| Dashboard home | Overview of platform modules | _TBD_ |
| Churn results | Model comparison metrics | _TBD_ |
| Segmentation | Cluster profiles | _TBD_ |
| Forecasting | Revenue forecast chart | _TBD_ |
| SHAP | Local / global explanations | _TBD_ |

---

## Results

> Placeholder — publish evaluation tables and charts after models are trained.

### Churn model comparison

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|----|---------|
| Logistic Regression | — | — | — | — | — |
| Random Forest | — | — | — | — | — |
| XGBoost | — | — | — | — | — |

### Segmentation

- Number of clusters: _TBD_  
- Segment summaries: _TBD_  

### Revenue forecasting

- Baseline metric (e.g. MAE / MAPE): _TBD_  
- PyTorch model metric: _TBD_  

---

## Security & GitHub readiness

- [x] `.gitignore` for Python, venvs, models, datasets, secrets  
- [x] `.env.example` without real credentials  
- [x] No API keys or connection strings in the repository  
- [x] Professional README with architecture and setup  
- [ ] Initialize remotes / push when you are ready (not done in this phase)  

---

## License

Specify a license (e.g. MIT, Apache-2.0) before publishing publicly.

---

## Contributing

Phased contributions preferred: implement one capability at a time (see Roadmap), keep secrets out of commits, and add tests with each feature.
