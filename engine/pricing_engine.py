import numpy as np
import pandas as pd


def run_creator_sim_core(
    creator_name,
    creator_id,
    true_price_arms,
    seed=999,
    n_events=1000,
    max_rel_churn_increase=0.10,  # +10% churn guardrail
    tau=0.90                      # 90% posterior guardrail threshold
):
    """
    Run full bandit simulation + Bayesian update + creator report
    for a single creator.

    Returns a dict with:
    - summary_obs: observed averages by arm
    - summary_post: posterior means
    - prob_df: probability each arm is best / >=3% better than next
    - safe_df: churn guardrail status
    - report_table: combined summary for UI
    - best_price: recommended price
    - uplift_pct: uplift vs baseline (%)
    - prob_ge_3: P(recommended >=3% better than next-best) in %
    - baseline_price: baseline A price
    - creator_name, creator_id
    - events_df: raw simulated events (for whales / DM features)
    """
    np.random.seed(seed)

    # Priors for Bayesian updating
    alpha0, beta0 = 1.0, 1.0   # revenue prior (Gamma)
    a0, b0         = 1.0, 1.0   # churn prior (Beta)

    def init_posteriors():
        post = {}
        for arm in true_price_arms.keys():
            post[arm] = {
                "alpha": alpha0,
                "beta":  beta0,
                "a":     a0,
                "b":     b0,
                "N":     0
            }
        return post

    posteriors = init_posteriors()

    # Simulate subscriber outcome at a given arm
    def simulate_outcome(arm_key):
        arm = true_price_arms[arm_key]
        m = arm["true_mean_revenue"]
        churn_prob = arm["true_churn"]

        # Lognormal noise for revenue: sigma^2 = 0.21
        sigma2 = 0.21
        sigma = np.sqrt(sigma2)
        mu = np.log(m) - 0.5 * sigma2
        revenue = np.random.lognormal(mean=mu, sigma=sigma)

        churn = int(np.random.rand() < churn_prob)
        return revenue, churn

    # Thompson sampling with churn guardrail
    def choose_price_arm(
        posteriors,
        baseline_arm="A",
        max_rel_churn_increase=max_rel_churn_increase,
        tau=tau,
        n_churn_samples=2000
    ):
        base = posteriors[baseline_arm]
        if (base["a"] + base["b"]) > 2:
            baseline_churn_est = base["a"] / (base["a"] + base["b"])
        else:
            baseline_churn_est = true_price_arms[baseline_arm]["true_churn"]

        churn_cap = baseline_churn_est * (1.0 + max_rel_churn_increase)

        safe_arms = []
        for arm, params in posteriors.items():
            a, b = params["a"], params["b"]
            # Early stage: not enough data, allow exploration
            if a + b <= 2:
                safe_arms.append(arm)
                continue
            theta_samples = np.random.beta(a, b, size=n_churn_samples)
            prob_bad = np.mean(theta_samples > churn_cap)
            if prob_bad < tau:
                safe_arms.append(arm)

        if not safe_arms:
            safe_arms = list(posteriors.keys())

        # Thompson sample on revenue among safe arms
        sampled_revenue = {}
        for arm in safe_arms:
            alpha, beta = posteriors[arm]["alpha"], posteriors[arm]["beta"]
            sampled_revenue[arm] = np.random.gamma(shape=alpha, scale=1.0 / beta)

        best_arm = max(sampled_revenue, key=sampled_revenue.get)
        return best_arm

    # 1) Run the bandit experiment
    events = []
    arm_list = list(true_price_arms.keys())

    for i in range(1, n_events + 1):
        if i <= len(arm_list) * 10:
            # Forced exploration first (10 rounds per arm)
            arm_key = arm_list[(i - 1) % len(arm_list)]
        else:
            arm_key = choose_price_arm(posteriors)

        revenue, churn = simulate_outcome(arm_key)

        posteriors[arm_key]["alpha"] += revenue
        posteriors[arm_key]["beta"]  += 1.0
        posteriors[arm_key]["a"]     += churn
        posteriors[arm_key]["b"]     += (1 - churn)
        posteriors[arm_key]["N"]     += 1

        events.append({
            "event_id": i,
            "creator_id": creator_id,
            "subscriber_id": f"S{i:04d}",
            "day_of_experiment": np.random.randint(1, 31),
            "price_arm": arm_key,
            "price_usd": true_price_arms[arm_key]["price"],
            "net_revenue_30d": float(revenue),
            "churn_30d": int(churn),
        })

    events_df = pd.DataFrame(events)

    # 2) Observed results
    summary_obs = events_df.groupby(["price_arm", "price_usd"]).agg(
        n_events=("event_id", "count"),
        avg_revenue_30d=("net_revenue_30d", "mean"),
        churn_rate_30d=("churn_30d", "mean")
    ).reset_index().sort_values("price_usd")

    # 3) Posterior beliefs
    rows = []
    for arm, params in posteriors.items():
        alpha, beta = params["alpha"], params["beta"]
        a, b = params["a"], params["b"]
        mean_rev = alpha / beta
        mean_churn = a / (a + b)
        rows.append({
            "price_arm": arm,
            "price_usd": true_price_arms[arm]["price"],
            "posterior_mean_revenue": mean_rev,
            "posterior_mean_churn": mean_churn,
            "n_events": params["N"],
        })

    summary_post = pd.DataFrame(rows).sort_values("price_usd")

    # 4) Monte Carlo: probability each arm is best / ≥3% better than next-best
    n_samples = 10000
    arm_keys = list(true_price_arms.keys())
    samples = {arm: None for arm in arm_keys}

    for arm, params in posteriors.items():
        alpha, beta = params["alpha"], params["beta"]
        samples[arm] = np.random.gamma(shape=alpha, scale=1.0 / beta, size=n_samples)

    samples_mat = np.vstack([samples[arm] for arm in arm_keys])
    best_idx = np.argmax(samples_mat, axis=0)
    best_counts = np.bincount(best_idx, minlength=len(arm_keys))
    prob_best = {arm_keys[i]: best_counts[i] / n_samples for i in range(len(arm_keys))}

    uplift_ge_3 = {arm: 0.0 for arm in arm_keys}
    for j in range(n_samples):
        col = samples_mat[:, j]
        order = np.argsort(col)
        if len(order) < 2:
            continue
        best = order[-1]
        second = order[-2]
        if col[second] == 0:
            continue
        rel_uplift = (col[best] - col[second]) / col[second]
        if rel_uplift >= 0.03:
            uplift_ge_3[arm_keys[best]] += 1
    uplift_ge_3 = {arm: cnt / n_samples for arm, cnt in uplift_ge_3.items()}

    prob_rows = []
    for arm in arm_keys:
        prob_rows.append({
            "price_arm": arm,
            "price_usd": true_price_arms[arm]["price"],
            "prob_arm_is_best": prob_best[arm],
            "prob_arm_is_≥3%_better_than_next": uplift_ge_3[arm],
        })
    prob_df = pd.DataFrame(prob_rows).sort_values("price_usd")

    # 5) Churn guardrail + recommendation
    baseline_arm = "A"
    base_params = posteriors[baseline_arm]
    baseline_churn_est = base_params["a"] / (base_params["a"] + base_params["b"])
    churn_cap = baseline_churn_est * (1.0 + max_rel_churn_increase)

    safe_rows = []
    for arm, params in posteriors.items():
        a, b = params["a"], params["b"]
        theta_samples = np.random.beta(a, b, size=5000)
        prob_bad = np.mean(theta_samples > churn_cap)
        is_safe = prob_bad < tau
        safe_rows.append({
            "price_arm": arm,
            "price_usd": true_price_arms[arm]["price"],
            "posterior_mean_churn": a / (a + b),
            "prob_churn_violates_guardrail": prob_bad,
            "is_safe": is_safe,
        })
    safe_df = pd.DataFrame(safe_rows).sort_values("price_usd")

    safe_candidates = summary_post.merge(
        safe_df[["price_arm", "is_safe"]],
        on="price_arm",
        how="left"
    )
    safe_candidates = safe_candidates[safe_candidates["is_safe"] == True]

    if not safe_candidates.empty:
        best_row = safe_candidates.sort_values("posterior_mean_revenue", ascending=False).iloc[0]
    else:
        best_row = summary_post[summary_post["price_arm"] == baseline_arm].iloc[0]

    best_arm = best_row["price_arm"]
    best_price = best_row["price_usd"]
    best_rev = best_row["posterior_mean_revenue"]

    base_row = summary_post[summary_post["price_arm"] == baseline_arm].iloc[0]
    base_rev = base_row["posterior_mean_revenue"]
    uplift_pct = (best_rev - base_rev) / base_rev * 100.0

    row_prob = prob_df[prob_df["price_arm"] == best_arm].iloc[0]
    prob_ge_3 = row_prob["prob_arm_is_≥3%_better_than_next"] * 100.0

    # 6) Build report table
    report_table = summary_post.copy()
    report_table = report_table.merge(
        prob_df[["price_arm", "prob_arm_is_best", "prob_arm_is_≥3%_better_than_next"]],
        on="price_arm",
        how="left"
    )
    report_table = report_table.merge(
        safe_df[["price_arm", "is_safe"]],
        on="price_arm",
        how="left"
    )
    base_rev_val = float(base_rev)
    report_table["uplift_vs_baseline_%"] = (
        (report_table["posterior_mean_revenue"] - base_rev_val) / base_rev_val * 100.0
    )

    # Round for display
    report_table_display = report_table.copy()
    for col in [
        "posterior_mean_revenue",
        "posterior_mean_churn",
        "prob_arm_is_best",
        "prob_arm_is_≥3%_better_than_next",
        "uplift_vs_baseline_%"
    ]:
        report_table_display[col] = report_table_display[col].astype(float).round(4)

    return {
        "summary_obs": summary_obs,
        "summary_post": summary_post,
        "prob_df": prob_df,
        "safe_df": safe_df,
        "report_table": report_table_display,
        "best_price": float(best_price),
        "uplift_pct": float(uplift_pct),
        "prob_ge_3": float(prob_ge_3),
        "baseline_price": float(true_price_arms[baseline_arm]["price"]),
        "creator_name": creator_name,
        "creator_id": creator_id,
        "events_df": events_df,  # raw data for whales / DM features
    }
