# services/context_manager.py

from typing import Dict, Any
from collections import defaultdict
from datetime import datetime
import logging

class ContextManager:
    """Manages both master and step-specific context for agents."""
    
    def __init__(self):
        self.master_context: Dict[str, Any] = {}  # Stores shared context data
        self.step_contexts: Dict[str, Dict[str, Any]] = {}  # Individual agent-specific contexts
        self.context_versions: Dict[str, int] = defaultdict(int)
        self.context_history = []  # For tracking updates over time
        self.logger = logging.getLogger(self.__class__.__name__)

    def initialize_master_context(self, initial_data: Dict[str, Any]):
        """Initialize the master context at the beginning of the proposal generation process."""
        self.master_context = initial_data
        self.logger.info("Master context initialized with data.")
        self._log_context_update('master_context', initial_data)

    def get_master_context(self) -> Dict[str, Any]:
        """Return the master context."""
        return self.master_context

    def update_master_context(self, new_data: Dict[str, Any]):
        """Update the master context and log the change."""
        self.master_context.update(new_data)
        self.logger.info("Master context updated.")
        self._log_context_update('master_context', new_data)

    def initialize_step_context(self, agent_id: str):
        """Initialize context for a specific agent using relevant data from master context."""
        if agent_id not in self.step_contexts:
            # Base contexts for specific agents
            if agent_id == 'scope_agent':
                self.step_contexts[agent_id] = {
                    'client_info': self.master_context.get('client_info', {}),
                    'engagement_details': self.master_context.get('engagement_details', {}),
                    'specific_requirements': self.master_context.get('specific_requirements', {}),
                }
            elif agent_id == 'value_proposition_agent':
                self.step_contexts[agent_id] = {
                    'client_info': self.master_context.get('client_info', {}),
                    'engagement_details': self.master_context.get('engagement_details', {}),
                    'proposal_needs': self.master_context.get('proposal_needs', {}),
                }
            elif agent_id == 'quality_judge_agent':
                self.step_contexts[agent_id] = {
                    'section_content': None,
                    'section_id': None,
                }
            # Add specific contexts for dependent agents
            elif agent_id in ['approach_agent', 'pricing_agent', 'team_agent']:
                # These depend on scope_agent
                self.step_contexts[agent_id] = {
                    'client_info': self.master_context.get('client_info', {}),
                    'engagement_details': self.master_context.get('engagement_details', {}),
                    'scope_output': self.step_contexts.get('scope_agent', {}).get('output', '')
                }
            elif agent_id == 'timeline_agent':
                # Depends on approach_agent
                self.step_contexts[agent_id] = {
                    'client_info': self.master_context.get('client_info', {}),
                    'engagement_details': self.master_context.get('engagement_details', {}),
                    'approach_output': self.step_contexts.get('approach_agent', {}).get('output', '')
                }
            elif agent_id == 'executive_summary_agent':
                # Depends on value_proposition_agent
                self.step_contexts[agent_id] = {
                    'client_info': self.master_context.get('client_info', {}),
                    'engagement_details': self.master_context.get('engagement_details', {}),
                    'value_proposition_output': self.step_contexts.get('value_proposition_agent', {}).get('output', '')
                }
            else:
                self.step_contexts[agent_id] = {}

            # Log the initialized context
            self.logger.info(f"Initialized step context for {agent_id}: {self.step_contexts[agent_id]}")

    def get_step_context(self, agent_id: str) -> Dict[str, Any]:
        """Return the context for a specific agent."""
        return self.step_contexts.get(agent_id, {})

    def update_step_context(self, agent_id: str, new_data: Dict[str, Any]):
        """Update and log changes in a specific agent's context."""
        if agent_id not in self.step_contexts:
            self.step_contexts[agent_id] = {}
        self.step_contexts[agent_id].update(new_data)
        self.context_versions[agent_id] += 1
        self.logger.info(f"Step context updated for {agent_id}: {self.step_contexts[agent_id]}")
        self._log_context_update(agent_id, new_data)

    def _log_context_update(self, context_name: str, update: Dict[str, Any]):
        """Log each update to the context for tracking."""
        self.context_history.append({
            'timestamp': datetime.now(),
            'context_name': context_name,
            'update': update,
            'version': self.context_versions[context_name]
        })
        self.logger.info(f"Context update logged for {context_name}")

    def get_context_history(self) -> list:
        """Retrieve the entire history of context updates for auditing."""
        return self.context_history
    
    def get_context_version(self, agent_id: str) -> int:
        """Retrieve the current version of the context for a specific agent."""
        return self.context_versions.get(agent_id, 0)
