"""Single source of truth for the transaction event shape.

Keep every component (generator, features, scoring, store) aligned to this schema.
Filled in during Phase 1 — see docs/PHASE_1.md.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Transaction:
    transaction_id: str
    timestamp: datetime
    user_id: str
    card_id: str
    amount: float
    merchant_id: str
    merchant_category: str
    latitude: float
    longitude: float
    is_fraud: int = 0  # label; known because we generate the data
