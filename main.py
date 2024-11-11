# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.context_manager import ContextManager
from services.trigger_controller import TriggerController
from services.dependency_graph import DependencyGraph
from services.quality_control import ProposalQualityControl
from services.proposal_assembler import ProposalAssembler
from agents.approach_agent import ApproachAgent
from agents.executive_summary_agent import ExecutiveSummaryAgent
from agents.pricing_agent import PricingAgent
from agents.scope_agent import ScopeAgent
from agents.team_agent import TeamAgent
from agents.timeline_agent import TimelineAgent
from agents.value_proposition_agent import ValuePropositionAgent
from agents.quality_judge_agent import QualityJudgeAgent
import asyncio
import logging
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this if your frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
context_manager = ContextManager()
dependency_graph = DependencyGraph()
quality_control = ProposalQualityControl(context_manager)
proposal_assembler = ProposalAssembler(context_manager)
trigger_controller = TriggerController(context_manager, dependency_graph, quality_control, proposal_assembler)

# Initialize Agents
agents = {
    "approach_agent": ApproachAgent("approach_agent", context_manager),
    "executive_summary_agent": ExecutiveSummaryAgent("executive_summary_agent", context_manager),
    "pricing_agent": PricingAgent("pricing_agent", context_manager),
    "scope_agent": ScopeAgent("scope_agent", context_manager),
    "team_agent": TeamAgent("team_agent", context_manager),
    "timeline_agent": TimelineAgent("timeline_agent", context_manager),
    "value_proposition_agent": ValuePropositionAgent("value_proposition_agent", context_manager),
    # "quality_judge_agent": QualityJudgeAgent("quality_judge_agent", context_manager),
}

# Define Agent Dependencies
agent_dependencies = {
    "executive_summary_agent": ["value_proposition_agent"],
    "approach_agent": ["scope_agent"],
    "pricing_agent": ["scope_agent"],
    "team_agent": ["scope_agent"],
    "timeline_agent": ["approach_agent"],
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Register Agents with TriggerController
for agent_id, agent in agents.items():
    dependencies = agent_dependencies.get(agent_id, [])
    trigger_controller.register_agent(agent_id, dependencies, agent.process)

# Define Pydantic Models for Request and Response

class ContactPersonModel(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None

class ClientInfoModel(BaseModel):
    company_name: str
    industry: str
    size: str
    location: Optional[str] = None
    contact_person: ContactPersonModel

class EngagementDetailsModel(BaseModel):
    engagement_size: str
    timeline: str
    budget_range: str
    project_objectives: List[str] = Field(default_factory=list)
    custom_requirements: List[str] = Field(default_factory=list)
    key_challenges: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    stakeholder_expectations: List[str] = Field(default_factory=list)

class SpecificRequirementsModel(BaseModel):
    custom_requirements: List[str] = Field(default_factory=list)
    key_challenges: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    stakeholder_expectations: List[str] = Field(default_factory=list)

class ProposalNeedsModel(BaseModel):
    sections: List[str] = Field(default_factory=list)
    document_style: str
    additional_notes: Optional[str] = ""

class ProposalConfigModel(BaseModel):
    client_info: ClientInfoModel
    engagement_details: EngagementDetailsModel
    specific_requirements: SpecificRequirementsModel
    proposal_needs: ProposalNeedsModel

class ProposalGenerateRequest(BaseModel):
    config: ProposalConfigModel

class ProposalGenerateResponse(BaseModel):
    main_document: str
    executive_summary: str
    approach: str
    timeline: str
    team: str
    pricing: str
    appendices: str

# Define API Endpoints

@app.post("/context", response_model=dict)
async def create_context(request: ProposalGenerateRequest):
    try:
        # Update the master context with received data
        context_manager.update_master_context(request.config.dict())
        
        # Start the proposal generation process asynchronously
        asyncio.create_task(trigger_controller.run_all())
        
        return {"message": "Context created successfully."}
    except Exception as e:
        logging.error(f"Error in /context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status", response_model=List[dict])
async def get_status():
    try:
        statuses = []
        for agent_id, status in trigger_controller.agent_status.items():
            statuses.append({
                "agent_id": agent_id,
                "state": status.state,
                "timestamp": status.timestamp.isoformat(),
            })
        return statuses
    except Exception as e:
        logging.error(f"Error in /status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sections/{agent_id}", response_model=dict)
async def get_section(agent_id: str):
    try:
        section = context_manager.get_step_context(agent_id)
        if "output" in section:
            return {"output": section["output"]}
        else:
            raise HTTPException(status_code=404, detail="Section not found or not yet generated.")
    except Exception as e:
        logging.error(f"Error in /sections/{agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proposal/preview", response_model=dict)
async def get_proposal_preview():
    try:
        outputs = await proposal_assembler.assemble_proposal()
        # Return HTML content for preview
        main_html = outputs.get("main_document_html", "")
        return {"html_content": main_html}
    except Exception as e:
        logging.error(f"Error in /proposal/preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/proposal/submit", response_model=dict)
async def submit_proposal():
    try:
        outputs = await proposal_assembler.assemble_proposal()
        # Implement submission logic, e.g., save to database, send emails, etc.
        # For demonstration, we'll just acknowledge the submission.
        # If outputs contain PDFs, you might want to handle them appropriately.
        # Here, we'll assume outputs are already stored or handled.
        return {"message": "Proposal submitted successfully.", "outputs": {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in outputs.items()}}
    except Exception as e:
        logging.error(f"Error in /proposal/submit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_model=str)
async def root():
    return "Proposal Generation Backend is running."
