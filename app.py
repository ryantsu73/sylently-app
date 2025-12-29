import streamlit as st
import pandas as pd

from engine.pricing_engine import run_creator_sim_core
from engine.whales import get_today_whales
from engine.dm_suggestions import generate_dm_suggestions


st.set_page_config(page_title="Sylently – Pricing Studio", layout="wide")

st.title("Sylently – Pricing & Revenue Studio (MVP)")
st.markdown(
    "Run price tests, spot whales, and get DM upsell ideas – all from one screen. "
    "_(Demo mode with simulated data.)_"
)

# ===============================
# Sidebar: feature switch
# ===============================

feature = st.sidebar.radio(
    "Feature",
    options=[
        "Smart Price Test",
        "AI Whale Picks",
        "AI DM Suggestions",
    ],
    index=0,
)


# ===============================
# Shared: default synthetic creators
# ===============================

DEFAULT_CREATORS = {
    "Aria (modest price up)": {
        "creator_name": "Aria",
        "creator_id": "CR_Aria",
        "true_price_arms": {
            "A": {"price": 10.0, "true_mean_revenue": 12.0, "true_churn": 0.20},
            "B": {"price": 11.5, "true_mean_revenue": 13.0, "true_churn": 0.21},
            "C": {"price": 13.0, "true_mean_revenue": 12.6, "true_churn": 0.26},
        },
        "seed": 999,
    },
    "Nova (higher WTP, price up)": {
        "creator_name": "Nova",
        "creator_id": "CR_Nova",
        "true_price_arms": {
            "A": {"price": 15.0, "true_mean_revenue": 17.0, "true_churn": 0.18},
            "B": {"price": 17.0, "true_mean_revenue": 19.2, "true_churn": 0.21},
            "C": {"price": 19.0, "true_mean_revenue": 19.5, "true_churn": 0.27},
        },
        "seed": 1234,
    },
    "Luna (baseline too high, price down)": {
        "creator_name": "Luna",
        "creator_id": "CR_Luna",
        "true_price_arms": {
            "A": {"price": 14.0, "true_mean_revenue": 14.5, "true_churn": 0.30},
            "B": {"price": 12.0, "true_mean_revenue": 15.3, "true_churn": 0.22},
            "C": {"price": 10.0, "true_mean_revenue": 14.0, "true_churn": 0.20},
        },
        "seed": 2025,
    },
}


# Make sure we have a place to store last run in session
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "last_events_df" not in st.session_state:
    st.session_state.last_events_df = None
if "current_config" not in st.session_state:
    first_key = list(DEFAULT_CREATORS.keys())[0]
    st.session_state.current_config = DEFAULT_CREATORS[first_key]


# ===============================
# Feature 1: Smart Price Test
# ===============================

if feature == "Smart Price Test":
    st.subheader("Smart Price Test – 21-day A/B/C")

    st.sidebar.header("Creator configuration")

    preset_name = st.sidebar.selectbox(
        "Preset creator",
        options=list(DEFAULT_CREATORS.keys()) + ["Custom"],
        index=0,
    )

    if preset_name != "Custom":
        cfg = DEFAULT_CREATORS[preset_name]
    else:
        cfg = st.session_state.current_config

    creator_name = st.sidebar.text_input("Creator name", value=cfg["creator_name"])
    creator_id = st.sidebar.text_input("Creator ID", value=cfg["creator_id"])
    seed = st.sidebar.number_input("Random seed", value=cfg.get("seed", 999), step=1)

    st.sidebar.markdown("### Price arms (A = baseline)")

    arms = {}
    for arm_key in ["A", "B", "C"]:
        st.sidebar.markdown(f"**Arm {arm_key}**")
        col1, col2, col3 = st.sidebar.columns(3)
        default_arm = cfg["true_price_arms"][arm_key]

        price = col1.number_input(
            f"Price {arm_key} ($)",
            key=f"price_{arm_key}",
            value=float(default_arm["price"]),
            step=0.5,
            format="%.2f",
        )
        mean_rev = col2.number_input(
            f"Mean rev {arm_key}",
            key=f"rev_{arm_key}",
            value=float(default_arm["true_mean_revenue"]),
            step=0.5,
            format="%.2f",
        )
        churn = col3.number_input(
            f"Churn {arm_key}",
            key=f"churn_{arm_key}",
            value=float(default_arm["true_churn"]),
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            format="%.2f",
        )

        arms[arm_key] = {
            "price": price,
            "true_mean_revenue": mean_rev,
            "true_churn": churn,
        }

    st.sidebar.markdown("### Guardrails & engine parameters")
    max_rel_churn_increase = st.sidebar.slider(
        "Max relative churn increase vs baseline",
        min_value=0.0,
        max_value=0.50,
        value=0.10,
        step=0.01,
        format="%.2f",
    )
    tau = st.sidebar.slider(
        "Churn guardrail confidence (tau)",
        min_value=0.5,
        max_value=0.99,
        value=0.90,
        step=0.01,
    )
    n_events = st.sidebar.number_input(
        "Simulated events (subscribers)",
        min_value=200,
        max_value=10000,
        value=1000,
        step=100,
    )

    run_button = st.sidebar.button("Run Sylently engine")

    # Store config so that "Custom" has memory
    st.session_state.current_config = {
        "creator_name": creator_name,
        "creator_id": creator_id,
        "true_price_arms": arms,
        "seed": int(seed),
    }

    if run_button:
        with st.spinner("Running Sylently engine..."):
            results = run_creator_sim_core(
                creator_name=creator_name,
                creator_id=creator_id,
                true_price_arms=arms,
                seed=int(seed),
                n_events=int(n_events),
                max_rel_churn_increase=float(max_rel_churn_increase),
                tau=float(tau),
            )

        # Save for other features
        st.session_state.last_results = results
        st.session_state.last_events_df = results["events_df"]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Creator", results["creator_name"])
        col_b.metric("Baseline price", f"${results['baseline_price']:.2f}")
        col_c.metric("Recommended price", f"${results['best_price']:.2f}")
        col_d.metric("Uplift vs baseline", f"{results['uplift_pct']:.1f}%")

        st.markdown("### Confidence & guardrails")
        st.write(
            f"- Confidence this price is ≥3% better than next-best: "
            f"**{results['prob_ge_3']:.1f}%**"
        )
        st.write(
            f"- Churn guardrail: max +{int(max_rel_churn_increase * 100)}% relative increase "
            f"vs baseline at {int(tau * 100)}% confidence."
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Posterior view by arm")
            st.dataframe(results["report_table"].sort_values("price_usd"))

        with col2:
            st.subheader("Churn guardrail status")
            st.dataframe(results["safe_df"].sort_values("price_usd"))

        st.subheader("Observed simulation results")
        st.dataframe(results["summary_obs"].sort_values("price_usd"))

        st.markdown(
            "_Note: This MVP runs on simulated subscribers to demonstrate "
            "Sylently's pricing engine. A production version would connect to live "
            "billing data (Stripe, Patreon, etc.)._"
        )
    else:
        st.info(
            "Choose a creator or customize the price arms in the sidebar, "
            "then click **Run Sylently engine** to see the recommendation."
        )


# ===============================
# Feature 2: AI Whale Picks
# ===============================

elif feature == "AI Whale Picks":
    st.subheader("Today’s AI Whale Picks – Top Spend Candidates")

    st.sidebar.info(
        "Whale picks are based on the most recent Smart Price Test run.\n\n"
        "Run a test first, then come back here."
    )

    events_df = st.session_state.last_events_df
    last_results = st.session_state.last_results

    if events_df is None or last_results is None:
        st.warning(
            "No price test run found. Go to **Smart Price Test**, run the engine, "
            "then return here to see whale picks."
        )
    else:
        creator_name = last_results["creator_name"]

        whales_df = get_today_whales(
            events_df=events_df,
            creator_name=creator_name,
            top_n=3,
        )

        st.markdown(
            f"These are the top **3 fans** most likely to spend more with {creator_name}, "
            "based on recent behavior."
        )

        for _, row in whales_df.iterrows():
            fan_id = row["fan_id"]
            spend = row["predicted_spend_30d"]
            price = row["last_price"]
            churned = bool(row["churned_any"])
            msg = row["ice_breaker"]

            with st.expander(
                f"{fan_id} – est. ${spend:.2f} in the next 30 days "
                f"@ ${price:.2f} ({'churned' if churned else 'active'})"
            ):
                st.write("**1-click ice-breaker DM:**")
                st.code(msg, language="text")

        st.markdown("### Raw whale table")
        st.dataframe(whales_df)


# ===============================
# Feature 3: AI DM Suggestions
# ===============================

elif feature == "AI DM Suggestions":
    st.subheader("AI DM Reply Suggestions – Flirty Upsells")

    st.sidebar.info(
        "This demo uses your last simulated data run to pick likely whales, "
        "then gives 3 upsell reply ideas per fan."
    )

    events_df = st.session_state.last_events_df
    last_results = st.session_state.last_results

    if events_df is None or last_results is None:
        st.warning(
            "No price test run found. Go to **Smart Price Test** first, "
            "run the engine, then return here."
        )
    else:
        creator_name = last_results["creator_name"]

        # Use top 5 whales as "unread fans" demo
        whales_df = get_today_whales(
            events_df=events_df,
            creator_name=creator_name,
            top_n=5,
        )

        st.markdown(
            "Below are some high-value fans. For each one, Sylently suggests "
            "**3 flirty reply ideas** you can copy into your DMs."
        )

        for _, row in whales_df.iterrows():
            fan_id = row["fan_id"]
            spend = row["predicted_spend_30d"]
            churned = bool(row["churned_any"])

            context = "generic_upsell"
            if churned:
                context = "renewal"

            suggestions = generate_dm_suggestions(
                fan_name=fan_id,
                creator_name=creator_name,
                context=context,
            )

            with st.expander(
                f"{fan_id} – high value fan (est. ${spend:.2f}/30d) "
                f"{'(at-risk)' if churned else ''}"
            ):
                for i, s in enumerate(suggestions, start=1):
                    st.markdown(f"**Option {i}:**")
                    st.code(s, language="text")
                    st.markdown("---")

        st.caption(
            "In a full production version, this panel would plug into the creator’s "
            "real DM inbox and only show **unread** or **at-risk** fans."
        )
