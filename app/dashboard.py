"""Streamlit dashboard for Decision Intelligence Platform."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    st.set_page_config(
        page_title="Decision Intelligence Platform",
        layout="wide",
    )
    st.title("Decision Intelligence Platform")
    st.caption("Churn · Segmentation · Revenue forecasting · SHAP")

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
            "Train everything with: `python scripts/run_pipeline.py --upload-azure`"
        )

    with tab_churn:
        st.subheader("Model comparison")
        metrics = _load_json(Path("models/churn/comparison.json"))
        if metrics is None:
            st.warning("No churn metrics yet. Run the training pipeline.")
        else:
            frame = pd.DataFrame(metrics)
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.bar_chart(frame.set_index("model")[["accuracy", "precision", "recall", "f1", "roc_auc"]])

    with tab_segments:
        st.subheader("Customer segments")
        profiles = _load_json(Path("models/segmentation/segment_profiles.json"))
        if profiles is None:
            st.warning("No segmentation profiles yet.")
        else:
            frame = pd.DataFrame(profiles)
            st.dataframe(frame, use_container_width=True, hide_index=True)
            st.bar_chart(frame.set_index("segment_name")["customers"])

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
            st.dataframe(pd.DataFrame(meta.get("top_features", [])), use_container_width=True, hide_index=True)
            if plot.exists():
                st.image(str(plot))
            st.markdown("Local example")
            st.json(meta.get("local_example", {}))


if __name__ == "__main__":
    main()
