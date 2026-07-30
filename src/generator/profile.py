"""Stable per-user identity — the thing normal behavior is sampled *from*.

A profile is fixed once at generation time and never mutated afterwards. Everything
that makes a user recognisable (where they live, how much they usually spend, when
they are awake, who they buy from) lives here. Behavioral sampling lives in
`normal.py`; fraud lives in `fraud.py`. Keep those concerns out of this module.

See docs/PHASE_1.md, Step 2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from faker import Faker

# --- Merchant universe -------------------------------------------------------
# Built once at import time, with its own RNG, so the id -> category mapping is
# identical no matter which seed the profiles use. normal.py and fraud.py import
# these directly: the same merchant_id must ALWAYS map to the same category.
MERCHANT_CATEGORIES_POOL = [
    "grocery",
    "fuel",
    "restaurant",
    "online",
    "travel",
    "electronics",
    "pharmacy",
]
N_MERCHANTS = 200

_merchant_rng = np.random.default_rng(0)
ALL_MERCHANT_IDS: list[str] = [f"m_{j:05d}" for j in range(N_MERCHANTS)]
MERCHANT_CATEGORIES: dict[str, str] = {
    merchant_id: str(_merchant_rng.choice(MERCHANT_CATEGORIES_POOL))
    for merchant_id in ALL_MERCHANT_IDS
}


@dataclass
class UserProfile:
    """A synthetic user's stable identity.

    Attributes:
        user_id: Stable identifier, reused as the ``user_id`` of every transaction.
        card_id: The user's card. One card per user keeps Phase 1 simple; velocity
            features in Phase 2 are computed per *card*, so this matters later.
        name: Cosmetic, from Faker. Useful when eyeballing generated rows.
        home_latitude: Anchor point for the user's normal geography.
        home_longitude: Anchor point for the user's normal geography.
        geo_jitter_std: Std-dev (in decimal degrees) of the gaussian noise applied
            around home for a normal transaction. ~0.01 deg is roughly 1 km.
        amount_mu: ``mu`` of the user's log-normal amount distribution. This is the
            mean of ``log(amount)``, NOT the mean amount.
        amount_sigma: ``sigma`` of the log-normal, i.e. std-dev of ``log(amount)``.
        active_hours: Hours-of-day (0-23) during which this user typically transacts.
        familiar_merchants: Merchant IDs the user returns to. Normal transactions
            draw mostly from this set; an unfamiliar merchant is a weak fraud signal.
    """

    user_id: str
    card_id: str
    name: str
    home_latitude: float
    home_longitude: float
    geo_jitter_std: float
    amount_mu: float
    amount_sigma: float
    active_hours: list[int] = field(default_factory=list)
    familiar_merchants: list[str] = field(default_factory=list)

    @property
    def baseline_amount_mean(self) -> float:
        """Mean of the user's amount distribution, in currency units.

        Closed form for a log-normal: ``exp(mu + sigma**2 / 2)``. Handy for
        `fraud.inject_amount_anomaly`, which needs a baseline to deviate from
        without having to scan the user's generated history.
        """
        return math.exp(self.amount_mu + self.amount_sigma**2 / 2)

    @property
    def baseline_amount_std(self) -> float:
        """Std-dev of the user's amount distribution, in currency units.

        Closed form: ``sqrt((exp(sigma**2) - 1) * exp(2*mu + sigma**2))``.
        """
        variance = (math.exp(self.amount_sigma**2) - 1) * math.exp(
            2 * self.amount_mu + self.amount_sigma**2
        )
        return math.sqrt(variance)


def generate_user_profiles(n_users: int, seed: int = 42) -> list[UserProfile]:
    """Create ``n_users`` stable, reproducible user profiles.

    Reproducibility contract: the same ``(n_users, seed)`` must always yield
    byte-identical profiles. That means seeding *both* Faker and numpy here, and
    never touching the global `random` module without seeding it too.

    Args:
        n_users: How many profiles to create.
        seed: Seeds Faker and the numpy RNG.

    Returns:
        A list of ``n_users`` profiles with unique ``user_id`` / ``card_id``.
    """
    fake = Faker()
    Faker.seed(seed)
    rng = np.random.default_rng(seed)

    profiles: list[UserProfile] = []
    for i in range(n_users):
        # Waking window: a contiguous run of 12-16 hours starting somewhere in the
        # morning. `% 24` wraps the tail past midnight — a 9h start with a 16h window
        # legitimately runs to 01:00. Varying the window per user keeps hour-of-day a
        # learnable signal instead of a global rule.
        window_start = int(rng.integers(6, 10))
        window_length = int(rng.integers(12, 17))
        active_hours = [(window_start + h) % 24 for h in range(window_length)]

        # Without replacement: a repeated id would skew the "familiar merchant" draw
        # in normal.py.
        n_familiar = int(rng.integers(5, 16))
        familiar_merchants = [
            str(m) for m in rng.choice(ALL_MERCHANT_IDS, size=n_familiar, replace=False)
        ]

        profiles.append(
            UserProfile(
                user_id=f"u_{i:05d}",
                card_id=f"c_{i:05d}",
                name=fake.name(),
                # São Paulo-ish box: a tight region keeps "distance from home" on a
                # sane scale and makes the geo-velocity jump unmistakable.
                home_latitude=float(rng.uniform(-23.7, -23.4)),
                home_longitude=float(rng.uniform(-46.8, -46.4)),
                geo_jitter_std=float(rng.uniform(0.005, 0.02)),
                amount_mu=float(rng.normal(3.2, 0.4)),
                amount_sigma=float(rng.uniform(0.4, 0.9)),
                active_hours=active_hours,
                familiar_merchants=familiar_merchants,
            )
        )

    return profiles
