"""CLI entry point — wires profiles -> normal transactions -> fraud -> parquet.

This module is glue, not learning material: it is written out in full. It will raise
``NotImplementedError`` until the TODOs in `profile.py`, `normal.py` and `fraud.py`
are filled in, which is expected.

Usage:
    python -m src.generator.generate \\
        --n-users 1000 --n-transactions 500000 --fraud-rate 0.003 \\
        --seed 42 --output data/transactions.parquet
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from src.common.schema import Transaction
from src.generator.fraud import inject_fraud
from src.generator.normal import generate_normal_transactions
from src.generator.profile import generate_user_profiles


def transactions_to_frame(transactions: list[Transaction]) -> pd.DataFrame:
    """Flatten transactions into a DataFrame with a stable column order."""
    frame = pd.DataFrame([asdict(t) for t in transactions])
    if frame.empty:
        # Keep the schema even for an empty result, so downstream code can rely on it.
        return pd.DataFrame(columns=list(Transaction.__annotations__))
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame[list(Transaction.__annotations__)].sort_values("timestamp", ignore_index=True)


def build_dataset(
    n_users: int,
    n_transactions: int,
    fraud_rate: float,
    seed: int,
    days: int = 30,
) -> pd.DataFrame:
    """Run the full pipeline and return the labelled dataset."""
    profiles = generate_user_profiles(n_users=n_users, seed=seed)
    normal = generate_normal_transactions(
        profiles=profiles, n_transactions=n_transactions, seed=seed, days=days
    )
    labelled = inject_fraud(
        transactions=normal, profiles=profiles, fraud_rate=fraud_rate, seed=seed
    )
    return transactions_to_frame(labelled)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic, labelled transaction dataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--n-users", type=int, default=1_000, help="Number of synthetic users.")
    parser.add_argument(
        "--n-transactions",
        type=int,
        default=500_000,
        help="Number of NORMAL transactions; fraud is injected on top of these.",
    )
    parser.add_argument(
        "--fraud-rate",
        type=float,
        default=0.003,
        help="Target share of fraudulent rows in the output (0.003 = 0.3%%).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seeds every sampling step.")
    parser.add_argument("--days", type=int, default=30, help="Length of the time window, in days.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/transactions.parquet"),
        help="Destination parquet file. Parent directories are created.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    if not 0.0 <= args.fraud_rate < 1.0:
        raise SystemExit("--fraud-rate must be in [0, 1)")

    frame = build_dataset(
        n_users=args.n_users,
        n_transactions=args.n_transactions,
        fraud_rate=args.fraud_rate,
        seed=args.seed,
        days=args.days,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Requires a parquet engine (pyarrow). Swap to .to_csv if you'd rather not add one.
    frame.to_parquet(args.output, index=False)

    n_fraud = int(frame["is_fraud"].sum()) if not frame.empty else 0
    rate = n_fraud / len(frame) if len(frame) else 0.0
    print(f"wrote {len(frame):,} transactions -> {args.output}")
    print(f"fraud: {n_fraud:,} rows ({rate:.4%}), target {args.fraud_rate:.4%}")


if __name__ == "__main__":
    main()
