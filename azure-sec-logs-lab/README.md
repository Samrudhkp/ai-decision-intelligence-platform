# Azure Event-Driven Security Lab

Small **event-driven security pipeline on Azure** (interview / portfolio lab):

> Upload fictional login logs to **Blob Storage**; **Event Grid** detects the new file and triggers a Python **Azure Function**; the function counts failed logins, flags accounts with **five or more** failures, and writes a JSON report back to Blob Storage.  
> It’s the Azure version of a Cloud Storage → Eventarc → Cloud Functions flow.

```
Upload login-log-alice-flagged.json → Blob Storage (logs)
        ↓
Event Grid sees “BlobCreated”
        ↓
Azure Function AnalyzeLoginLog runs
        ↓
Report lands in Blob Storage (reports)
        ↓
Open report → alice flagged (5 failed logins)
```

---

## 30-second interview pitch

“I built a small event-driven security pipeline on Azure. I upload fictional login logs to Blob Storage; Event Grid detects the new file and triggers a Python Azure Function; the function counts failed logins, flags accounts with five or more failures, and writes a JSON report back to Blob Storage. It’s the Azure version of a Cloud Storage → Eventarc → Cloud Functions flow.”

---

## Components

| Component | Name (default) | Role |
|-----------|----------------|------|
| Resource Group | `rg-sec-logs-lab` | One unit to create/tear down the lab |
| Storage Account | `stseclogs******` | Object storage (like GCS) |
| Blob container `logs` | input | Login-log JSON uploads |
| Blob container `reports` | output | Analyzer JSON reports |
| Event Grid | system topic + subscription | Watches `BlobCreated` on `logs` |
| Azure Function | `AnalyzeLoginLog` | Serverless Python analyzer |
| Hosting plan | `EastUSLinuxDynamicPlan` (Consumption / Y1) | Near-zero cost when idle |

### GCP ↔ Azure cheat sheet

| GCP | Azure in this lab |
|-----|-------------------|
| Cloud Storage bucket | Blob Storage container |
| Eventarc | Event Grid |
| Cloud Functions | Azure Functions |
| Project / cleanup | Resource group delete |

---

## Repository layout

```
azure-sec-logs-lab/
├── function_app/          # Python Azure Function (v2 programming model)
│   ├── function_app.py    # Event Grid trigger
│   ├── analyzer.py        # Pure analysis logic
│   ├── host.json
│   └── requirements.txt
├── infra/                 # Bicep (RG, Storage, Function, Event Grid)
├── sample_logs/           # Fictional login logs (alice flagged + clean)
├── scripts/deploy.sh      # Deploy + upload sample + wait for report
├── scripts/teardown.sh    # az group delete
├── tests/                 # Local unit tests (no Azure required)
└── .env.example           # Secrets template — never commit .env
```

---

## Prerequisites

- Azure pay-as-you-go (or free) subscription  
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)  
- Python 3.10+ (for local tests)  
- Auth via `az login` **or** service principal:

```bash
export AZURE_SUBSCRIPTION_ID=...
export AZURE_TENANT_ID=...
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
az login --service-principal \
  -u "$AZURE_CLIENT_ID" \
  -p "$AZURE_CLIENT_SECRET" \
  --tenant "$AZURE_TENANT_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

**Never commit credentials.** Copy `.env.example` → `.env` for local use only.

---

## Deploy (spend: Consumption plan ≈ $0 when idle)

```bash
cd azure-sec-logs-lab
chmod +x scripts/*.sh
./scripts/deploy.sh
```

What the script does:

1. Deploys Bicep at subscription scope (creates `rg-sec-logs-lab` + resources)  
2. Zip-deploys the Python function  
3. Uploads `sample_logs/login-log-alice-flagged.json` to `logs`  
4. Polls `reports` for `login-log-alice-flagged-report.json`  

### Tear down

```bash
./scripts/teardown.sh
# or: az group delete --name rg-sec-logs-lab --yes
```

---

## Local tests (no cloud)

```bash
cd azure-sec-logs-lab
python3 -m pytest tests/ -q
```

---

## Expected report shape

```json
{
  "failure_threshold": 5,
  "flagged_accounts": [
    {"username": "alice", "failed_logins": 5}
  ],
  "source_blob": "logs/login-log-alice-flagged.json",
  "summary": "1 account(s) flagged with >=5 failed logins"
}
```

---

## Security notes

- No public blob access  
- HTTPS only / TLS 1.2 on storage  
- Secrets via env / Key Vault later — not in source  
- Lab is fictional logs only (no real PII)

---

## Status

| Step | Status |
|------|--------|
| Function + analyzer code | Ready |
| Bicep + deploy/teardown scripts | Ready |
| Sample logs + local tests | Ready |
| Live Azure deploy | **Blocked until Azure credentials are provided to this agent** |
