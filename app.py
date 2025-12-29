import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Sylently",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------
# Session state initialization
# -----------------------------
def init_state():
    if "creator_profile" not in st.session_state:
        st.session_state["creator_profile"] = None  # dict with creator info

    if "profile_loaded" not in st.session_state:
        st.session_state["profile_loaded"] = False  # bool

    if "percentile_data" not in st.session_state:
        st.session_state["percentile_data"] = None  # dict with percentile metrics

    if "test_results" not in st.session_state:
        st.session_state["test_results"] = None  # whatever structure you like


init_state()


# -----------------------------
# Core business-logic stubs
# -----------------------------

def lookup_onlyfans_profile(profile_url_or_username: str) -> dict:
    """
    LOOKUP STEP (LIVE PAGE / PROFILE SCRAPE)

    Replace the contents of this function with your actual OnlyFans lookup logic:
    - Scrape the live page
    - Or call your internal API
    - Or whatever you already have working

    It should return a dict that the rest of the app can rely on.
    Feel free to add/remove fields to match your existing app.
    """

    # --- BEGIN: example stub (safe to replace with your real code) ---
    username = profile_url_or_username.strip()
    if "onlyfans.com" in username:
        username = username.rstrip("/").split("/")[-1]

    # Dummy data to show the structure; adapt as needed:
    fake_profile = {
        "username": username,
        "display_name": username.capitalize(),
        "profile_url": f"https://onlyfans.com/{username}",
        "avatar_url": None,
        "followers": 1234,
        "posts_count": 56,
        "avg_likes": 89,
        "avg_comments": 4,
        "bio": "This is an example bio. Replace with real scraped data.",
        "niche": "General",
        "source": "live_page",  # mark that this came from a live lookup
    }
    return fake_profile
    # --- END: example stub ---


def run_small_test_for_creator(profile: dict) -> dict:
    """
    SMALL TEST LOGIC

    This function should run your 'small test' to generate performance data,
    then return a structure with the key outputs your UI needs.

    Plug your existing test logic in here.
    """

    # --- BEGIN: example stub (safe to replace with your real code) ---
    username = profile.get("username", "unknown_creator")
    results = {
        "creator": username,
        "test_sample_size": 100,
        "test_notes": "Example test results. Replace with real test logic.",
        "raw_metrics": {
            "click_through_rate": 0.12,
            "conversion_rate": 0.03,
        },
    }
    return results
    # --- END: example stub ---


def compute_percentiles_from_test_results(test_results: dict) -> dict:
    """
    Given the 'small test' results, compute percentile metrics.
    Replace the body with your real scoring / percentile model.
    """

    # --- BEGIN: example stub (safe to replace with your real code) ---
    percentiles = {
        "views_percentile": 0.75,        # 75th percentile
        "earnings_percentile": 0.62,     # 62nd percentile
        "engagement_percentile": 0.80,   # 80th percentile
        "source": "small_test",
        "explanation": "Dummy percentile values for demonstration.",
    }
    return percentiles
    # --- END: example stub ---


def compute_percentiles_from_live_profile(profile: dict) -> dict:
    """
    FALLBACK: compute rough/approximate percentiles directly from live profile data
    when no small test data exists.

    This is where you map live stats (followers, engagement, etc.) to percentile scores.
    """

    # --- BEGIN: example stub (safe to replace with your real code) ---
    followers = profile.get("followers") or 0
    posts = profile.get("posts_count") or 0

    # Very rough / fake logic just to show structure:
    views_percentile = min(0.99, max(0.01, followers / 10000.0))
    earnings_percentile = min(0.99, max(0.01, (followers * 0.5 + posts * 2) / 20000.0))
    engagement_percentile = 0.5  # constant in this stub

    percentiles = {
        "views_percentile": round(views_percentile, 2),
        "earnings_percentile": round(earnings_percentile, 2),
        "engagement_percentile": round(engagement_percentile, 2),
        "source": "live_profile_fallback",
        "explanation": (
            "Approximate percentiles computed from live profile data only. "
            "Replace this with your real model."
        ),
    }
    return percentiles
    # --- END: example stub ---


# -----------------------------
# UI helper functions
# -----------------------------

def ensure_profile_loaded():
    """
    Guard function to be used at the top of any tab or section that
    depends on the creator profile.
    """
    if not st.session_state.get("profile_loaded") or not st.session_state.get("creator_profile"):
        st.warning("Please complete **Step 1 · Look up OnlyFans profile** above first.")
        st.stop()


def show_sidebar_profile_summary():
    """
    Shows the currently loaded creator profile in the sidebar.
    """
    prof = st.session_state.get("creator_profile")
    st.sidebar.markdown("### Current Creator")

    if not prof:
        st.sidebar.info("No creator selected yet. Use Step 1 to look up a profile.")
        return

    display_name = prof.get("display_name", prof.get("username", "Unknown"))
    username = prof.get("username", "n/a")
    st.sidebar.write(f"**{display_name}**")
    st.sidebar.write(f"@{username}")

    if prof.get("profile_url"):
        st.sidebar.write(prof["profile_url"])

    st.sidebar.write(f"Followers: {prof.get('followers', 'n/a')}")
    st.sidebar.write(f"Posts: {prof.get('posts_count', 'n/a')}")
    niche = prof.get("niche")
    if niche:
        st.sidebar.write(f"Niche: {niche}")


def show_profile_lookup_step():
    """
    STEP 1: OnlyFans profile lookup (this always comes first in the flow).
    """
    st.subheader("Step 1 · Look up OnlyFans profile (required)")

    col1, col2 = st.columns([3, 1])

    with col1:
        profile_input = st.text_input(
            "OnlyFans profile URL or username",
            value="",
            placeholder="e.g. https://onlyfans.com/creatorname or creatorname",
            key="profile_input",
        )

    with col2:
        st.write("")  # spacing
        st.write("")
        lookup_clicked = st.button("Look up profile", type="primary")

    if lookup_clicked:
        if not profile_input.strip():
            st.error("Please enter an OnlyFans URL or username.")
        else:
            with st.spinner("Looking up OnlyFans profile..."):
                profile = lookup_onlyfans_profile(profile_input)

            if not profile:
                st.error("Could not fetch profile data. Please check the URL/username.")
                st.session_state["creator_profile"] = None
                st.session_state["profile_loaded"] = False
            else:
                st.session_state["creator_profile"] = profile
                st.session_state["profile_loaded"] = True
                # Reset downstream data when a new profile is loaded
                st.session_state["percentile_data"] = None
                st.session_state["test_results"] = None

                username = profile.get("username", profile_input.strip())
                st.success(f"Profile loaded for @{username}")

    # If a profile is already loaded, show a small summary below the input
    if st.session_state["profile_loaded"] and st.session_state["creator_profile"]:
        prof = st.session_state["creator_profile"]
        st.info(
            f"Using profile: **{prof.get('display_name', prof.get('username', 'Unknown'))}** "
            f"(@{prof.get('username', 'n/a')})\n\n"
            f"URL: {prof.get('profile_url', 'n/a')}"
        )


# -----------------------------
# Tab content functions
# -----------------------------

def show_overview_tab():
    ensure_profile_loaded()
    prof = st.session_state["creator_profile"]

    st.subheader("Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Basic Info")
        st.write(f"**Display name:** {prof.get('display_name', 'n/a')}")
        st.write(f"**Username:** @{prof.get('username', 'n/a')}")
        st.write(f"**Profile URL:** {prof.get('profile_url', 'n/a')}")

        niche = prof.get("niche") or "n/a"
        st.write(f"**Niche:** {niche}")

        bio = prof.get("bio") or "_No bio available_"
        st.markdown("**Bio:**")
        st.write(bio)

    with col2:
        st.markdown("#### Stats (from live profile)")
        st.write(f"**Followers:** {prof.get('followers', 'n/a')}")
        st.write(f"**Posts:** {prof.get('posts_count', 'n/a')}")
        st.write(f"**Avg likes (example field):** {prof.get('avg_likes', 'n/a')}")
        st.write(f"**Avg comments (example field):** {prof.get('avg_comments', 'n/a')}")

    st.markdown("---")
    st.markdown(
        "_This overview is powered by the live OnlyFans profile data. "
        "Run a small test in the next tab for deeper percentile-based insights._"
    )


def show_tests_tab():
    ensure_profile_loaded()
    prof = st.session_state["creator_profile"]

    st.subheader("Tests / Performance")

    st.markdown(
        "Use a small test to generate more accurate performance metrics for this creator. "
        "If you skip the test, you can still approximate metrics from the live profile data."
    )

    run_test_clicked = st.button("Run small test for this creator")

    if run_test_clicked:
        with st.spinner("Running small test..."):
            results = run_small_test_for_creator(prof)
        st.session_state["test_results"] = results

        # After test, compute percentiles from test results
        percentiles = compute_percentiles_from_test_results(results)
        st.session_state["percentile_data"] = percentiles

        st.success("Small test completed and percentile data updated.")

    # Show test results if they exist
    if st.session_state["test_results"]:
        st.markdown("### Test Results")
        st.json(st.session_state["test_results"])
    else:
        st.info("No test has been run yet for this creator.")


def show_percentiles_tab():
    ensure_profile_loaded()
    prof = st.session_state["creator_profile"]
    st.subheader("Percentiles & Insights")

    percentile_data = st.session_state.get("percentile_data")

    if not percentile_data:
        # Original message
        st.warning("Run a small test first; we don't have percentile data.")

        # New button: use live profile data instead
        use_live = st.button("Use live OnlyFans profile data instead")

        if use_live:
            with st.spinner("Computing approximate metrics from live profile data..."):
                approx = compute_percentiles_from_live_profile(prof)
            st.session_state["percentile_data"] = approx
            percentile_data = approx
            st.success("Approximate metrics added from live profile data.")

    if percentile_data:
        source = percentile_data.get("source", "unknown")
        explanation = percentile_data.get("explanation")

        st.markdown(f"**Data source:** `{source}`")
        if explanation:
            st.markdown(f"**Note:** {explanation}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Views Percentile",
                value=f"{int((percentile_data.get('views_percentile', 0) or 0) * 100)}th",
            )
        with col2:
            st.metric(
                label="Earnings Percentile",
                value=f"{int((percentile_data.get('earnings_percentile', 0) or 0) * 100)}th",
            )
        with col3:
            st.metric(
                label="Engagement Percentile",
                value=f"{int((percentile_data.get('engagement_percentile', 0) or 0) * 100)}th",
            )

        st.markdown("#### Raw percentile data (debug / detail)")
        st.json(percentile_data)
    else:
        st.info(
            "Once you run a small test or use live profile data, "
            "this tab will show percentile-based insights."
        )


def show_pricing_tab():
    ensure_profile_loaded()
    prof = st.session_state["creator_profile"]
    percentile_data = st.session_state.get("percentile_data")

    st.subheader("Pricing & Offer Strategy")

    if not percentile_data:
        st.warning(
            "You don't have percentile data yet. "
            "Pricing suggestions will be very rough. "
            "Consider running a small test first (Tests tab) or using live profile data."
        )

    st.markdown("### Suggested positioning")

    followers = prof.get("followers") or 0
    base_tier = "mid-tier"
    if followers < 1000:
        base_tier = "small"
    elif followers > 10000:
        base_tier = "top-tier"

    st.write(
        f"This creator currently looks like a **{base_tier}** creator "
        f"based on live follower count ({followers})."
    )

    if percentile_data:
        earnings_pct = percentile_data.get("earnings_percentile", 0.5)
        if earnings_pct >= 0.8:
            st.write(
                "Their earnings indicators are in the **top 20%** of creators. "
                "You can likely justify higher pricing and more premium offers."
            )
        elif earnings_pct <= 0.3:
            st.write(
                "Their earnings indicators are in the **lower 30%**. "
                "You may want to start with conservative pricing and performance-based deals."
            )
        else:
            st.write(
                "Their earnings indicators are around the **middle of the pack**. "
                "Balanced, market-rate deals are likely appropriate."
            )

    st.markdown("---")
    st.markdown(
        "_Customize this tab with your actual pricing logic once your percentile "
        "data and test results are wired in._"
    )


# -----------------------------
# Main app
# -----------------------------

def main():
    st.title("Sylently")

    # Sidebar summary of current profile
    show_sidebar_profile_summary()

    # STEP 1: OnlyFans profile lookup (always first)
    show_profile_lookup_step()

    st.markdown("---")

    # Tabs that all depend on the selected creator
    tab_overview, tab_tests, tab_percentiles, tab_pricing = st.tabs(
        ["Overview", "Tests", "Percentiles", "Pricing"]
    )

    with tab_overview:
        show_overview_tab()

    with tab_tests:
        show_tests_tab()

    with tab_percentiles:
        show_percentiles_tab()

    with tab_pricing:
        show_pricing_tab()


if __name__ == "__main__":
    main()
