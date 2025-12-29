from typing import List


def generate_dm_suggestions(
    fan_name: str,
    creator_name: str,
    context: str = "generic_upsell",
) -> List[str]:
    """
    Returns 3 flirty upsell reply suggestions for a given fan.

    This is rule-based for now (no external AI calls) but structured so we can
    later swap in a real LLM.

    context can be:
    - "generic_upsell"
    - "renewal"
    - "ppv_drop"
    """
    fan = fan_name or "babe"

    if context == "renewal":
        return [
            f"{fan}, I saw your sub is close to renewing and I kinda love having you here 😈 "
            f"If you stay, I’ll send you a little extra just for my loyal ones… deal?",
            f"Should I keep you on my VIP list, {fan}? If you renew, I have a spicy thank-you ready for you 🔥",
            f"I’m planning something special for my day-ones… if you stick around this month, "
            f"I’ll make sure your DMs feel extra worth it 😉",
        ]

    if context == "ppv_drop":
        return [
            f"{fan}, I just shot something I’m lowkey nervous to send out 😏 "
            "If I dropped a little preview, would you want first look?",
            f"I’m putting together a special set and I keep thinking you’d appreciate it the most… "
            "want me to save you a spot when it goes live?",
            f"If I made a bundle that’s hotter than what I usually post on main, "
            f"would you rather see it early or get the full thing later? 👀",
        ]

    # default: generic upsell
    return [
        f"Hey {fan}, I love how you show up for me here 🖤 "
        "If I sent you something a bit more personal tonight, would you want it?",
        f"I’m feeling a little extra today… if I put together a private set just for my best supporters, "
        f"should I count you in, {fan}? 😉",
        f"Real talk, {fan}… if I made a special offer just for you, "
        "would you rather get more teasing pics or a longer video? 👀",
    ]
