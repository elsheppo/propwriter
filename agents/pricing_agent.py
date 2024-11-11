# agents/pricing_agent.py

"""Provides pricing models and budget breakdown using GPT-4."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class PricingAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        engagement_details = context.get('engagement_details', {})
        budget_range = engagement_details.get('budget_range', "")
        project_objectives = engagement_details.get('project_objectives', [])

        if not budget_range:
            raise ValueError("Budget range is missing in engagement details.")
        if not project_objectives:
            raise ValueError("Project objectives are missing in engagement details.")

        prompt = (
            f"Based on the following project objectives and budget range, provide a detailed pricing model and budget breakdown:\n\n"
            f"Budget Range: {budget_range}\n"
            f"Project Objectives: {', '.join(project_objectives)}\n\n"
            f"Pricing Model and Budget Breakdown:"
        )

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are a professional proposal writer specializing in pricing.",
                model="gpt-4",
                max_tokens=500,
                temperature=0.7
            )
            
            pricing_items = response.strip().split('\n')
            pricing = []
            for item in pricing_items:
                service_cost = item.strip('- ').strip()
                if ':' in service_cost:
                    service, cost = service_cost.split(':', 1)
                    pricing.append({'service': service.strip(), 'cost': cost.strip()})
            
            return {
                'output': pricing,
                'reasoning_log': self.reasoning_log
            }
        except Exception as e:
            self.logger.error(f"Failed to generate pricing model: {e}")
            raise