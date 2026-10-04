"""Streamlit dashboard for Decision Intelligence Platform."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.churn.train import predict_churn
from src.segmentation.cluster import predict_segments


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _customer_form(prefix: str) -> dict:
    c1, c2, c3 = st.columns(3)
    with c1:
        tenure_months = st.number_input("Tenure (months)", 0, 120, 8, key=f"{prefix}_tenure")
        monthly_charges = st.number_input("Monthly charges", 0.0, 300.0, 95.0, key=f"{prefix}_monthly")
        total_charges = st.number_input("Total charges", 0.0, 20000.0, 760.0, key=f"{prefix}_total")
    with c2:
        contract_type = st.selectbox(
            "Contract",
            ["month-to-month", "one-year", "two-year"],
            key=f"{prefix}_contract",
        )
        internet_service = st.selectbox(
            "Internet",
            ["fiber", "dsl", "none"],
            key=f"{prefix}_internet",
        )
    with c3:
        support_tickets = st.number_input("Support tickets", 0, 30, 3, key=f"{prefix}_tickets")
        payment_delay_days = st.number_input(
            "Payment delay (days)", 0.0, 60.0, 10.0, key=f"{prefix}_delay"
        )
    return {
        "tenure_months": int(tenure_months),
        "monthly_charges": float(monthly_charges),
        "total_charges": float(total_charges),
        "contract_type": contract_type,
        "internet_service": internet_service,
        "support_tickets": int(support_tickets),
        "payment_delay_days": float(payment_delay_days),
    }


def main() -> None:
    st.set_page_config(
        page_title="Decision Intelligence Platform",
        layout="wide",
    )
    st.title("Decision Intelligence Platform")
    st.caption("Churn · Segmentation · Revenue forecasting · SHAP · Azure")

    tab_overview, tab_churn, tab_segments, tab_forecast, tab_shap = st.tabs(
        ["Overview", "Churn", "Segmentation", "Forecasting", "SHAP"]
    )

    with tab_overview:
        st.subheader("Platform status")
        checks = {
            "Churn comparison": Path("models/churn/comparison.json").exists(),
            "Segmentation profiles": Path("models/segmentation/segment_profiles.json").exists(),
            "Baseline forecast": Path("models/forecasting/baseline_forecast.json").exists(),
            "PyTorch forecast": Path("models/forecasting/pytorch_forecast.json").exists(),
            "SHAP summary": Path("models/explainability/metadata.json").exists(),
        }
        st.dataframe(
            pd.DataFrame(
                [{"artifact": k, "ready": "yes" if v else "missing"} for k, v in checks.items()]
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            """
**Quick start**
1. `PYTHONPATH=. python scripts/run_pipeline.py --upload-azure`
2. API docs: `http://127.0.0.1:8000/docs`
3. Azure resources: see `docs/azure.md`
"""
        )

    with tab_churn:
        st.subheader("Model comparison")
        metrics = _load_json(Path("models/churn/comparison.json"))
        if metrics is None:
            st.warning("No churn metrics yet. Run the training pipeline.")
        else:
            frame = pd.DataFrame(metrics)
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.bar_chart(
                frame.set_index("model")[["accuracy", "precision", "recall", "f1", "roc_auc"]]
            )

        st.subheader("Score a customer")
        record = _customer_form("churn")
        if st.button("Predict churn", type="primary"):
            try:
                pred = predict_churn([record])[0]
                st.metric("Churn probability", f"{pred['churn_probability']:.1%}")
                st.write(
                    "Prediction:",
                    "Likely to churn" if pred["churn_predicted"] else "Likely to stay",
                )
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

    with tab_segments:
        st.subheader("Customer segments")
        profiles = _load_json(Path("models/segmentation/segment_profiles.json"))
        if profiles is None:
            st.warning("No segmentation profiles yet.")
        else:
            frame = pd.DataFrame(profiles)
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.bar_chart(frame.set_index("segment_name")["customers"])

        st.subheader("Assign a customer to a cluster")
        seg_record = _customer_form("seg")
        if st.button("Predict segment", type="primary"):
            try:
                cluster = predict_segments([seg_record])[0]
                name = "unknown"
                if profiles:
                    match = next((p for p in profiles if int(p["cluster"]) == cluster), None)
                    if match:
                        name = match.get("segment_name", "unknown")
                st.success(f"Cluster {cluster} — {name}")
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

    with tab_forecast:
        st.subheader("Revenue forecasts")
        baseline = _load_json(Path("models/forecasting/baseline_forecast.json"))
        pytorch = _load_json(Path("models/forecasting/pytorch_forecast.json"))
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Baseline (seasonal naive)**")
            if baseline is None:
                st.warning("Missing baseline forecast")
            else:
                st.json(baseline.get("metrics", {}))
                st.line_chart(
                    pd.DataFrame(baseline["future_forecast"]).set_index("month")["revenue"]
                )
        with col2:
            st.markdown("**PyTorch LSTM**")
            if pytorch is None:
                st.warning("Missing PyTorch forecast")
            else:
                st.json(pytorch.get("metrics", {}))
                st.line_chart(
                    pd.DataFrame(pytorch["future_forecast"]).set_index("month")["revenue"]
                )

    with tab_shap:
        st.subheader("Explainability")
        meta = _load_json(Path("models/explainability/metadata.json"))
        plot = Path("models/explainability/shap_summary.png")
        if meta is None:
            st.warning("No SHAP artifacts yet.")
        else:
            st.dataframe(
                pd.DataFrame(meta.get("top_features", [])),
                use_container_width=True,
                hide_index=True,
            )
            if plot.exists():
                st.image(str(plot))
            st.markdown("Local example")
            st.json(meta.get("local_example", {}))


if __name__ == "__main__":
    main()
