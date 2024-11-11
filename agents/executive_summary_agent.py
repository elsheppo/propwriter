# agents/executive_summary_agent.py

"""Generates an executive summary using GPT-4."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ExecutiveSummaryAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        client_info = context.get('client_info', {})
        engagement_details = context.get('engagement_details', {})
        project_objectives = engagement_details.get('project_objectives', [])

        if not client_info:
            raise ValueError("Client information is missing in context.")
        if not project_objectives:
            raise ValueError("Project objectives are missing in engagement details.")

        prompt = (
            f"Create an executive summary for a proposal based on the following details:\n\n"
            f"Client Name: {client_info.get('company_name')}\n"
            f"Industry: {client_info.get('industry')}\n"
            f"Company Size: {client_info.get('size')}\n"
            f"Key Objectives: {', '.join(project_objectives)}\n\n"
            f"Executive Summary:"
        )

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a professional proposal writer.",
                model="gpt-4o",
                max_tokens=500,
                temperature=0.7
            )
            return {
                'output': response,
                'reasoning_log': self.reasoning_log
            }
        except Exception as e:
            self.logger.error(f"Failed to generate executive summary: {e}")
            raise