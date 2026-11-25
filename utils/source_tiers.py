"""Source tier classification for RAG evidence reliability."""

from __future__ import annotations

SOURCE_TIERS = {
    "Housing & Development Board (HDB)": 1,
    "Singapore Civil Defence Force (SCDF)": 1,
    "Building and Construction Authority (BCA)": 1,
    "Qanvast": 2,
}

TIER_LABELS = {
    1: "Tier 1 – Official",
    2: "Tier 2 – Third-party",
}

OFFICIAL_DOMAINS = ["hdb.gov.sg", "scdf.gov.sg", "bca.gov.sg"]


def get_tier(organisation: str) -> int:
    return SOURCE_TIERS.get(organisation, 2)


def get_tier_label(organisation: str) -> str:
    return TIER_LABELS[get_tier(organisation)]


def is_verified_official(hostname: str, organisation: str) -> tuple[bool, str]:
    """Check whether a source can be classified as an Official Source (Tier 1)."""
    hostname = hostname.lower()
    is_gov = any(hostname.endswith(d) for d in OFFICIAL_DOMAINS)
    expected_tier = SOURCE_TIERS.get(organisation, 2)

    if is_gov and expected_tier == 1:
        return True, ""

    if not is_gov:
        return False, (
            f"The domain ‘{hostname}’ is not in the approved list of official "
            f"government domains ({', '.join(OFFICIAL_DOMAINS)}). Only verified government "
            f"authority websites can be classified as Official Sources."
        )

    return False, (
        f"The organisation ‘{organisation}’ is not recognised as an official "
        f"government authority. Only HDB, SCDF, and BCA sources can be classified as "
        f"Official Sources."
    )
