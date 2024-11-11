# agents/base_agent.py

"""An abstract base class that defines the structure for all agents, including processing logic, reasoning logs, and validation methods."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
import logging  # Added import for logging
from openai import AsyncOpenAI
import os

class BaseAgent(ABC):
    def __init__(self, agent_id: str, context_manager: Any):
        print(f"Initializing BaseAgent for {agent_id}")  # Add this debug line
        self.agent_id = agent_id
        self.context_manager = context_manager
        self.reasoning_log = []
        self.logger = logging.getLogger(self.__class__.__name__)  # Initialized logger
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def _call_openai(self, 
                        prompt: str, 
                        system_message: str = "You are a professional proposal writer.",
                        model: str = "gpt-4",
                        max_tokens: int = 500,
                        temperature: float = 0.7) -> str:
        """Helper method for OpenAI API calls."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # The response object should be awaited and message.content accessed
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"OpenAI API error in base agent: {str(e)}")
            # Print more debug info
            self.logger.error(f"Response type: {type(response)}")
            self.logger.error(f"Response dir: {dir(response)}")
            raise

    async def process(self, input_context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._validate_input_context(input_context)
            start_time = datetime.now()
            self.log_reasoning('Processing Start', f'Begin processing at {start_time}')
            result = await self._core_process(input_context)
            self._validate_output(result)
            processing_time = datetime.now() - start_time
            self.log_reasoning('Processing Complete', f'Completed in {processing_time}')
            return {
                'output': result,
                'reasoning_log': self.reasoning_log,
                'metadata': {
                    'processing_time': str(processing_time),
                    'input_hash': hash(str(input_context)),
                    'version': self.context_manager.get_context_version(self.agent_id)
                }
            }
        except Exception as e:
            self.log_reasoning('Processing Error', str(e))
            self.logger.error(f"Error processing agent {self.agent_id}: {e}")
            raise

    @abstractmethod
    async def _core_process(self, context: Dict[str, Any]) -> Any:
        """To be implemented by specific agents"""
        pass

    def log_reasoning(self, step: str, rationale: str):
        """Log reasoning steps for transparency"""
        self.reasoning_log.append({
            'step': step,
            'rationale': rationale,
            'timestamp': datetime.now()
        })

    def _validate_input_context(self, input_context: Dict[str, Any]):
        """Validate input context before processing"""
        if not input_context:
            raise ValueError("Input context is empty.")

    def _validate_output(self, result: Any):
        """Validate output after processing"""
        if not result:
            raise ValueError("Processing result is empty.")

    