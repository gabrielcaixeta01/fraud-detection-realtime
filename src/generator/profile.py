"""Stable per-user identity — the thing normal behavior is sampled *from*.

A profile is fixed once at generation time and never mutated afterwards. Everything
that makes a user recognisable (where they live, how much they usually spend, when
they are awake, who they buy from) lives here. Behavioral sampling lives in
`normal.py`; fraud lives in `fraud.py`. Keep those concerns out of this module.

See docs/PHASE_1.md, Step 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from faker import Faker


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
        # TODO(you): implement the log-normal mean formula.
        raise NotImplementedError

    @property
    def baseline_amount_std(self) -> float:
        """Std-dev of the user's amount distribution, in currency units.

        Closed form: ``sqrt((exp(sigma**2) - 1) * exp(2*mu + sigma**2))``.
        """
        # TODO(you): implement the log-normal std-dev formula.
        raise NotImplementedError


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
    # TODO(you): rng = np.random.default_rng(seed)

    # TODO(you): build the merchant universe ONCE, before the loop — every user's
    # familiar set should be a subset of the same global pool, otherwise "unfamiliar
    # merchant" is meaningless across users. Suggested: ~200 merchant ids paired with
    # a category drawn from a fixed list (grocery, fuel, restaurant, online, travel,
    # electronics, pharmacy). Keep the id -> category mapping around; normal.py needs
    # it to fill Transaction.merchant_category. Consider returning it, or moving it to
    # a module-level constant / small `Merchant` dataclass if you prefer.

    profiles: list[UserProfile] = []
    for _ in range(n_users):
        # TODO(you): sample one profile. Guidance per field:
        #
        #   user_id / card_id  -> stable unique strings, e.g. f"u_{i:05d}" / f"c_{i:05d}".
        #                         Prefer deterministic ids over uuid4 (uuid4 ignores the seed).
        #   name               -> fake.name()
        #   home lat/long      -> pick a plausible bounded region rather than the whole
        #                         globe, so "distance from home" has a sane scale.
        #                         e.g. lat ~ Uniform(-23.7, -23.4), long ~ Uniform(-46.8, -46.4)
        #                         for São Paulo. A single tight region also makes the
        #                         geo-velocity fraud pattern stand out clearly.
        #   geo_jitter_std     -> small, per-user, e.g. Uniform(0.005, 0.02) degrees.
        #   amount_mu          -> Normal(3.2, 0.4)-ish. Remember exp(3.2) ~= 25 currency
        #                         units, so this sets the user's typical spend.
        #   amount_sigma       -> Uniform(0.4, 0.9). Bigger sigma = heavier tail = more
        #                         naturally-large purchases = harder amount-anomaly task.
        #   active_hours       -> a contiguous-ish waking window, e.g. start ~ randint(6, 10)
        #                         and 12-16 consecutive hours mod 24. Do NOT give everyone
        #                         the same window; hour-of-day should still be learnable.
        #   familiar_merchants -> sample 5-15 ids WITHOUT replacement from the global pool.
        #
        # Then: profiles.append(UserProfile(...))
        pass

    return profiles  # placeholder: empty until the loop above is implemented
