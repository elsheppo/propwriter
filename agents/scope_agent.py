# agents/scope_agent.py

"""Defines the project scope based on client information."""

from .base_agent import BaseAgent
from typing import Dict, Any

class ScopeAgent(BaseAgent):
    async def _core_process(self, context: Dict[str, Any]) -> str:
        client_info = context.get('client_info', {})
        engagement_details = context.get('engagement_details', {})
        specific_requirements = context.get('specific_requirements', {})
        custom_requirements = engagement_details.get('custom_requirements', [])

        # Check if necessary data is present
        if not client_info:
            raise ValueError("Client information is missing in context.")
        if not engagement_details:
            raise ValueError("Engagement details are missing in context.")

        scope = (
            f"Project Scope for {client_info.get('company_name')}:\n"
            f"- Industry: {client_info.get('industry')}\n"
            f"- Size: {client_info.get('size')}\n"
            f"- Location: {client_info.get('location')}\n"
            f"- Engagement Size: {engagement_details.get('engagement_size')}\n"
            f"- Timeline: {engagement_details.get('timeline')}\n"
            f"- Budget Range: {engagement_details.get('budget_range')}\n\n"
            f"Custom Requirements:\n"
        )

        for req in custom_requirements:
            scope += f"- {req}\n"

        scope += "\nThis project will focus on addressing the key challenges identified by the client, including:\n"

        key_challenges = specific_requirements.get('key_challenges', [])
        for challenge in key_challenges:
            scope += f"- {challenge}\n"

        return scope