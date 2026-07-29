"""Layer 2 — fraud injected on top of an existing normal stream.

Each pattern is its own parametrizable function. Keep them independent: in Phase 4
you will shift their parameters (or swap one pattern for another) to simulate concept
drift, and that is only cheap if no pattern reaches into another's internals.

Convention followed by every ``inject_*`` function:
  - it RETURNS a list of new fraudulent transactions, each already tagged
    ``is_fraud=1``; it does NOT mutate the input list;
  - it takes an ``anchor``: a real transaction from the victim's history that fixes
    *when* and *where* the attack starts. Anchoring on real history is what keeps the
    fraud plausible instead of uniformly random noise;
  - it takes a ``rng`` so the caller owns reproducibility (do not seed inside).

See docs/PHASE_1.md, Step 3.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.common.schema import Transaction
from src.generator.profile import UserProfile

if TYPE_CHECKING:  # numpy is a runtime dep; the import is here only for the annotation
    from numpy.random import Generator


def inject_burst(
    profile: UserProfile,
    anchor: Transaction,
    rng: "Generator",
    n_transactions: int = 8,
    window_seconds: int = 300,
    amount_scale: float = 1.0,
) -> list[Transaction]:
    """Many charges on one card inside a very short window.

    The signal is *rate*, not amount: a card that normally sees a few transactions a
    day suddenly emits ``n_transactions`` within ``window_seconds``. This is the
    pattern the 1-min / 10-min velocity counters of Phase 2 are built to catch, so
    keep the window tight enough that those counters actually fire.

    Args:
        profile: Victim, used for the amount distribution and home location.
        anchor: Real transaction that fixes the attack's start time and place.
        rng: Caller-owned numpy RNG.
        n_transactions: How many charges in the burst.
        window_seconds: Total span the burst is squeezed into.
        amount_scale: Multiplier on the user's typical amount. 1.0 keeps amounts
            ordinary so the model must learn rate rather than value.

    Returns:
        ``n_transactions`` fraudulent transactions, chronological, ``is_fraud=1``.
    """
    # TODO(you):
    #   - draw n_transactions offsets uniformly in [0, window_seconds), sort them,
    #     and add to anchor.timestamp
    #   - amounts: profile's log-normal * amount_scale
    #   - location: near the anchor, but NOT the user's home — an attacker is
    #     somewhere else. Reuse the anchor's lat/long with a modest offset.
    #   - merchants: draw from the global pool, not familiar_merchants
    raise NotImplementedError


def inject_geo_velocity(
    profile: UserProfile,
    anchor: Transaction,
    rng: "Generator",
    distance_km: float = 3000.0,
    minutes_after: int = 30,
) -> list[Transaction]:
    """One charge physically impossible to reach from the previous one.

    ``distance_km`` away, ``minutes_after`` minutes later — an implied speed no
    traveller achieves. The learnable feature is distance ÷ time-elapsed, computed
    against the card's *previous* transaction, so this pattern only works if the
    anchor really is the victim's latest transaction at that instant.

    Choose the defaults so implied speed clears any plausible flight: 3000 km in
    30 min is 6000 km/h. If you soften this later for a harder task, keep it above
    ~1000 km/h or it stops being unambiguously impossible.

    Args:
        profile: Victim.
        anchor: The transaction the impossible jump is measured *from*.
        rng: Caller-owned numpy RNG.
        distance_km: Great-circle distance from the anchor's location.
        minutes_after: Time gap after the anchor.

    Returns:
        A single fraudulent transaction, ``is_fraud=1``.
    """
    # TODO(you):
    #   - convert distance_km to a lat/long offset in a random bearing. Rough and
    #     good enough near the equator: 1 deg latitude ~= 111 km, and
    #     1 deg longitude ~= 111 * cos(latitude) km. Draw the bearing from
    #     rng.uniform(0, 2*pi) so the jump direction varies.
    #   - timestamp = anchor.timestamp + timedelta(minutes=minutes_after)
    #   - amount: ordinary for this user, so distance is the only giveaway
    #   - merchant: from the global pool
    raise NotImplementedError


def inject_amount_anomaly(
    profile: UserProfile,
    anchor: Transaction,
    rng: "Generator",
    n_std: float = 8.0,
) -> list[Transaction]:
    """A single charge far above the user's own baseline.

    "Far above" is *relative to this user* — 5000 is unremarkable for a heavy spender
    and absurd for a light one. Derive the amount from the profile's closed-form
    baseline (``profile.baseline_amount_mean`` / ``baseline_amount_std``), not from a
    fixed threshold, and not from a scan of future rows.

    Args:
        profile: Victim, source of the baseline.
        anchor: Fixes when and roughly where the charge happens.
        rng: Caller-owned numpy RNG.
        n_std: How many baseline std-devs above the mean. 8 is comfortably detectable;
            drop toward 3-4 if the baseline model gets too easy.

    Returns:
        A single fraudulent transaction, ``is_fraud=1``.
    """
    # TODO(you):
    #   - amount = profile.baseline_amount_mean + n_std * profile.baseline_amount_std,
    #     then add mild jitter so the value is not a constant per user
    #   - timestamp: shortly after the anchor (minutes to a few hours)
    #   - merchant: high-ticket categories are more plausible here (electronics,
    #     travel) — an unfamiliar merchant reinforces the signal
    raise NotImplementedError


def inject_card_testing(
    profile: UserProfile,
    anchor: Transaction,
    rng: "Generator",
    n_probes: int = 5,
    probe_amount_max: float = 2.0,
    probe_window_minutes: int = 20,
    payoff_multiplier: float = 30.0,
) -> list[Transaction]:
    """Several tiny probe charges, then one large payoff.

    The attacker is validating a stolen card with amounts small enough to slip past
    review, then cashing in once it clears. The learnable shape is the *sequence*:
    an abnormal run of sub-currency-unit charges followed by a spike. Emit the probes
    and the payoff as one group so the ordering survives.

    Args:
        profile: Victim.
        anchor: Fixes the start of the testing run.
        rng: Caller-owned numpy RNG.
        n_probes: Number of small probe charges.
        probe_amount_max: Upper bound for a probe amount. Keep this below anything the
            normal layer emits, otherwise the pattern is indistinguishable from noise.
        probe_window_minutes: Span the probes are spread across.
        payoff_multiplier: Payoff amount as a multiple of the user's baseline mean.

    Returns:
        ``n_probes + 1`` fraudulent transactions, chronological, ``is_fraud=1``.
    """
    # TODO(you):
    #   - probes: amounts ~ rng.uniform(0.01, probe_amount_max), timestamps spread
    #     over probe_window_minutes starting at the anchor
    #   - payoff: profile.baseline_amount_mean * payoff_multiplier, timestamped just
    #     after the last probe
    #   - keep all n_probes + 1 on the same card, from unfamiliar merchants; online
    #     categories are the realistic choice for probing
    raise NotImplementedError


def inject_fraud(
    transactions: list[Transaction],
    profiles: list[UserProfile],
    fraud_rate: float = 0.003,
    seed: int = 42,
) -> list[Transaction]:
    """Apply the patterns above to a normal stream until the target rate is reached.

    Orchestration only — no pattern logic belongs in this function.

    Args:
        transactions: Chronologically sorted normal stream. Not mutated.
        profiles: Population, indexed by ``user_id`` to find each victim's profile.
        fraud_rate: Target share of fraudulent rows in the OUTPUT, e.g. 0.003 = 0.3%.
            Note the denominator grows as you inject: to hit rate ``r`` on top of
            ``n`` normal rows you need roughly ``n * r / (1 - r)`` fraudulent rows.
        seed: Seeds the numpy RNG shared by every pattern call.

    Returns:
        A new chronologically sorted list containing the normal stream plus the
        injected fraud. Fraudulent rows carry ``is_fraud=1``.
    """
    # TODO(you): rng = np.random.default_rng(seed)

    # TODO(you): compute the fraud budget from fraud_rate (see the note in the
    #   docstring — do not just multiply by len(transactions), that undershoots).

    # TODO(you): index profiles by user_id, and index transactions by user_id so you
    #   can pick a victim and an anchor from that victim's own history.

    # TODO(you): loop until the budget is spent:
    #   1. pick a victim (uniformly, or bias toward active users)
    #   2. pick an anchor from that victim's transactions. Avoid the very last one for
    #      geo-velocity — the pattern needs the anchor to be the *previous* event, and
    #      the jump should still land inside the generated time window.
    #   3. choose a pattern. Keep the mix explicit and tunable, e.g.
    #        weights = {"burst": .3, "geo": .25, "amount": .25, "card_testing": .2}
    #      Store it as a module-level dict or a parameter so Phase 4 can shift it.
    #   4. call the pattern, extend a `frauds` list with the result.
    #   Note patterns return different counts (geo/amount return 1, burst and
    #   card_testing return many) — count actual rows against the budget, not calls.

    # TODO(you): give the injected rows unique transaction_ids that cannot collide
    #   with the normal layer's (e.g. prefix "f_"), then merge and re-sort:
    #     merged = transactions + frauds
    #     merged.sort(key=lambda t: t.timestamp)

    return list(transactions)  # placeholder: returns the stream unchanged, 0% fraud
