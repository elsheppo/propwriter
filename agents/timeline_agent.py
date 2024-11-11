# agents/timeline_agent.py

"""Develops a detailed project timeline using GPT-4."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class TimelineAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        engagement_details = context.get('engagement_details', {})
        timeline = engagement_details.get('timeline', "")
        project_objectives = engagement_details.get('project_objectives', [])

        if not project_objectives:
            raise ValueError("Project objectives are missing in engagement details.")

        prompt = (
            f"Based on the following project objectives and timeline, develop a detailed project timeline:\n\n"
            f"Timeline: {timeline}\n"
            f"Project Objectives: {', '.join(project_objectives)}\n\n"
            f"Project Timeline:"
        )

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a professional project planner.",
                model="gpt-4",
                max_tokens=500,
                temperature=0.7
            )
            
            milestones = [m.strip('- ').strip() for m in response.split('\n') if m.strip()]
            return {
                'output': milestones,
                'reasoning_log': self.reasoning_log
            }
        except Exception as e:
            self.logger.error(f"Failed to generate timeline: {e}")
            raise