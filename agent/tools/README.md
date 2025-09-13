## Tools — quick reference
======================

This package provides small, focused helpers and client wrappers used by
operational agents and orchestrators. The goal is to centralize shared
utilities (DB clients, record formatting, deterministic data coordinators)
so agents can remain simple and focused on domain logic.

Files and purpose
-----------------
- `supabase_tools.py`
	- `SupabaseClient`: a thin wrapper around the Supabase Python client.
		- Main method: `query_table(table, filters=None, select='*')` which applies
			flexible filter shapes and returns a list of dict rows.
		- `format_records(records, limit=20)`: utility for human-readable summaries.
		- Exports `TOOL = SupabaseClient` for discovery by `agent.tools.registry`.

- `data_coordinator.py`
	- `DataCoordinator`: deterministic query helper used by `RAGAgent`.
		- Normalizes a small, whitelisted set of filters and returns an
			envelope-like dict (`metadata`, `records`) with lightweight provenance.
		- Provides a `tool(args)` wrapper compatible with LangChain tool shapes.

- `registry.py`
	- `discover_local_tools()`: runtime discovery helper that imports modules
		under `agent.tools` and returns a mapping name → tool class/factory when
		modules expose `TOOL` or `create_tool()`.

- `__init__.py`
	- Package entrypoint. Keep imports minimal to avoid side-effects at import
		time.

Usage patterns
--------------
- Discovery: load available tools programmatically:

	from agent.tools.registry import discover_local_tools
	tools = discover_local_tools()

- Prefer dependency injection: instantiate tool clients in wiring code and
	pass them into agents (constructor or factory). Avoid hard imports in agent
	modules to keep tests simple.

Security and secrets
--------------------
- Tools may require credentials (e.g., `SUPABASE_URL`, `SUPABASE_KEY`). Do
	not commit `.env` files or secrets to source control; use environment
	variables or secret stores in CI and production.

Provenance and raw data
-----------------------
- Tools and coordinators attach minimal provenance to records:
	`{source, row_id, row_hash, retrieved_at}`.
- Avoid including full raw rows by default; offer `include_raw=True` as an
	explicit opt-in for debugging or data-export flows. For large raw results,
	consider pushing to an object store and returning a pointer.

Testing
-------
- Unit test `DataCoordinator` by passing a fake `SupabaseClient` that returns
	controlled rows.
- Mock `SupabaseClient` responses for error cases to ensure robust envelope
	behavior.

