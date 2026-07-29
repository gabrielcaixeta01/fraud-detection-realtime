# Architecture

This document describes each component, the data flow between them, and the key design
decisions.

---

## Data flow

1. **Generator** emits a stream of transaction events. Most reflect normal user behavior; a
   small fraction are fraudulent, following injected patterns.
2. Events land on the **stream** (Redis Streams / Kafka).
3. The **scoring service** consumes each event, asks the **feature engine** for that
   transaction's live features, calls the **model**, and produces a decision (fraud
   probability + flag).
4. The transaction and its decision are written to the **store**.
5. The **monitoring dashboard** reads from the store to display latency, throughput, fraud
   rate, and drift signals.

Offline and in parallel, the **training pipeline** produces the model artifact the scoring
service loads, and a **backtest** evaluates it honestly before deployment.

---

## Components

### Generator (`src/generator/`)
Produces synthetic transactions. Two responsibilities:
- Model **normal** behavior per user: home geo-location, typical amount distribution, usual
  active hours, familiar merchants.
- Inject **fraud** patterns: transaction bursts, impossible geographic velocity (two cities
  minutes apart), amounts many standard deviations above the user's baseline, and
  card-testing (a series of tiny transactions before a large one).

Runs in two modes: **batch** (write a labelled dataset for Phase 1 training) and **stream**
(emit events continuously for Phase 2+).

### Feature engine (`src/features/`)
The technical heart of the project. Computes **velocity** features — features that only make
sense in the context of a card's recent history:
- count of transactions in the last minute / hour,
- geographic velocity (distance since last transaction ÷ time elapsed),
- current amount as a z-score against the user's rolling baseline,
- rate of first-time-merchant usage.

Two implementations that **must agree**:
- **Batch** (pandas) for training — easy to reason about.
- **Streaming** (stateful, sliding windows per card) for real-time scoring.

Keeping these two consistent is the subtle engineering challenge, and mirrors the real-world
"training/serving skew" problem.

### Scoring service (`src/scoring/`)
FastAPI service. Receives a transaction, requests live features, runs the model, returns a
decision. The whole path is latency-budgeted and measured (p50/p99).

### Training pipeline (`src/training/`)
Loads the batch dataset, builds features, trains LightGBM, evaluates with PR-AUC and
precision/recall, and writes the model artifact (optionally logged to MLflow).

### Monitoring (`src/monitoring/`)
Dashboard + drift detection. Compares the live distribution of features and predictions
against the training baseline; raises a drift signal when they diverge. Phase 3 deliberately
introduces drift to prove this works.

### Common (`src/common/`)
Shared transaction schema (a single source of truth for the event shape), config loading,
and utilities used across modules.

---

## Key design decisions

**Why synthetic data instead of a public dataset.** Generating the data forces genuine
domain understanding and enables true feature engineering, rather than working with
pre-anonymized black-box columns. It also lets us *control* the fraud pattern — essential for
the drift demonstration in Phase 3.

**Why velocity features are computed live.** Fraud is almost never visible in a single
isolated transaction; it shows up in the transaction relative to recent history. Computing
that history in real time (with state and sliding windows) is an engineering problem, not an
ML one — and it is where a systems background is an advantage.

**Why the stream layer is swappable.** Starting on Redis Streams keeps early phases simple;
isolating the stream behind a small interface means Kafka can replace it later without
touching the scoring or feature logic.

**Why PR-AUC over accuracy.** With ~0.1% fraud, a model that predicts "never fraud" scores
99.9% accuracy and is useless. Precision/recall and PR-AUC measure what actually matters:
catching fraud without drowning in false positives.
