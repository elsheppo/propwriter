# services/proposal_assembler.py

"""Collects outputs from all agents, validates them, structures the narrative, applies formatting, and generates the final proposal outputs (e.g., PDFs)."""

from typing import Dict, Any, List
from .context_manager import ContextManager
from .quality_control import ProposalQualityControl
from jinja2 import Environment, FileSystemLoader
import pdfkit
import logging
import yaml
import os

class ProposalAssembler:
    """Assembles the final proposal from agent outputs."""
    
    def __init__(self, context_manager: ContextManager):
        self.context_manager = context_manager
        self.quality_control = ProposalQualityControl(context_manager)
        
        # Set up Jinja2 environment to load templates from the correct directory
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.template_engine = Environment(loader=FileSystemLoader(template_dir))
        
        # Load style configuration from YAML file
        self.style_config = self._load_style_config()
        self.logger = logging.getLogger(self.__class__.__name__)

    agent_to_section_map = {
        "executive_summary_agent": "executive_summary",
        "approach_agent": "approach",
        "pricing_agent": "pricing",
        "scope_agent": "scope",
        "team_agent": "team",
        "timeline_agent": "timeline",
        "value_proposition_agent": "value_proposition",
    }

    async def assemble_proposal(self) -> Dict[str, Any]:
        """Assemble, validate, and structure the proposal."""
        
        # Collect content from all agent-generated sections
        sections = self._collect_section_content()

        # Validate sections
        if not await self.quality_control.validate_proposal(sections):
            self.logger.error("Proposal failed quality validation.")
            raise ValueError("Proposal failed quality validation.")

        # Structure and format narrative content
        structured_content = self._structure_narrative(sections)
        formatted_content = self._apply_formatting(structured_content)

        # Generate the final outputs
        outputs = self._generate_outputs(formatted_content)

        return outputs

    def _collect_section_content(self) -> Dict[str, str]:
        """Collect content from all sections based on context manager data."""
        
        sections = {}
        for agent_id, content in self.context_manager.step_contexts.items():
            if 'output' in content and agent_id in self.agent_to_section_map:
                section_name = self.agent_to_section_map[agent_id]
                sections[section_name] = content['output']
        return sections

    def _structure_narrative(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Organize and structure proposal narrative by sections."""
        
        # Define proposal section ordering
        ordered_sections = [
            "executive_summary", "understanding", "approach", "scope",
            "timeline", "team", "pricing", "appendices", "value_proposition"
        ]
        
        narrative_sections = [
            {'section_id': section_id, 'content': sections.get(section_id, "")}
            for section_id in ordered_sections if section_id in sections
        ]
        
        return {'sections': narrative_sections, 'transitions': {}}

    def _apply_formatting(self, structured_content: Dict[str, Any]) -> Dict[str, Any]:
        """Apply styles and format content based on narrative structure."""
        
        # Here you might apply styles based on `self.style_config`
        # Currently, this function returns the structured content as-is
        return structured_content

    def _generate_outputs(self, formatted_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multiple outputs, including the main proposal document and section-specific PDFs."""
        
        outputs = {}

        # Generate main proposal document as HTML for preview
        main_template = self.template_engine.get_template("main_template.html")
        main_html = main_template.render(sections=formatted_content['sections'])
        outputs['main_document_html'] = main_html  # HTML for preview

        # Generate main proposal PDF
        main_pdf = pdfkit.from_string(main_html, False)
        outputs['main_document_pdf'] = main_pdf

        # Generate additional sections PDFs
        sections = ['executive_summary', 'approach', 'timeline', 'team', 'pricing', 'appendices']
        
        for section_name in sections:
            content = next(
                (section['content'] for section in formatted_content['sections'] if section['section_id'] == section_name),
                ""
            )
            if content:
                try:
                    template = self.template_engine.get_template(f"{section_name}_template.html")
                    render_params = {section_name: content}
                    html = template.render(**render_params)
                    pdf = pdfkit.from_string(html, False)
                    outputs[f"{section_name}_pdf"] = pdf
                except Exception as e:
                    self.logger.error(f"Error generating PDF for {section_name}: {e}")
        
        self.logger.info("Proposal assembled successfully.")
        return outputs


    def _load_style_config(self) -> Dict[str, Any]:
        """Load and return style configuration from a YAML file."""
        
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'proposal_styles.yaml')
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        else:
            self.logger.warning("Style configuration file not found; using default styles.")
            return {}
