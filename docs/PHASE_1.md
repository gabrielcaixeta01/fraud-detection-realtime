# Phase 1 — Data generator + offline baseline

**Goal:** produce realistic synthetic transactions and prove, offline, that a model can
separate fraud from non-fraud.

Do this phase carefully — it is the foundation everything else stands on. If the generated
data is unrealistic, every later phase inherits the problem.

---

## Step 1 — Define the transaction schema

Decide the shape of a transaction event once, in `src/common/schema.py`, and reuse it
everywhere. A reasonable starting set of fields:

- `transaction_id`, `timestamp`
- `user_id`, `card_id`
- `amount`
- `merchant_id`, `merchant_category`
- `latitude`, `longitude` (transaction location)
- `is_fraud` (label — known because we generate it)

## Step 2 — Model normal behavior

For each synthetic user, fix a stable profile:
- a **home location** (lat/long), with most transactions near it;
- a **typical amount** distribution (e.g. log-normal — most purchases small, a few large);
- **active hours** (few transactions at 4 a.m.);
- a set of **familiar merchants** they return to.

Normal transactions are sampled from this profile. Faker helps generate the static
attributes (names, addresses, card numbers); you write the behavioral sampling.

## Step 3 — Inject fraud patterns

Fraud should be a small fraction (start ~0.1–0.5%). Implement a few distinct, realistic
patterns so the model has something learnable and you can later shift them for the drift
demo:

- **Burst:** many transactions from one card in a very short window.
- **Impossible geo-velocity:** consecutive transactions too far apart for the time between
  them.
- **Amount anomaly:** a charge many standard deviations above the user's baseline.
- **Card testing:** several tiny charges, then a large one.

Tag every fraudulent transaction with `is_fraud = 1`.

## Step 4 — Engineer velocity features (batch)

In pandas first — it is far easier to debug than streaming. For each transaction, compute
features from that card's **prior** history only (never using future rows — this is where
look-ahead bias creeps in and you must avoid it):

- transactions in the last 1 min / 10 min / 1 hour for this card,
- distance from the previous transaction ÷ time since it,
- amount z-score vs. the card's running mean/std,
- whether the merchant is new for this card.

Write this logic so it can later be mirrored in the streaming engine.

## Step 5 — Train a baseline

- Split **temporally** (train on earlier data, test on later) — not a random split. A random
  split leaks future information and inflates your metrics.
- Train **LightGBM**. Do not reach for deep learning.
- Handle imbalance via class weights or `scale_pos_weight` (start there before fancier
  resampling).

## Step 6 — Evaluate honestly

- Report **PR-AUC**, **precision**, **recall**, and a confusion matrix — not accuracy.
- Inspect feature importance: the velocity features should rank high. If they do not,
  something in Step 4 is wrong.
- Sanity-check: look at the transactions the model flags and confirm they look suspicious.

---

## Deliverable

- A reusable generator (`src/generator/`) with batch + (stub) stream modes.
- A labelled dataset.
- A notebook (`notebooks/01_baseline.ipynb`) walking through features → training →
  evaluation, with the metrics above.

## Common pitfalls

- **Look-ahead bias** in features — only ever use a card's past, never its future.
- **Random train/test split** — must be temporal.
- **Optimizing accuracy** — meaningless at this imbalance.
- **Over-investing in the model** — a solid baseline is enough here. Save your energy for
  the streaming system in Phase 2.
