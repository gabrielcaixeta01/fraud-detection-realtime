"""Layer 1 — normal behavior only.

Every transaction produced here has ``is_fraud=0``. There is deliberately NO fraud
logic in this module: fraud is layered on top by `fraud.py`, so each layer can be
validated on its own (histogram the output of this file and it should look like
boring, plausible spending).

See docs/PHASE_1.md, Step 2.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from src.common.schema import Transaction
from src.generator.profile import UserProfile


def generate_normal_transactions(
    profiles: list[UserProfile],
    n_transactions: int,
    seed: int = 42,
    start: datetime | None = None,
    days: int = 30,
) -> list[Transaction]:
    """Sample ``n_transactions`` legitimate transactions from the given profiles.

    Each transaction is drawn from exactly one user's profile, so the output stays
    consistent with that user's identity: amounts follow their log-normal, locations
    cluster near their home, timestamps land in their active hours, and merchants
    come mostly from their familiar set.

    Ordering: the returned list MUST be sorted by ``timestamp`` ascending. Everything
    downstream (fraud injection, velocity features, the temporal split) assumes a
    chronological stream. Sort once at the end rather than trying to generate in order.

    Args:
        profiles: Users to sample from. Transactions are spread across all of them.
        n_transactions: Total number of transactions to produce.
        seed: Seeds the numpy RNG. Use a different seed than the profiles if you want
            independent behavior for the same population.
        start: Timestamp of the beginning of the window. Defaults to
            ``days`` before now, truncated to midnight for tidiness.
        days: Length of the generated time window, in days.

    Returns:
        Chronologically sorted transactions, all with ``is_fraud=0``.
    """
    # TODO(you): rng = np.random.default_rng(seed)
    if start is None:
        start = (datetime.now() - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    end = start + timedelta(days=days)  # noqa: F841  (used once the body is filled in)

    transactions: list[Transaction] = []
    for i in range(n_transactions):
        # TODO(you): pick the acting user.
        #   Uniform choice over profiles is fine to start. More realistic: assign each
        #   user a weight (e.g. Dirichlet or log-normal) so some users are far more
        #   active than others — real traffic is heavily skewed, and it makes per-card
        #   velocity features in Phase 2 more interesting.
        # profile = profiles[rng.integers(len(profiles))]

        # TODO(you): amount.
        #   Sample from the user's OWN log-normal: rng.lognormal(profile.amount_mu,
        #   profile.amount_sigma). Round to 2 decimals. Optionally floor at ~1.0 so you
        #   never emit a 0.03 charge — tiny amounts are the card-testing fraud signal
        #   and should not appear in the normal layer.

        # TODO(you): timestamp.
        #   Two-step, so hour-of-day stays learnable:
        #     1. pick a day uniformly in [start, end)
        #     2. pick an hour from profile.active_hours (uniform, or weight the middle
        #        of the window higher), then a uniform minute/second within that hour.
        #   Leave a small escape hatch (~2-5% of the time) for an off-hours transaction,
        #   otherwise active_hours becomes a perfect rule and the model just memorises it.

        # TODO(you): location.
        #   home + gaussian jitter:
        #     lat  = profile.home_latitude  + rng.normal(0, profile.geo_jitter_std)
        #     long = profile.home_longitude + rng.normal(0, profile.geo_jitter_std)
        #   Then ~5% "travel" transactions with a much larger jitter (e.g. 20x std) so
        #   distance-from-home is not a trivially clean separator. Keep travel geographic
        #   displacement plausible *for the time elapsed* — that is what makes the
        #   geo-velocity fraud pattern (fraud.py) a genuinely distinct signal.

        # TODO(you): merchant.
        #   ~90% from profile.familiar_merchants, ~10% from the global merchant pool
        #   (a genuinely new merchant). merchant_category must be looked up from the
        #   id -> category mapping built in profile.generate_user_profiles — decide how
        #   to thread it through (return it alongside the profiles, store it on the
        #   profile, or promote it to a module-level constant) and keep it consistent:
        #   the same merchant_id must ALWAYS map to the same category.

        # TODO(you): transaction_id -> deterministic, e.g. f"t_{i:08d}". Avoid uuid4 so
        #   the same seed reproduces the same ids.

        # transactions.append(Transaction(..., is_fraud=0))
        pass

    # TODO(you): transactions.sort(key=lambda t: t.timestamp)
    return transactions  # placeholder: empty until the loop above is implemented
