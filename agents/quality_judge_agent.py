# agents/quality_judge_agent.py

"""Validates proposal sections by acting as an LLM-based judge."""

from .base_agent import BaseAgent
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class QualityJudgeAgent(BaseAgent):
    def __init__(self, agent_id: str, context_manager: Any):
        super().__init__(agent_id, context_manager)

    async def _core_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        section_content = context.get('section_content', "")
        section_id = context.get('section_id', "")

        if not section_content or not section_id:
            raise ValueError("Section content or section ID is missing in context.")

        prompt = (
            f"You are an expert in proposal writing. Validate the following section for completeness, coherence, style compliance, and content quality:\n\n"
            f"Section ID: {section_id}\n"
            f"Content:\n{section_content}\n\n"
            f"Please respond with 'pass' if the section meets all quality standards, or provide detailed feedback on what needs to be improved."
        )

        try:
            response = await self._call_openai(
                prompt=prompt,
                system_message="You are an expert in proposal quality assurance.",
                model="gpt-4o",
                max_tokens=1000,
                temperature=0.3
            )
            response_text = response.lower()
            if response_text == 'pass':
                return {'output': True, 'reasoning_log': self.reasoning_log}
            else:
                self.logger.warning(f"Quality feedback for section '{section_id}': {response_text}")
                return {'output': False, 'reasoning_log': self.reasoning_log}
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise