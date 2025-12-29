import pandas as pd


def get_today_whales(
    events_df: pd.DataFrame,
    creator_name: str,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Simple "Today’s AI Whale Picks".

    - Groups by subscriber_id.
    - Uses 30-day revenue as spend proxy.
    - Adds a crude whale_score and 1 ice-breaker DM per fan.

    Returns a DataFrame with:
    fan_id, predicted_spend_30d, last_price, churned_any, whale_score, ice_breaker
    """
    required_cols = {"subscriber_id", "net_revenue_30d", "churn_30d", "price_usd"}
    if not required_cols.issubset(events_df.columns):
        missing = required_cols - set(events_df.columns)
        raise ValueError(f"events_df missing required columns: {missing}")

    agg = (
        events_df
        .groupby("subscriber_id")
        .agg(
            predicted_spend_30d=("net_revenue_30d", "sum"),
            last_price=("price_usd", "last"),
            churned_any=("churn_30d", "max"),
        )
        .reset_index()
    )

    # Crude whale_score: revenue, boosted if they haven't churned
    agg["whale_score"] = agg["predicted_spend_30d"] * (1.5 - 0.5 * agg["churned_any"])

    whales = (
        agg.sort_values("whale_score", ascending=False)
        .head(top_n)
        .copy()
    )

    ice_breakers = []
    for _, row in whales.iterrows():
        fan_id = row["subscriber_id"]
        spend = row["predicted_spend_30d"]
        price = row["last_price"]
        churned = bool(row["churned_any"])

        if churned:
            msg = (
                f"Hey {fan_id}, I miss seeing you in my VIP list 😏 "
                f"I made a special offer around ${price:.2f} just for you. "
                "Should I send it over?"
            )
        else:
            msg = (
                f"Hey {fan_id}, I noticed you've been spoiling me lately 👀 "
                f"If I dropped something a bit more exclusive around ${price:.2f}, "
                "would you want first dibs?"
            )

        ice_breakers.append(msg)

    whales["ice_breaker"] = ice_breakers
    whales = whales.rename(columns={"subscriber_id": "fan_id"})

    return whales[
        ["fan_id", "predicted_spend_30d", "last_price", "churned_any", "whale_score", "ice_breaker"]
    ]
