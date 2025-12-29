# engine/pricing_engine.py

import streamlit as st
import pandas as pd


def _simulate_scenarios(
    current_price: float,
    current_subs: int,
    candidate_prices,
    churn_pct: float,
    upgrade_pct: float,
):
    rows = []
    for price in candidate_prices:
        churn_rate = churn_pct / 100.0
        upgrade_rate = upgrade_pct / 100.0

        churned = int(current_subs * churn_rate)
        upgraded = int((current_subs - churned) * upgrade_rate)
        stayers = current_subs - churned - upgraded

        current_mrr = current_price * current_subs
        new_mrr = stayers * current_price + upgraded * price

        lift = new_mrr - current_mrr
        lift_pct = (lift / current_mrr * 100.0) if current_mrr > 0 else 0.0

        rows.append(
            {
                "Test price": price,
                "Stayers at old price": stayers,
                "Upgraded to test price": upgraded,
                "Churned fans": churned,
                "Current MRR": round(current_mrr, 2),
                "Projected MRR": round(new_mrr, 2),
                "MRR lift ($)": round(lift, 2),
                "MRR lift (%)": round(lift_pct, 2),
            }
        )

    return pd.DataFrame(rows)


def render_ui():
    st.subheader("🧪 Smart Price Test")

    st.markdown(
        """
        Model how changing your subscription price might affect MRR.
        This is a **simple simulator**, not financial advice.
        """
    )

    with st.form("price_test_form"):
        col1, col2 = st.columns(2)

        with col1:
            current_price = st.number_input(
                "Current monthly price ($)",
                min_value=0.0,
                value=20.0,
                step=1.0,
            )
            current_subs = st.number_input(
                "Active subscribers",
                min_value=0,
                value=200,
                step=10,
            )
            churn_pct = st.slider(
                "Estimated % of fans who will churn if you raise price",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=1.0,
            )

        with col2:
            min_test_price = st.number_input(
                "Lowest test price ($)",
                min_value=0.0,
                value=max(5.0, current_price * 0.8),
                step=1.0,
            )
            max_test_price = st.number_input(
                "Highest test price ($)",
                min_value=min_test_price,
                value=max(current_price * 1.8, min_test_price + 5.0),
                step=1.0,
            )
            num_steps = st.slider(
                "Number of price points to simulate",
                min_value=2,
                max_value=7,
                value=4,
            )
            upgrade_pct = st.slider(
                "% of remaining fans who will accept the new price",
                min_value=0.0,
                max_value=100.0,
                value=40.0,
                step=5.0,
            )

        submitted = st.form_submit_button("Run simulation")

    if not submitted:
        return

    if current_subs <= 0 or current_price <= 0:
        st.error("Please enter a positive current price and at least 1 subscriber.")
        return

    candidate_prices = [
        round(min_test_price + i * (max_test_price - min_test_price) / (num_steps - 1), 2)
        for i in range(num_steps)
    ]

    df = _simulate_scenarios(
        current_price=current_price,
        current_subs=current_subs,
        candidate_prices=candidate_prices,
        churn_pct=churn_pct,
        upgrade_pct=upgrade_pct,
    )

    current_mrr = current_price * current_subs
    best_row = df.iloc[df["Projected MRR"].idxmax()]

    st.markdown("### Results")

    col_a, col_b = st.columns(2)

    with col_a:
        st.metric("Current MRR", f"${current_mrr:,.2f}")
        st.metric(
            "Best projected MRR",
            f"${best_row['Projected MRR']:,.2f}",
            f"{best_row['MRR lift (%)']:+.1f}%",
        )

    with col_b:
        st.metric("Recommended test price", f"${best_row['Test price']:.2f}")
        st.metric(
            "MRR lift at recommended price",
            f"${best_row['MRR lift ($)']:,.2f}",
        )

    st.markdown("#### Scenario table")
    st.dataframe(df, use_container_width=True)

    st.markdown("#### MRR by price")
    chart_data = df[["Test price", "Projected MRR"]].set_index("Test price")
    st.bar_chart(chart_data)
