# Tech Stack — and why each choice

Every tool here was picked either because it is the industry-standard vocabulary for an ML
Engineer role in fintech, or because it keeps the project simple enough to actually finish.
Where there is a "start simple, upgrade later" path, it is noted.

---

## Language: Python 3.11+

The default language for ML engineering. Version 3.11+ for the performance improvements and
modern typing.

## ML: LightGBM (primary), scikit-learn, pandas

- **LightGBM** — gradient-boosted trees. In real-world tabular fraud/credit problems,
  gradient boosting beats deep learning far more often than newcomers expect. It trains
  fast, handles imbalance, and is genuinely what many fintechs run in production.
- **scikit-learn** — metrics, splitting, preprocessing, baselines.
- **pandas** — batch feature engineering in Phase 1.

Deep learning is deliberately **not** the starting point. Reaching for a neural net on
tabular fraud data signals inexperience, not sophistication.

## Synthetic data: Faker

Generates realistic names, addresses, and card numbers. You write the behavioral and fraud
logic on top. Generating your own data is a feature, not a shortcut — it forces you to
understand what actually makes a transaction suspicious.

## Streaming: Redis Streams → Kafka

- **Start with Redis Streams.** It gives you a real producer/consumer streaming model with
  a fraction of Kafka's operational overhead. You can run it from a single Docker container.
- **Upgrade to Kafka later** if you want the name on your CV and want to demonstrate
  partitioning/consumer groups. The code is structured so the stream layer is swappable.

Why streaming at all: it is the single biggest thing separating this project from the
thousands of static-CSV fraud notebooks. It is also where your systems background shows.

## Serving: FastAPI

Modern, async, fast Python web framework. The standard for exposing a model as a
low-latency HTTP endpoint. Async matters here because scoring is latency-sensitive.

## Packaging: Docker + docker-compose

Everything runs in containers, orchestrated with docker-compose (generator, Redis, scoring
service, dashboard). This is what "runs in production" looks like, and it makes the project
reproducible for anyone reviewing it.

## Monitoring: Streamlit (or Grafana)

- **Streamlit** — fastest way to build a live dashboard in pure Python. Good default.
- **Grafana** — more impressive and more "real production," but more setup. Optional upgrade
  if you want the polish.

The dashboard must show: throughput, p50/p99 latency, fraud rate over time, and the drift
signal.

## Experiment tracking: MLflow (optional)

Versions models and logs training runs. Optional, but adds a recognized MLOps name to the
project and shows you think about model lifecycle, not just training once.

## Testing: pytest

The Python testing standard. Even a handful of good tests (feature correctness, schema
validation, latency budget) signals engineering maturity that most portfolio projects lack.

---

## Summary: the "minimum viable" vs. "impressive" path

| Component     | Minimum viable      | Impressive upgrade   |
|---------------|---------------------|----------------------|
| Streaming     | Redis Streams       | Kafka                |
| Monitoring    | Streamlit           | Grafana + Prometheus |
| Tracking      | (skip)              | MLflow               |
| Model         | LightGBM            | LightGBM + tuning    |

Ship the minimum viable path end-to-end **first**. A complete simple system beats a
half-built impressive one.
