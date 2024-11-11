import asyncio
from typing import List, Dict, Any, Callable
from .dependency_graph import DependencyGraph
from .context_manager import ContextManager
from .quality_control import ProposalQualityControl
from .proposal_assembler import ProposalAssembler
import logging
from datetime import datetime

class AgentStatus:
    """Tracks the current status of an agent."""
    
    def __init__(self, state: str, timestamp: Any, version: int, output: Any = None, error: str = None):
        self.state = state
        self.timestamp = timestamp
        self.version = version
        self.output = output
        self.error = error

class TriggerController:
    """Controls execution flow based on dependencies and manages agents."""
    
    def __init__(self, context_manager: ContextManager, dependency_graph: DependencyGraph, quality_control: ProposalQualityControl, assembler: ProposalAssembler):
        self.context_manager = context_manager
        self.dependency_graph = dependency_graph
        self.quality_control = quality_control
        self.assembler = assembler
        self.agent_status: Dict[str, AgentStatus] = {}
        self.agent_callbacks: Dict[str, Callable[[Dict[str, Any]], Any]] = {}
        self.logger = logging.getLogger(__name__)

    def register_agent(self, agent_id: str, dependencies: List[str], callback: Callable[[Dict[str, Any]], Any]):
        """Register an agent with its dependencies and callback."""
        for dep in dependencies:
            self.dependency_graph.add_dependency(agent_id, dep)
        self.agent_status[agent_id] = AgentStatus(state="pending", timestamp=datetime.now(), version=1)
        self.agent_callbacks[agent_id] = callback
        self.logger.info(f"Registered agent {agent_id} with dependencies {dependencies}")

    async def execute_agent(self, agent_id: str):
        """Execute an agent if dependencies are met."""
        if not self.dependency_graph.check_dependencies_met(agent_id, self.agent_status):
            self.logger.info(f"Dependencies not met for agent {agent_id}. Waiting for dependencies.")
            return

        # Initialize agent-specific context
        self.context_manager.initialize_step_context(agent_id)

        # Log the context for debugging
        input_context = self.context_manager.get_step_context(agent_id)
        self.logger.info(f"Executing agent {agent_id} with context: {input_context}")

        # Proceed with execution as before
        try:
            output = await self.agent_callbacks[agent_id](input_context)
            self.context_manager.update_step_context(agent_id, {"output": output['output']})
            self.agent_status[agent_id].state = "completed"
            self.agent_status[agent_id].output = output['output']
            self.logger.info(f"Agent {agent_id} completed successfully.")
            await self._trigger_dependents(agent_id)
        except Exception as e:
            self.agent_status[agent_id].state = "failed"
            self.agent_status[agent_id].error = str(e)
            self.logger.error(f"Agent {agent_id} failed with error: {e}")

    async def _trigger_dependents(self, agent_id: str):
        """Trigger agents that depend on the completed agent."""
        dependents = self.dependency_graph.get_dependents(agent_id)
        for dependent in dependents:
            if self.dependency_graph.check_dependencies_met(dependent, self.agent_status):
                self.logger.info(f"Triggering dependent agent: {dependent}")
                asyncio.create_task(self.execute_agent(dependent))

    async def run_all(self):
        """Run all agents in order based on dependencies, checking for circular dependencies first."""
        if self.dependency_graph.has_circular_dependency():
            self.logger.error("Circular dependency detected. Cannot execute agents.")
            return

        tasks = []
        for agent_id in self.agent_callbacks.keys():
            if self.dependency_graph.check_dependencies_met(agent_id, self.agent_status):
                tasks.append(asyncio.create_task(self.execute_agent(agent_id)))

        if tasks:
            await asyncio.gather(*tasks)
        else:
            self.logger.info("No agents ready for execution.")