"""
Scope Filter — named entry point for the Crovenett-only content rule.

Delegates to response_guardrails for the actual logic; this module exists
to give the rule a clear home in the project structure.
"""
from app.core.response_guardrails import is_out_of_scope, scope_redirect_response

__all__ = ["is_out_of_scope", "scope_redirect_response"]
