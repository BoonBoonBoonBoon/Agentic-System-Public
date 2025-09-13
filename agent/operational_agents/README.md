## Operational agents — folder index

This file documents what lives under `agent/operational_agents/` and gives a
brief description of each subfolder and notable files. Use this as a quick
reference when navigating agents and their responsibilities.

Layout
------
- `copywriter_agent/` (empty placeholder)
	- Intended for an agent that generates sales/copy content (LLM-backed).
	- Add an `AGENT_CLASS` or `create_agent()` and unit tests here.

- `db_write_agent/` (empty placeholder)
	- Intended for agents that perform idempotent writes to a database.
	- Should accept a DB client via constructor and implement `run(payload)`.

- `multi_channel_sequencer/` (empty placeholder)
	- Intended for agents that manage multi-channel deliveries or sequencing
		logic (e.g., schedule message across email/SMS/ads).

- `rag_agent/`
	- `rag_agent.py`: concrete RAG (retrieval-augmented generation) agent.
		- Exposes `AGENT_CLASS = RAGAgent` for registry discovery.
		- Key responsibilities:
			- Query lead records via `SupabaseClient` and `DataCoordinator`.
			- Provide tools for LangChain integration (`query_leads`,
				`data_coordinator`, `rag_agent`, `deliver_data`).
			- Offer `run(prompt, return_json=False)` which either returns a
				machine-readable envelope (when `return_json=True`) or a string
				response.
			- Parsing helpers: `parse_filters_from_text`, `parse_filters_with_llm`.
			- Delivery helper methods: `deliver_data_tool` and a disabled
				`deliver_data_disabled` placeholder.

- `registry.py`
	- Implements `discover_local_agents()` which imports each subpackage and
		looks for `AGENT_CLASS` or `create_agent()` to return a mapping of name →
		class/factory. This is the entrypoint for runtime discovery of agents.

- `__init__.py`
	- Exposes the package and indicates discovery utilities are available.

How to use
----------
- Discovery: call `from agent.operational_agents.registry import discover_local_agents`
	and use the returned dict to instantiate or call agents.
- Agent contract: prefer `AGENT_CLASS` that implements `run(payload)` and
	returns an envelope-like dict (`metadata`, `records`). Keep side-effects
	(writes, network calls) behind injected clients for testability.

Testing & extension
-------------------
- Unit tests: pass test doubles/mocks for external clients (Supabase, LLMs).
- Integration test: register a fake agent via the registry and run it through
	a Worker/Queue in-memory wiring to validate end-to-end behavior.

Contract
- Inputs: free-text prompts or small structured filters.
- Outputs: human-readable summaries by default; use `--json` for machine-readable envelopes when available.
- Errors: agents should validate inputs and warn or raise when required env vars (SUPABASE_*, OPENAI_API_KEY) are missing.

