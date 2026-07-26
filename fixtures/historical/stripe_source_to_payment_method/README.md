# Historical Stripe validation fixture (M6)

Models Stripe's Charges API rename of the `source` parameter to `payment_method`
(the same surface our demo bump exercises). Specs are trimmed OpenAPI excerpts —
not full Stripe dumps — so diff + scan stay deterministic.

- `old.json` / `new.json` / `expected.json` — diff engine inputs
- `../consumer/billing.py` — synthetic consumer with two true call sites

Validation: `pytest tests/test_historical_stripe.py`
