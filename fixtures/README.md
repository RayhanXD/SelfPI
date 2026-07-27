# Fixtures

- `diff/<kind>/` — OpenAPI `old.json` / `new.json` / `expected.json` triples for the
  diff engine (M1). Kinds: `renamed_param`, `removed_field`, `type_changed`,
  `value_deprecated`.
- `scanner/python/` — golden CallSite IR records for the Python scanner (M2).
- `sample_repo/` — tiny Python app used by scanner + patcher outcome tests.
- `detector/` — sample trees for API auto-detect (with/without Stripe) + `expected.json`.
- `specs/` — optional full OpenAPI snapshots for demo bumps.
