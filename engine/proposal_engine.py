# engine/proposal_engine.py

"""The core engine that initializes contexts, registers agents, manages execution flow, and triggers the proposal assembly process."""

from services.context_manager import ContextManager
from services.dependency_graph import DependencyGraph
from services.quality_control import ProposalQualityControl
from services.proposal_assembler import ProposalAssembler
from services.trigger_controller import TriggerController, AgentStatus
from agents.scope_agent import ScopeAgent
from agents.value_proposition_agent import ValuePropositionAgent
from agents.executive_summary_agent import ExecutiveSummaryAgent
from agents.approach_agent import ApproachAgent
from agents.timeline_agent import TimelineAgent
from agents.team_agent import TeamAgent
from agents.pricing_agent import PricingAgent
from typing import Dict, Any
from datetime import datetime
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

class ProposalEngine:
    """Main entry point for proposal generation"""
    def __init__(self):
        self.context_manager = ContextManager()
        self.dependency_graph = DependencyGraph()
        self.quality_control = ProposalQualityControl(self.context_manager)
        self.assembler = ProposalAssembler(self.context_manager)
        self.trigger_controller = TriggerController(
            context_manager=self.context_manager,
            dependency_graph=self.dependency_graph,
            quality_control=self.quality_control,
            assembler=self.assembler
        )
        self.logger = logging.getLogger(__name__)

    async def generate_proposal(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a full proposal based on given configuration"""
        try:
            self.context_manager.update_master_context({
                'client_info': {
                    'company_name': config['client_info']['company_name'],
                    'industry': config['client_info']['industry'],
                    'size': config['client_info']['size'],
                    'location': config['client_info']['location'],
                    'contact_person': config['client_info']['contact_person']
                },
                'engagement_details': {
                    'engagement_size': config['engagement_details']['engagement_size'],
                    'timeline': config['engagement_details']['timeline'],
                    'budget_range': config['engagement_details']['budget_range'],
                    'project_objectives': config['engagement_details']['project_objectives'],
                    'custom_requirements': config['specific_requirements']['custom_requirements'],
                    'key_challenges': config['specific_requirements']['key_challenges'],
                    'success_metrics': config['specific_requirements']['success_metrics'],
                    'stakeholder_expectations': config['specific_requirements']['stakeholder_expectations']
                },
                'proposal_requirements': {
                    'sections': config['proposal_needs']['sections'],
                    'document_style': config['proposal_needs']['document_style'],
                    'key_objectives': config['proposal_needs'].get('key_objectives', [])
                },
                'additional_notes': config['proposal_needs'].get('additional_notes', "")
            })

            # Create recovery point
            recovery_point = await self._create_recovery_point()

            try:
                # Register agents with dependencies
                await self._register_agents()

                # Execute all agents
                await self.trigger_controller.run_all()

                # Assemble proposal
                proposal = await self.assembler.assemble_proposal()

                # Validate final output
                if not await self._validate_final_proposal(proposal):
                    raise ValueError("Final proposal validation failed")

                return proposal

            except Exception as e:
                # Attempt recovery
                await self._recover_from_error(recovery_point, e)
                raise

        except Exception as e:
            self.logger.error(f"Proposal generation failed: {e}")
            raise

    async def _register_agents(self):
        """Register agents for each proposal section"""
        # Instantiate agents
        scope_agent = ScopeAgent("scope_agent", self.context_manager)
        value_prop_agent = ValuePropositionAgent("value_proposition_agent", self.context_manager)
        exec_summary_agent = ExecutiveSummaryAgent("executive_summary_agent", self.context_manager)
        approach_agent = ApproachAgent("approach_agent", self.context_manager)
        timeline_agent = TimelineAgent("timeline_agent", self.context_manager)
        team_agent = TeamAgent("team_agent", self.context_manager)
        pricing_agent = PricingAgent("pricing_agent", self.context_manager)

        # Register ScopeAgent (no dependencies)
        self.trigger_controller.register_agent(
            agent_id="scope_agent",
            dependencies=[],
            callback=scope_agent.process
        )

        # Register ValuePropositionAgent (depends on ScopeAgent)
        self.trigger_controller.register_agent(
            agent_id="value_proposition_agent",
            dependencies=["scope_agent"],
            callback=value_prop_agent.process
        )

        # Register ExecutiveSummaryAgent (depends on ValuePropositionAgent)
        self.trigger_controller.register_agent(
            agent_id="executive_summary_agent",
            dependencies=["value_proposition_agent"],
            callback=exec_summary_agent.process
        )

        # Register ApproachAgent (depends on ExecutiveSummaryAgent)
        self.trigger_controller.register_agent(
            agent_id="approach_agent",
            dependencies=["executive_summary_agent"],
            callback=approach_agent.process
        )

        # Register TimelineAgent (depends on ApproachAgent)
        self.trigger_controller.register_agent(
            agent_id="timeline_agent",
            dependencies=["approach_agent"],
            callback=timeline_agent.process
        )

        # Register TeamAgent (depends on TimelineAgent)
        self.trigger_controller.register_agent(
            agent_id="team_agent",
            dependencies=["timeline_agent"],
            callback=team_agent.process
        )

        # Register PricingAgent (depends on TeamAgent)
        self.trigger_controller.register_agent(
            agent_id="pricing_agent",
            dependencies=["team_agent"],
            callback=pricing_agent.process
        )

    async def _create_recovery_point(self) -> Dict[str, Any]:
        """Create a recovery point to revert to in case of error"""
        return {
            'master_context': self.context_manager.master_context.copy(),
            'step_contexts': {k: v.copy() for k, v in self.context_manager.step_contexts.items()}
        }

    async def _recover_from_error(self, recovery_point: Dict[str, Any], error: Exception):
        """Attempt to recover from an error using the saved recovery point"""
        self.logger.warning(f"Attempting recovery due to error: {error}")
        self.context_manager.master_context = recovery_point['master_context']
        self.context_manager.step_contexts = recovery_point['step_contexts']
        # Reset agent statuses
        for agent_id in self.trigger_controller.agent_status:
            self.trigger_controller.agent_status[agent_id].state = "pending"
            self.trigger_controller.agent_status[agent_id].output = None
            self.trigger_controller.agent_status[agent_id].error = None
        # Optionally, re-execute agents or notify the user for manual intervention

    async def _validate_final_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Validate the final proposal output"""
        # Placeholder for additional validation if needed
        return True
