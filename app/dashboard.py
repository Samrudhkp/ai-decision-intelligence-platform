"""Streamlit dashboard entrypoint.

Pages for predictions, clusters, forecasts, and SHAP will be added later.
Run (after install): streamlit run app/dashboard.py
"""

from __future__ import annotations

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Decision Intelligence Platform",
        page_icon=None,
        layout="wide",
    )
    st.title("Decision Intelligence Platform")
    st.markdown(
        """
        Enterprise AI forecasting and decision intelligence dashboard.

        **Coming in later phases**
        - Customer churn predictions and model comparison
        - Customer segmentation (K-Means clusters)
        - Revenue forecasts (baseline + PyTorch)
        - SHAP explanations
        - MLflow experiment links
        """
    )
    st.info(
        "Scaffold only — models and visualizations are not implemented yet.",
        icon=None,
    )


if __name__ == "__main__":
    main()
