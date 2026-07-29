# Real-Time Fraud Detection System

A streaming fraud detection system that scores financial transactions in real time.
The focus of this project is **production engineering around ML**, not just a model in a
notebook: transactions arrive as a stream, features are computed on the fly, each
transaction is scored in milliseconds, and the system monitors itself for latency and
model drift.

> **Why this project exists.** Real fraud detection does not run on a static CSV. It runs
> on streaming infrastructure over millions of events per day, where a decision has to be
> made before the transaction is approved. This repo is built to reflect that reality — the
> hard parts are the system around the model, not the model itself.

---

## What this demonstrates

- **Real-time feature engineering** — velocity features (transactions per minute,
  geographic velocity, amount vs. user baseline) computed with live state, not precomputed
  columns.
- **Streaming architecture** — a producer/consumer pipeline that scores transactions as
  they arrive.
- **Low-latency serving** — the scoring path is measured end-to-end (p50/p99 latency).
- **Drift monitoring** — the system detects when the fraud pattern shifts and the model
  starts to degrade.
- **Honest evaluation** — metrics chosen for extreme class imbalance (PR-AUC,
  precision/recall), never raw accuracy.

## Architecture

```
                          ┌─────────────────┐
                          │  Transaction    │
                          │  Generator      │   simulates normal behavior
                          │  (synthetic)    │   + injected fraud patterns
                          └────────┬────────┘
                                   │ events
                                   ▼
                          ┌─────────────────┐
                          │  Stream          │   Redis Streams (→ Kafka)
                          │  (event queue)   │
                          └────────┬────────┘
                                   │
                                   ▼
        ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
        │  Feature      │  │  Scoring         │  │  Model        │
        │  Engine       │◄─┤  Service         ├─►│  (LightGBM)   │
        │ (live state)  │  │  (FastAPI)       │  │               │
        └──────────────┘  └────────┬────────┘  └──────────────┘
                                   │ decision
                                   ▼
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
             ┌──────────────┐          ┌──────────────────┐
             │  Store        │          │  Monitoring       │
             │ (transactions │          │  Dashboard        │
             │  + decisions) │          │ (latency, drift)  │
             └──────────────┘          └──────────────────┘

   Offline (parallel):  Training pipeline  ──►  Backtest / evaluation
```

## Project status

This project is built in four phases. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the full
plan.

- [ ] **Phase 1** — Data generator + offline baseline model
- [ ] **Phase 2** — Streaming pipeline (real-time scoring)
- [ ] **Phase 3** — Production packaging + drift monitoring
- [ ] **Phase 4** — Polish, tests, and documentation

## Tech stack

| Layer              | Technology                                  |
|--------------------|---------------------------------------------|
| Language           | Python 3.11+                                |
| Data / ML          | pandas, LightGBM, scikit-learn              |
| Synthetic data     | Faker                                       |
| Streaming          | Redis Streams → Kafka                       |
| Serving            | FastAPI                                     |
| Packaging          | Docker, docker-compose                      |
| Monitoring         | Streamlit (or Grafana)                      |
| Experiment tracking| MLflow                                      |
| Testing            | pytest                                      |

See [`docs/TECH_STACK.md`](docs/TECH_STACK.md) for why each was chosen.

## Repository layout

```
fraud-detection-realtime/
├── docs/               Project documentation (roadmap, tech stack, architecture)
├── src/
│   ├── generator/      Synthetic transaction generator
│   ├── features/       Feature engineering (batch + streaming)
│   ├── scoring/        Real-time scoring service
│   ├── training/       Model training pipeline
│   ├── monitoring/     Drift detection + dashboard
│   └── common/         Shared schemas and utilities
├── tests/              pytest test suite
├── notebooks/          Exploratory analysis and baseline
├── config/             Configuration files
└── scripts/            Helper scripts (run, seed, benchmark)
```

## Getting started

```bash
# clone and set up
git clone https://github.com/gabrielcaixeta01/fraud-detection-realtime.git
cd fraud-detection-realtime
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Phase 1: generate data and train a baseline
python -m src.generator.generate --n-users 1000 --n-transactions 500000
python -m src.training.train
```

Full setup instructions arrive with each phase.

## License

MIT — see [`LICENSE`](LICENSE).
