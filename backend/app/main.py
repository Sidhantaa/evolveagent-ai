from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router, linear_poll_worker, scheduler_tick_worker
from app.api.discovery_routes import router as discovery_router
from app.api.system_routes import router as system_router
from app.api.memory_v2_routes import router as memory_v2_router
from app.api.agent_registry_routes import router as agent_registry_router
from app.api.agent_governance_routes import router as agent_governance_router
from app.api.event_bus_routes import router as event_bus_router
from app.api.agent_quality_routes import router as agent_quality_router
from app.api.business_intel_routes import router as business_intel_router
from app.api.data_export_routes import router as data_export_router
from app.api.governance_console_routes import router as governance_console_router
from app.api.health_monitor_routes import router as health_monitor_router
from app.api.integration_hub_routes import router as integration_hub_router
from app.api.launch_console_routes import router as launch_console_router
from app.api.meeting_intel_routes import router as meeting_intel_router
from app.api.productivity_routes import router as productivity_router
from app.api.real_api_routes import router as real_api_router
from app.api.simulations_routes import router as simulations_router
from app.api.system_prompts_routes import router as system_prompts_router
from app.api.learning_routes import router as learning_router
from app.api.os_routes import router as os_router
from app.api.master_agent_routes import router as master_agent_router
from app.api.notifications_inbox_routes import router as notifications_inbox_router
from app.api.approvals_center_routes import router as approvals_center_router
from app.api.retrieval_routes import router as retrieval_router
from app.api.os2_routes import router as os2_router
from app.api.usage_ledger_routes import router as usage_ledger_router
from app.api.features_routes import router as features_router
from app.api.export_center_routes import router as export_center_router
from app.api.import_center_routes import router as import_center_router
from app.api.provider_control_routes import router as provider_control_router
from app.api.qa_center_routes import router as qa_center_router
from app.api.workspace_templates_routes import router as workspace_templates_router
from app.api.release_manager_routes import router as release_manager_router
from app.api.playbooks_routes import router as playbooks_router
from app.api.debate_routes import router as debate_router
from app.api.data_manager_routes import router as data_manager_router
from app.api.code_intel_routes import router as code_intel_router
from app.api.goals_routes import router as goals_router
from app.api.github_connector_routes import router as github_connector_router
from app.api.app_builder_routes import router as app_builder_router
from app.api.digital_twin_routes import router as digital_twin_router
from app.api.doc_intel_routes import router as doc_intel_router
from app.api.eval_harness_routes import router as eval_harness_router
from app.api.integrations_routes import router as integrations_router
from app.api.operating_layer_2_routes import router as operating_layer_2_router
from app.api.permissions_routes import router as permissions_router
from app.api.plugin_marketplace_routes import router as plugin_marketplace_router
from app.api.portfolio_routes import router as portfolio_router
from app.api.quality_routes import router as quality_router
from app.api.scheduled_tasks_routes import router as scheduled_tasks_router
from app.api.tools_routes import router as tools_router
from app.api.team_manager_routes import router as team_manager_router
from app.api.self_healing_routes import router as self_healing_router
from app.api.research_agent_routes import router as research_agent_router
from app.api.project_manager_routes import router as project_manager_router
from app.api.operating_layer_routes import router as operating_layer_router
from app.api.multimodal_routes import router as multimodal_router
from app.api.industry_modes_routes import router as industry_modes_router
from app.api.evaluation_routes import router as evaluation_router
from app.api.device_operator_routes import router as device_operator_router
from app.api.demo_routes import router as demo_router
from app.api.company_brain_routes import router as company_brain_router
from app.api.chief_of_staff_routes import router as chief_of_staff_router
from app.api.business_simulator_routes import router as business_simulator_router
from app.api.business_routes import router as business_router
from app.api.autopilot_routes import router as autopilot_router
from app.api.agent_studio_routes import router as agent_studio_router
from app.api.agent_network_routes import router as agent_network_router
from app.api.agent_marketplace_routes import router as agent_marketplace_router
from app.api.agent_jobs_routes import router as agent_jobs_router
from app.api.hardware_companion_routes import router as hardware_companion_router
from app.api.organization_os_routes import router as organization_os_router
from app.api.simulation_world_routes import router as simulation_world_router
from app.api.innovation_lab_routes import router as innovation_lab_router
from app.api.executive_board_routes import router as executive_board_router
from app.api.business_operator_routes import router as business_operator_router
from app.api.saas_builder_routes import router as saas_builder_router
from app.api.universal_operator_routes import router as universal_operator_router
from app.api.life_os_routes import router as life_os_router
from app.api.avatar_routes import router as avatar_router
from app.api.training_lab_routes import router as training_lab_router
from app.api.departments_routes import router as departments_router
from app.api.research_routes import router as research_router
from app.api.feature_routes import router as feature_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await linear_poll_worker.start()
    await scheduler_tick_worker.start()  # no-op unless SCHEDULER_TICK_ENABLED=true
    yield
    await scheduler_tick_worker.stop()
    await linear_poll_worker.stop()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "project": settings.app_name}


app.include_router(router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(memory_v2_router, prefix="/api")
app.include_router(agent_registry_router, prefix="/api")
app.include_router(agent_governance_router, prefix="/api")
app.include_router(event_bus_router, prefix="/api")
app.include_router(agent_quality_router, prefix="/api")
app.include_router(business_intel_router, prefix="/api")
app.include_router(data_export_router, prefix="/api")
app.include_router(governance_console_router, prefix="/api")
app.include_router(health_monitor_router, prefix="/api")
app.include_router(integration_hub_router, prefix="/api")
app.include_router(launch_console_router, prefix="/api")
app.include_router(meeting_intel_router, prefix="/api")
app.include_router(productivity_router, prefix="/api")
app.include_router(real_api_router, prefix="/api")
app.include_router(simulations_router, prefix="/api")
app.include_router(system_prompts_router, prefix="/api")
app.include_router(learning_router, prefix="/api")
app.include_router(os_router, prefix="/api")
app.include_router(master_agent_router, prefix="/api")
app.include_router(notifications_inbox_router, prefix="/api")
app.include_router(approvals_center_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api")
app.include_router(os2_router, prefix="/api")
app.include_router(usage_ledger_router, prefix="/api")
app.include_router(features_router, prefix="/api")
app.include_router(export_center_router, prefix="/api")
app.include_router(import_center_router, prefix="/api")
app.include_router(provider_control_router, prefix="/api")
app.include_router(qa_center_router, prefix="/api")
app.include_router(workspace_templates_router, prefix="/api")
app.include_router(release_manager_router, prefix="/api")
app.include_router(playbooks_router, prefix="/api")
app.include_router(debate_router, prefix="/api")
app.include_router(data_manager_router, prefix="/api")
app.include_router(code_intel_router, prefix="/api")
app.include_router(goals_router, prefix="/api")
app.include_router(github_connector_router, prefix="/api")
app.include_router(app_builder_router, prefix="/api")
app.include_router(digital_twin_router, prefix="/api")
app.include_router(doc_intel_router, prefix="/api")
app.include_router(eval_harness_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(operating_layer_2_router, prefix="/api")
app.include_router(permissions_router, prefix="/api")
app.include_router(plugin_marketplace_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api")
app.include_router(quality_router, prefix="/api")
app.include_router(scheduled_tasks_router, prefix="/api")
app.include_router(tools_router, prefix="/api")
app.include_router(team_manager_router, prefix="/api")
app.include_router(self_healing_router, prefix="/api")
app.include_router(research_agent_router, prefix="/api")
app.include_router(project_manager_router, prefix="/api")
app.include_router(operating_layer_router, prefix="/api")
app.include_router(multimodal_router, prefix="/api")
app.include_router(industry_modes_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(device_operator_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(company_brain_router, prefix="/api")
app.include_router(chief_of_staff_router, prefix="/api")
app.include_router(business_simulator_router, prefix="/api")
app.include_router(business_router, prefix="/api")
app.include_router(autopilot_router, prefix="/api")
app.include_router(agent_studio_router, prefix="/api")
app.include_router(agent_network_router, prefix="/api")
app.include_router(agent_marketplace_router, prefix="/api")
app.include_router(agent_jobs_router, prefix="/api")
app.include_router(hardware_companion_router, prefix="/api")
app.include_router(organization_os_router, prefix="/api")
app.include_router(simulation_world_router, prefix="/api")
app.include_router(innovation_lab_router, prefix="/api")
app.include_router(executive_board_router, prefix="/api")
app.include_router(business_operator_router, prefix="/api")
app.include_router(saas_builder_router, prefix="/api")
app.include_router(universal_operator_router, prefix="/api")
app.include_router(life_os_router, prefix="/api")
app.include_router(avatar_router, prefix="/api")
app.include_router(training_lab_router, prefix="/api")
app.include_router(departments_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(feature_router, prefix="/api")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
