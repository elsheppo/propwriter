# agents/value_proposition_agent.py

"""Crafts the value proposition using GPT-4 based on the client configuration."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ValuePropositionAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        client_info = context.get('client_info', {})
        engagement_details = context.get('engagement_details', {})
        project_objectives = engagement_details.get('project_objectives', [])
        proposal_needs = context.get('proposal_needs', {})

        if not client_info:
            raise ValueError("Client information is missing in context.")
        if not project_objectives:
            raise ValueError("Project objectives are missing in engagement details.")

        document_style = proposal_needs.get('document_style', 'Formal')
        additional_notes = proposal_needs.get('additional_notes', '')

        prompt = (
            f"Based on the following client information and project objectives, generate a compelling value proposition for a proposal.\n\n"
            f"Client Name: {client_info.get('company_name')}\n"
            f"Industry: {client_info.get('industry')}\n"
            f"Company Size: {client_info.get('size')}\n"
            f"Project Objectives: {', '.join(project_objectives)}\n"
            f"Document Style: {document_style}\n"
            f"Additional Notes: {additional_notes}\n\n"
            f"Value Proposition:"
        )

        try:
            print("About to call _call_openai")  # Add this line
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a professional proposal writer.",
                model="gpt-4",
                max_tokens=500,
                temperature=0.7
            )
            return {
                'output': response,
                'reasoning_log': self.reasoning_log
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise