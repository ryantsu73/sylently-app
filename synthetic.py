from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any
import random


@dataclass
class SyntheticPoint:
    impressions: int
    clicks: int
    subs: int
    revenue: float


def _smooth_random(base: float, variation: float) -> float:
    """
    Adds a small, bounded random variation around a base value.
    variation is a fraction (e.g. 0.3 means ±30%).
    """
    return max(0.0, base * (1 + random.uniform(-variation, variation)))


def generate_synthetic_data_from_profile(
    profile: Dict[str, Any],
    days: int = 7,
) -> Dict[str, Any]:
    """
    Generate synthetic, realistic metrics from basic OnlyFans profile stats.

    Expected profile keys (you can adapt names to your real fields):
      - followers: int
      - posts_count: int
      - price: float (monthly subscription price, if you have it)
      - avg_likes: float (optional)
      - avg_comments: float (optional)

    Returns a dict of shape:
      {
        "daily": [ {impressions, clicks, subs, revenue}, ... ],
        "summary": {...},
        "source": "synthetic_from_profile"
      }
    """

    followers = profile.get("followers") or 0
    posts_count = profile.get("posts_count") or 0
    price = float(profile.get("price") or 9.99)  # default if unknown

    # Follower & posting scale
    followers = max(0, int(followers))
    posts_count = max(0, int(posts_count))

    # Assume a rough daily reach as a fraction of followers.
    # Smaller creators typically reach a higher % of their base.
    if followers <= 1_000:
        reach_ratio = 0.5   # 50% of followers
    elif followers <= 10_000:
        reach_ratio = 0.25  # 25%
    elif followers <= 100_000:
        reach_ratio = 0.12  # 12%
    else:
        reach_ratio = 0.05  # 5%

    # Baseline CTR and conversion, then we add noise per day
    base_ctr = 0.08          # 8% click-through rate
    base_conversion = 0.025  # 2.5% of clicks convert to subs

    # Slightly nudge based on posting frequency:
    # More posts → a bit more impressions, but slightly lower per-post CTR.
    posting_factor = 1.0
    if posts_count > 200:
        posting_factor = 1.2
        base_ctr *= 0.95
    elif posts_count < 20:
        posting_factor = 0.8
        base_ctr *= 1.05

    daily_points: List[SyntheticPoint] = []

    for _ in range(days):
        # Daily impressions
        base_impressions = int(followers * reach_ratio * posting_factor)
        impressions = int(_smooth_random(base_impressions, 0.3))

        # Clicks from impressions
        ctr = _smooth_random(base_ctr, 0.25)
        clicks = int(impressions * ctr)

        # Subs from clicks
        conv = _smooth_random(base_conversion, 0.3)
        subs = int(clicks * conv)

        # Revenue from subs
        revenue = subs * price

        daily_points.append(
            SyntheticPoint(
                impressions=impressions,
                clicks=clicks,
                subs=subs,
                revenue=revenue,
            )
        )

    # Aggregate summary
    total_impressions = sum(p.impressions for p in daily_points)
    total_clicks = sum(p.clicks for p in daily_points)
    total_subs = sum(p.subs for p in daily_points)
    total_revenue = sum(p.revenue for p in daily_points)

    avg_impressions = total_impressions / days if days else 0
    avg_clicks = total_clicks / days if days else 0
    avg_subs = total_subs / days if days else 0
    avg_revenue = total_revenue / days if days else 0

    summary = {
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
        "total_subs": total_subs,
        "total_revenue": round(total_revenue, 2),
        "avg_impressions": round(avg_impressions, 1),
        "avg_clicks": round(avg_clicks, 1),
        "avg_subs": round(avg_subs, 1),
        "avg_revenue": round(avg_revenue, 2),
        "cvr": round(total_subs / total_clicks, 4) if total_clicks else 0.0,
        "ctr": round(total_clicks / total_impressions, 4) if total_impressions else 0.0,
        "rpm": round(total_revenue * 1000 / total_impressions, 2) if total_impressions else 0.0,
    }

    return {
        "daily": [p.__dict__ for p in daily_points],
        "summary": summary,
        "source": "synthetic_from_profile",
    }


def _map_to_percentile(value: float, low: float, high: float) -> float:
    """
    Maps value from [low, high] → [0.05, 0.95].
    Below low → 0.05, above high → 0.95.
    """
    if value <= low:
        return 0.05
    if value >= high:
        return 0.95
    ratio = (value - low) / (high - low)
    return 0.05 + ratio * (0.95 - 0.05)


def compute_percentiles_from_synthetic(synth: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert synthetic summary metrics to percentile scores.
    Tune the [low, high] thresholds to your expectations.
    """

    summary = synth.get("summary", {})

    rpm = summary.get("rpm", 0.0)                      # revenue per 1000 impressions
    ctr = summary.get("ctr", 0.0)                      # click-through rate
    avg_impressions = summary.get("avg_impressions", 0)
    # If you want, you can also incorporate cvr:
    # cvr = summary.get("cvr", 0.0)

    views_percentile = _map_to_percentile(avg_impressions, 100.0, 50_000.0)
    earnings_percentile = _map_to_percentile(rpm, 1.0, 80.0)
    engagement_percentile = _map_to_percentile(ctr, 0.01, 0.15)

    return {
        "views_percentile": round(views_percentile, 2),
        "earnings_percentile": round(earnings_percentile, 2),
        "engagement_percentile": round(engagement_percentile, 2),
        "source": "synthetic_profile_model",
        "explanation": (
            "Percentiles estimated from synthetic metrics generated from the "
            "creator's OnlyFans profile stats. Real test data will override these."
        ),
    }
