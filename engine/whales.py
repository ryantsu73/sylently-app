# engine/whales.py

import streamlit as st
import pandas as pd
import numpy as np


def _generate_sample_data(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    fan_ids = [f"fan_{i+1:03d}" for i in range(n)]
    lifetime_spend = rng.gamma(shape=2.0, scale=20.0, size=n) + 5
    last_tip_days_ago = rng.integers(0, 90, size=n)
    tips_last_30 = rng.poisson(lam=1.2, size=n)

    df = pd.DataFrame(
        {
            "fan_id": fan_ids,
            "lifetime_spend": lifetime_spend.round(2),
            "last_tip_days_ago": last_tip_days_ago,
            "tips_last_30_days": tips_last_30,
        }
    )
    return df


def _score_segments(df: pd.DataFrame, whale_top_pct: float = 10.0) -> pd.DataFrame:
    df = df.copy()

    spend_threshold = np.percentile(df["lifetime_spend"], 100 - whale_top_pct)
    df["is_whale"] = df["lifetime_spend"] >= spend_threshold

    df["segment"] = "Regular"

    df.loc[
        (df["is_whale"]) & (df["last_tip_days_ago"] <= 14),
        "segment",
    ] = "Active whale"

    df.loc[
        (df["is_whale"]) & (df["last_tip_days_ago"] > 14),
        "segment",
    ] = "Whale – at risk"

    df.loc[
        (~df["is_whale"]) & (df["tips_last_30_days"] >= 3),
        "segment",
    ] = "Rising supporter"

    return df.sort_values("lifetime_spend", ascending=False)


def render_ui():
    st.subheader("🐋 Whale Radar")

    st.markdown(
        """
        Upload your fan revenue file or play with sample data.
        We'll flag **whales**, **rising supporters**, and **at-risk whales**.
        """
    )

    col_left, col_right = st.columns([2, 1])

    with col_left:
        uploaded = st.file_uploader(
            "Upload CSV with at least these columns: fan_id, lifetime_spend, last_tip_days_ago, tips_last_30_days",
            type=["csv"],
        )
    with col_right:
        use_sample = st.checkbox("Use sample data instead", value=uploaded is None)

    if uploaded is not None and not use_sample:
        try:
            df_raw = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"Could not read CSV: {e}")
            return
    else:
        df_raw = _generate_sample_data()

    required_cols = {"fan_id", "lifetime_spend", "last_tip_days_ago", "tips_last_30_days"}
    missing = required_cols - set(df_raw.columns)
    if missing:
        st.error(
            f"Missing required columns in your CSV: {', '.join(sorted(missing))}. "
            "Please add them and re-upload, or use the sample data."
        )
        st.dataframe(df_raw.head(), use_container_width=True)
        return

    whale_pct = st.slider(
        "Top % of fans to treat as whales (by lifetime spend)",
        min_value=5,
        max_value=30,
        value=10,
        step=1,
    )

    df_scored = _score_segments(df_raw, whale_top_pct=whale_pct)

    total_fans = len(df_scored)
    total_whales = int(df_scored["is_whale"].sum())
    active_whales = int(
        ((df_scored["segment"] == "Active whale")).sum()
    )
    at_risk_whales = int(
        ((df_scored["segment"] == "Whale – at risk")).sum()
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total fans", f"{total_fans}")
    col2.metric("Whales", f"{total_whales}")
    col3.metric("Active whales", f"{active_whales}")
    col4.metric("At-risk whales", f"{at_risk_whales}")

    st.markdown("#### Top fans by lifetime spend")
    st.dataframe(
        df_scored[["fan_id", "lifetime_spend", "last_tip_days_ago", "tips_last_30_days", "segment"]],
        use_container_width=True,
        height=380,
    )

    st.markdown("#### Suggested actions")
    st.markdown(
        """
        - **Active whales** → send playful thank-you + early access offers.
        - **Whales – at risk** → send a save-my-whale DM (acknowledge them + ask what they'd like more of).
        - **Rising supporters** → invite them to upgrade or join higher tiers.
        """
    )
