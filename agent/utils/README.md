## Utils — quick reference
=========================

This package contains small helper modules used across agents and orchestrators.
It is intentionally minimal and optional (some functionality depends on `pydantic`).

Files and purpose
-----------------
- `envelope.py`
    - `Envelope` dataclass: produce and validate compact JSON envelopes exchanged
      between agents. Key methods: `from_records`, `to_dict`, `to_json`, `validate`.
    - `make_envelope`, `validate_envelope`: convenience functions used by callers
      that don't want to import the `Envelope` class.
    - Envelopes include minimal `provenance` per-record: `{source, row_id, row_hash, retrieved_at}`.
    - Optional: if `pydantic` is installed the module will use models from `schemas.py`.

- `schemas.py`
    - Optional `pydantic` models for stricter envelope validation when `pydantic`
      is available. Models: `ProvenanceModel`, `RecordModel`, `EnvelopeModel`.
    - The codebase treats these as optional; envelope validation falls back to
      lightweight structural checks when `pydantic` is not present.

Usage patterns
--------------
- For simple flows, use `make_envelope(source, records, task_id)` to return a
  Python dict and `to_json` when needed for wire formats.
- For stricter validation in tests or runtime, install `pydantic` and call
  `Envelope.validate()` or `validate_envelope(env)` to assert structure.

Testing
-------
- Unit test `Envelope.from_records` with both empty and non-empty record lists.
- Test `validate_envelope` with both valid and invalid structures and with
  `pydantic` available (install in CI test matrix to exercise both paths).
