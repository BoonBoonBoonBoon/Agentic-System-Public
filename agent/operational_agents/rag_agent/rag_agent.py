from typing import Any, Dict
import json
import re
import os
from datetime import datetime, timezone
import hashlib

# Try to import OpenAI/LangChain pieces lazily in methods to avoid import-time failures
try:
    from langchain.agents import initialize_agent, Tool
except Exception:
    initialize_agent = None


class RAGAgent:
    """Minimal, test-friendly RAG agent wrapper.

    Keeps initialization light-weight and avoids network calls during import/instantiation.
    """

    def __init__(self):
        self._llm = None
        self._agent = None
        self.supabase = None
        # lightweight coordinator stub so tests can replace .tool with a MagicMock
        class _CoordinatorStub:
            def tool(self, args):
                now = datetime.now(timezone.utc).isoformat()
                return {"metadata": {"source": "coord.stub", "retrieved_at": now, "total_count": 0}, "records": []}

        self.coordinator = _CoordinatorStub()

        # Tools: keep as simple dicts in case langchain.Tool isn't available
        self.tools = [
            {
                "name": "query_leads",
                "func": self.query_leads_tool,
                "description": "Query the leads table (test-friendly stub).",
            }
        ]

    def get_llm(self):
        if self._llm is None:
            try:
                from langchain_openai import OpenAI
            except Exception:
                try:
                    from langchain_community.llms import OpenAI as OpenAICommunity

                    OpenAI = OpenAICommunity
                except Exception:
                    try:
                        from langchain.llms import OpenAI
                    except Exception:
                        OpenAI = None

            if OpenAI is not None:
                self._llm = OpenAI(temperature=0)
        return self._llm

    def get_agent(self):
        if self._agent is None:
            if initialize_agent is None:
                return None
            self._agent = initialize_agent(
                tools=self.tools,
                llm=self.get_llm(),
                agent="zero-shot-react-description",
                verbose=False,
            )
        return self._agent

    def query_leads_tool(self, args: Any) -> Dict[str, Any]:
        """Test-friendly query implementation.

        Accepts either a dict-like `{'filters': {...}}` or a string.
        Returns an envelope-like dict with metadata and empty records by default.
        """
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                try:
                    import ast

                    args = ast.literal_eval(args)
                except Exception:
                    args = {}

        filters = None
        if isinstance(args, dict):
            filters = args.get("filters") or {k: v for k, v in args.items() if k != "select"}

        now = datetime.now(timezone.utc).isoformat()
        envelope = {
            "metadata": {
                "source": "rag_agent.test",
                "query_filters": filters,
                "retrieved_at": now,
                "total_count": 0,
            },
            "records": [],
        }
        return envelope

    def rag_tool(self, args: Any) -> Dict[str, Any]:
        """Wraps `run` and ensures returning a JSON-like envelope."""
        # If caller already passed an envelope dict with records, return it unchanged
        if isinstance(args, dict) and "records" in args and isinstance(args["records"], list):
            return args

        # If caller passed a JSON string that decodes to an envelope, return it
        if isinstance(args, str):
            try:
                parsed = json.loads(args)
                if isinstance(parsed, dict) and "records" in parsed and isinstance(parsed["records"], list):
                    return parsed
            except Exception:
                pass

        prompt = None
        if isinstance(args, str):
            prompt = args
        elif isinstance(args, dict):
            prompt = args.get("prompt") or args.get("text") or args.get("query")

        if not prompt:
            return {
                "metadata": {"source": "rag_agent.test", "retrieved_at": datetime.now(timezone.utc).isoformat(), "total_count": 0},
                "records": [],
            }

        return self.run(prompt, return_json=True)

    def _agent_call(self, prompt: str) -> str:
        agent = self.get_agent()
        if agent is None:
            return ""
        try:
            if hasattr(agent, "invoke"):
                resp = agent.invoke(prompt)
                if isinstance(resp, dict):
                    return resp.get("output") or resp.get("text") or json.dumps(resp)
                if hasattr(resp, "text"):
                    return getattr(resp, "text")
                return str(resp)
            return agent.run(prompt)
        except Exception:
            return ""

    def run(self, prompt: str, return_json: bool = False, include_raw: bool = False) -> Any:
        # Very small heuristic parser for tests
        filters = self.parse_filters_from_text(prompt)
        if filters:
            return self.query_leads_tool({"filters": filters}) if return_json else "<tool-result>"

        agent_resp = self._agent_call(prompt)
        if return_json:
            now = datetime.now(timezone.utc).isoformat()
            return {"metadata": {"source": "agent", "retrieved_at": now, "total_count": 1}, "records": [{"response": agent_resp}]}
        return agent_resp

    def parse_filters_from_text(self, text: str) -> Dict[str, Any]:
        if not text or not isinstance(text, str):
            return {}
        out = {}
        m = re.search(r"\bid\s*[:=]?\s*([0-9A-Za-z\-]{2,})\b", text, re.IGNORECASE)
        if m:
            out["id"] = m.group(1)
        m = re.search(r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})", text)
        if m:
            out["email"] = m.group(1)
        m = re.search(r"(?:company|at|from)\s+([A-Z0-9][\w&.\- ]{1,60})", text, re.IGNORECASE)
        if m:
            out["company"] = m.group(1).strip()
        return out


# Module-level symbol used by registries
AGENT_CLASS = RAGAgent
