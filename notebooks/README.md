# Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_eda_churn_revenue.ipynb` | Quick EDA on synthetic churn + revenue data |

Generate data first:

```bash
PYTHONPATH=. python -c "from src.utils.data_generation import write_datasets; write_datasets()"
```

Do not commit notebooks that embed secrets, raw PII, or huge outputs.
