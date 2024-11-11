# agents/team_agent.py

"""Describes the proposed team structure and expertise using GPT-4."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class TeamAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        client_info = context.get('client_info', {})
        project_objectives = context.get('engagement_details', {}).get('project_objectives', [])

        if not client_info:
            raise ValueError("Client information is missing in context.")
        if not project_objectives:
            raise ValueError("Project objectives are missing in engagement details.")

        prompt = (
            f"Based on the following client information and project objectives, describe the proposed team structure and expertise for the project:\n\n"
            f"Client Name: {client_info.get('company_name')}\n"
            f"Project Objectives: {', '.join(project_objectives)}\n\n"
            f"Team Structure:"
        )

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a professional proposal writer specializing in team composition.",
                model="gpt-4o",
                max_tokens=500,
                temperature=0.7
            )
            
            team_members = response.split('\n')
            team = []
            for member in team_members:
                name_role, description = member.split(':', 1) if ':' in member else (member, "")
                team.append({
                    'name': name_role.strip(),
                    'role': '',
                    'description': description.strip()
                })
                
            return {
                'output': team,
                'reasoning_log': self.reasoning_log
            }
        except Exception as e:
            self.logger.error(f"Failed to generate team structure: {e}")
            raise
