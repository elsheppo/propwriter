# services/quality_control.py

"""Validates proposal sections and overall coherence using the QualityJudgeAgent."""

from typing import Dict, Any
from .context_manager import ContextManager
from agents.quality_judge_agent import QualityJudgeAgent
import asyncio
import logging

class ProposalQualityControl:
    """Validates proposal sections and overall coherence"""
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.quality_judge_agent = QualityJudgeAgent("quality_judge_agent", context_manager)
        self.logger = logging.getLogger(__name__)

    async def validate_section(self, section_id: str, content: str) -> bool:
        """Validate a specific section using the QualityJudgeAgent"""
        context = {
            'section_id': section_id,
            'section_content': content
        }
        validation_result = await self.quality_judge_agent.process(context)
        if validation_result:
            self.logger.info(f"Section '{section_id}' passed quality validation.")
            return True
        else:
            self.logger.warning(f"Section '{section_id}' failed quality validation.")
            return False

    async def validate_proposal(self, sections: Dict[str, Any]) -> bool:
        """Validate all sections of the proposal"""
        tasks = []
        for section_id, content in sections.items():
            tasks.append(self.validate_section(section_id, content))
        results = await asyncio.gather(*tasks)
        return all(results)