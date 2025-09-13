"""Tools package for small helper modules used by agents.

Re-export common helpers for convenience and provide a discovery registry
for local tools.
"""

from .supabase_tools import SupabaseClient, format_records

__all__ = ["SupabaseClient", "format_records", "registry"]

