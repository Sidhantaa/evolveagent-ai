from datetime import UTC, datetime
from uuid import uuid4

from app.agents.dynamic_agent_creator import DynamicAgentCreator
from app.agents.evolution_agent import EvolutionAgent
from app.agents.file_analysis_agent import FileAnalysisAgent
from app.agents.image_agent import ImageAgent
from app.agents.implementation_planner_agent import ImplementationPlannerAgent
from app.agents.judge_agent import JudgeAgent
from app.agents.goal_planner_agent import GoalPlannerAgent
from app.agents.logic_agent import LogicAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.prompt_injection_firewall_agent import PromptInjectionFirewallAgent
from app.agents.project_scanner_agent import ProjectScannerAgent
from app.agents.recording_analysis_agent import RecordingAnalysisAgent
from app.agents.research_agent import ResearchAgent
from app.agents.risk_agent import RiskAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.writing_agent import WritingAgent
from app.models.request_models import RunRequest
from app.models.response_models import (
    AgentOutput,
    AutomationPlan,
    GovernanceEvent,
    JudgeResult,
    MasterPlan,
    PromptInjectionResult,
    QualityGates,
    RunResponse,
    SecurityReport,
    WorkflowStep,
)
from app.config import settings
from app.services.file_service import CODE_EXTENSIONS, FileService
from app.services.custom_agent_service import CustomAgentService
from app.services.goal_service import GoalService
from app.services.governance_service import GovernanceService
from app.services.llm_router import llm_router
from app.services.permission_service import PermissionService
from app.services.recording_service import RecordingService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService
from app.services.assistant_command_service import AssistantCommandService
from app.services.knowledge_service import KnowledgeService
from app.services.tool_execution_service import ToolExecutionService
from app.services.tool_registry_service import ToolRegistryService
from app.services.tool_router_service import ToolRouterService
from app.services.workspace_service import WorkspaceService
from app.services.workflow_strategy_service import WorkflowStrategyService


class MasterOrchestratorAgent:
    def __init__(self, storage: StorageService, memory_agent: MemoryAgent):
        self.storage = storage
        self.memory_agent = memory_agent
        self.dynamic_creator = DynamicAgentCreator()
        self.image_agent = ImageAgent()
        self.goal_planner = GoalPlannerAgent()
        self.goal_service = GoalService(storage)
        self.custom_agents = CustomAgentService(storage)
        self.workspace = WorkspaceService(storage)
        self.file_service = FileService(storage)
        self.file_analysis = FileAnalysisAgent()
        self.recording_service = RecordingService(storage)
        self.recording_analysis = RecordingAnalysisAgent()
        self.project_scanner = ProjectScannerAgent()
        self.implementation_planner = ImplementationPlannerAgent()
        self.workflow_strategy = WorkflowStrategyService(storage)
        self.firewall = PromptInjectionFirewallAgent()
        self.secret_scanner = SecretScanner()
        self.permission_service = PermissionService()
        self.governance = GovernanceService(storage)
        self.knowledge_service = KnowledgeService(storage, self.workspace)
        self.assistant_commands = AssistantCommandService(self.workspace, self.knowledge_service)
        self.tool_registry = ToolRegistryService(storage, self.permission_service)
        self.tool_execution = ToolExecutionService(storage)
        self.tool_router = ToolRouterService(
            self.tool_registry,
            self.assistant_commands,
            self.permission_service,
            self.secret_scanner,
            self.tool_execution,
        )
        self.specialists = [ResearchAgent(), LogicAgent(), RiskAgent(), StrategyAgent()]
        self.writer = WritingAgent()
        self.judge = JudgeAgent()
        self.evolution = EvolutionAgent()

    def run(self, request: RunRequest) -> RunResponse:
        task_id = str(uuid4())
        session_id = request.session_id or str(uuid4())
        workspace_id = self.workspace.resolve_workspace_id(request.workspace_id)
        request = request.model_copy(update={"workspace_id": workspace_id})
        assistant_message_id = str(uuid4())
        created_at = datetime.now(UTC).isoformat()
        task_type, confidence = (
            self.detect_task_type_with_confidence(request.user_input)
            if request.task_type == "auto"
            else (request.task_type.lower(), 100)
        )
        quality_gates, security_report, governance_events, request = self.security_preflight(
            request, task_id, session_id, task_type
        )
        if security_report.blocked:
            return self.run_blocked_security_response(
                request,
                task_id,
                session_id,
                assistant_message_id,
                created_at,
                task_type,
                confidence,
                quality_gates,
                security_report,
                governance_events,
            )
        if task_type == "image_generation":
            return self.run_image_generation_workflow(
                request,
                task_id,
                session_id,
                assistant_message_id,
                created_at,
                confidence,
                quality_gates,
                security_report,
                governance_events,
            )
        if task_type == "app_automation":
            return self.run_app_automation_workflow(
                request,
                task_id,
                session_id,
                assistant_message_id,
                created_at,
                confidence,
                quality_gates,
                security_report,
                governance_events,
            )
        if task_type == "goal_planning":
            return self.run_goal_planning_workflow(
                request,
                task_id,
                session_id,
                assistant_message_id,
                created_at,
                confidence,
                quality_gates,
                security_report,
                governance_events,
            )
        if task_type == "recording_summary" and not request.recording_ids:
            return self.run_recording_summary_placeholder(
                request,
                task_id,
                session_id,
                assistant_message_id,
                created_at,
                confidence,
                quality_gates,
                security_report,
                governance_events,
            )

        file_context = ""
        files_used: list[dict] = []
        file_summary = None
        file_context_used = False
        recording_context = ""
        recordings_used: list[dict] = []
        recording_summary = None
        recording_context_used = False
        transcript_preview = None
        if request.recording_ids:
            recording_context, recordings_used = self.recording_service.build_context(request.recording_ids)
            recording_context_used = bool(recording_context and recordings_used)
            recording_context, recording_context_used, recording_events = self.secure_context(
                "recording_transcript",
                recording_context,
                task_id,
                session_id,
                task_type,
                quality_gates,
                security_report,
                workspace_id,
            )
            governance_events.extend(recording_events)
            if request.task_type == "auto" and recording_context_used:
                task_type, confidence = "recording_summary", 92
        if request.file_ids:
            file_context, files_used = self.file_service.build_context(request.file_ids)
            file_context_used = bool(file_context and files_used)
            file_context, file_context_used, file_events = self.secure_context(
                "file_context",
                file_context,
                task_id,
                session_id,
                task_type,
                quality_gates,
                security_report,
                workspace_id,
            )
            governance_events.extend(file_events)
            if request.task_type == "auto" and file_context_used:
                task_type, confidence = self.detect_file_task_type_with_confidence(request.user_input, files_used)

        suggested_agents = self.dynamic_creator.suggest(task_type)
        selected_agents = (
            (["Recording Analysis Agent"] if recording_context_used else [])
            + (["File Analysis Agent"] if file_context_used else [])
            + [agent.name for agent in self.specialists]
            + [self.writer.name]
        )
        execution_order = [
            "Detect task type",
            "Create master plan",
            *selected_agents[:-1],
            "Judge Agent",
            self.writer.name,
            "Judge Agent final review",
            "Evolution Agent",
            "Memory Agent",
        ]
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=selected_agents,
            suggested_future_agents=suggested_agents,
            execution_order=execution_order,
            selection_reason=self.selection_reason(task_type, confidence, suggested_agents),
            retry_policy="If final judge score is below 70, rerun Risk Agent and Writing Agent once before saving.",
        )
        workflow_trace: list[WorkflowStep] = [
            WorkflowStep(
                step=1,
                stage="Routing",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Detected task type '{task_type}' with {confidence}% confidence.",
            ),
            WorkflowStep(
                step=2,
                stage="Planning",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Selected {len(selected_agents)} active agents and suggested {len(suggested_agents)} future specialists.",
            ),
        ]

        agent_outputs: list[AgentOutput] = []
        conversation_context = self.get_recent_conversation_context(session_id)
        workspace_memory_context, workspace_memory_used = self.workspace.relevant_memory(
            workspace_id,
            request.user_input,
        )
        shared_context = f"Detected task type: {task_type}. Suggested future agents: {', '.join(suggested_agents)}."
        if workspace_memory_context:
            shared_context += f"\n\nRelevant workspace memory:\n{workspace_memory_context}"
        if conversation_context:
            shared_context += f"\n\nRecent conversation context:\n{conversation_context}"
        tool_trace = self.tool_router.route_and_run(request.user_input, workspace_id=workspace_id)
        if tool_trace:
            executed_tools = [item for item in tool_trace if item.get("executed")]
            blocked_tools = [item for item in tool_trace if item.get("blocked")]
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Tool routing",
                    agent_name="Tool Router Agent",
                    status="complete" if not blocked_tools else "warning",
                    summary=f"Selected {len(tool_trace)} tool(s); executed {len(executed_tools)} read-only tool(s).",
                )
            )
            tool_context = "\n".join(
                f"{item['tool_name']} ({item['permission_level']}): {item.get('result_summary', '')}"
                for item in executed_tools
                if item.get("result_summary")
            )
            if tool_context:
                shared_context += f"\n\nRead-only tool results:\n{tool_context}"
        if recording_context_used:
            recording_agent_output, recording_summary = self.recording_analysis.run(
                recordings_used, recording_context, request.user_input
            )
            agent_outputs.append(recording_agent_output)
            transcript_preview = self.summarize_step(recording_context)
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Recording analysis",
                    agent_name=recording_agent_output.agent_name,
                    status="complete",
                    summary=self.summarize_step(recording_agent_output.output),
                )
            )
            shared_context += (
                "\n\nUploaded recording transcript context was provided. Use it as primary evidence for the answer."
                f"\nRecording summary:\n{recording_summary.model_dump_json()}"
                f"\n\nTranscript context, capped at 20,000 characters:\n{recording_context}"
            )
        if file_context_used:
            file_agent_output, file_summary = self.file_analysis.run(files_used, file_context, request.user_input)
            agent_outputs.append(file_agent_output)
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="File analysis",
                    agent_name=file_agent_output.agent_name,
                    status="complete",
                    summary=self.summarize_step(file_agent_output.output),
                )
            )
            shared_context += (
                f"\n\nUploaded file context was provided. Use it as primary evidence for the answer."
                f"\nFile summary:\n{file_summary.model_dump_json()}"
                f"\n\nUploaded file extracted text, capped at 20,000 characters:\n{file_context}"
            )
        custom_agent_config = None
        if request.custom_agent_id:
            custom_agent_output, custom_agent_config = self.custom_agents.run(
                request.custom_agent_id,
                request.user_input,
                context=shared_context,
            )
            if custom_agent_output:
                agent_outputs.append(custom_agent_output)
                workflow_trace.append(
                    WorkflowStep(
                        step=len(workflow_trace) + 1,
                        stage="Custom agent execution",
                        agent_name=custom_agent_output.agent_name,
                        status="complete" if custom_agent_output.success else "blocked",
                        summary=self.summarize_step(custom_agent_output.output),
                    )
                )
                shared_context += f"\n\n{custom_agent_output.agent_name} output:\n{custom_agent_output.output}"
                governance_events.append(
                    self.log_governance_event(
                        task_id,
                        session_id,
                        task_type,
                        action_type="custom_agent_used",
                        tool_used="CustomAgentService",
                        permission_level=(custom_agent_config or {}).get("approval_level", "read_only"),
                        approved=False,
                        blocked=not custom_agent_output.success,
                        workspace_id=workspace_id,
                        risk_score=0 if custom_agent_output.success else 55,
                        reason=f"Custom agent {(custom_agent_config or {}).get('name', request.custom_agent_id)} participated in the workflow.",
                    )
                )
        for agent in self.specialists:
            agent_output = agent.run_with_metadata(request.user_input, context=shared_context)
            agent_outputs.append(agent_output)
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Specialist execution",
                    agent_name=agent.name,
                    status="complete",
                    summary=f"{agent_output.provider}/{agent_output.model}: {self.summarize_step(agent_output.output)}",
                )
            )
            shared_context += f"\n\n{agent.name} output:\n{agent_output.output}"

        preliminary_judge = self.judge.evaluate(agent_outputs)
        workflow_trace.append(
            WorkflowStep(
                step=len(workflow_trace) + 1,
                stage="Quality gate",
                agent_name=self.judge.name,
                status="complete",
                summary=f"Preliminary score was {preliminary_judge.overall_score}/100 before final writing.",
            )
        )
        if request.deep_mode:
            consensus_outputs = self.run_consensus_candidates(request.user_input, shared_context)
            consensus_winner, consensus_judge_reason, consensus_disagreement_notes = self.summarize_consensus(consensus_outputs)
            agent_outputs.extend(consensus_outputs)
            shared_context += "\n\nConsensus candidates:\n" + "\n\n".join(
                f"{item.agent_name} ({item.provider}/{item.model}):\n{item.output}" for item in consensus_outputs
            )
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Consensus mode",
                    agent_name="Master Orchestrator Agent",
                    status="complete",
                    summary=f"Deep Mode generated {len(consensus_outputs)} model candidates for comparison.",
                )
            )
        else:
            consensus_winner = None
            consensus_judge_reason = None
            consensus_disagreement_notes = []
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Consensus mode",
                    agent_name="Master Orchestrator Agent",
                    status="skipped",
                    summary="Deep Mode was off, so the workflow avoided extra model calls.",
                )
            )
        writing_output = self.writer.run_final_with_metadata(
            request.user_input,
            agent_outputs,
            judge_summary=preliminary_judge.model_dump_json(),
        )
        final_output = writing_output.output
        agent_outputs.append(writing_output)
        workflow_trace.append(
            WorkflowStep(
                step=len(workflow_trace) + 1,
                stage="Final synthesis",
                agent_name=self.writer.name,
                status="complete",
                summary=f"{writing_output.provider}/{writing_output.model}: {self.summarize_step(final_output)}",
            )
        )

        judge_result = self.judge.evaluate(agent_outputs, final_output=final_output, avoid_provider=writing_output.provider)
        workflow_trace.append(
            WorkflowStep(
                step=len(workflow_trace) + 1,
                stage="Final review",
                agent_name=self.judge.name,
                status="complete",
                summary=f"Final score is {judge_result.overall_score}/100. Recommendation: {judge_result.recommendation}",
            )
        )
        if judge_result.overall_score < 70:
            retry_output = self.risk_retry(
                request.user_input,
                shared_context,
                agent_outputs,
                judge_result.overall_score,
                writing_provider=writing_output.provider,
            )
            final_output = retry_output["final_output"]
            agent_outputs = retry_output["agent_outputs"]
            judge_result = retry_output["judge_result"]
            workflow_trace.extend(retry_output["workflow_trace"])
        else:
            workflow_trace.append(
                WorkflowStep(
                    step=len(workflow_trace) + 1,
                    stage="Retry decision",
                    agent_name="Master Orchestrator Agent",
                    status="skipped",
                    summary="Judge score met the quality threshold, so no retry was needed.",
                )
            )

        evolution_notes = self.evolution.recommend(task_type, agent_outputs, judge_result)
        workflow_trace.append(
            WorkflowStep(
                step=len(workflow_trace) + 1,
                stage="Evolution",
                agent_name=self.evolution.name,
                status="complete",
                summary=f"Generated {len(evolution_notes)} workflow improvement recommendations.",
            )
        )
        agents_used = [item.agent_name for item in agent_outputs]
        workflow_trace.append(
            WorkflowStep(
                step=len(workflow_trace) + 1,
                stage="Persistence",
                agent_name=self.memory_agent.name,
                status="complete",
                summary="Saved task result, memory summary, and evolution notes to JSON storage.",
            )
        )
        workflow_trace = [step.model_copy(update={"step": index}) for index, step in enumerate(workflow_trace, start=1)]

        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=workspace_id,
            task_type=task_type,
            agents_used=agents_used,
            suggested_agents=suggested_agents,
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=agent_outputs,
            consensus_candidates=consensus_outputs if request.deep_mode else [],
            consensus_winner=consensus_winner,
            consensus_judge_reason=consensus_judge_reason,
            consensus_disagreement_notes=consensus_disagreement_notes,
            judge_result=judge_result,
            evolution_notes=evolution_notes,
            memory_saved=True,
            memory_used=bool(workspace_memory_context),
            workspace_memory_used=workspace_memory_used,
            memory_context_characters=len(workspace_memory_context),
            file_context_used=file_context_used,
            files_used=files_used,
            file_summary=file_summary,
            file_context_characters=len(file_context),
            recording_context_used=recording_context_used,
            recordings_used=recordings_used,
            transcript_preview=transcript_preview,
            recording_summary=recording_summary,
            action_items=recording_summary.action_items if recording_summary else [],
            decisions=recording_summary.decisions if recording_summary else [],
            goal_id=request.goal_id,
            goal_task_id=request.task_id,
            custom_agent_used=bool(request.custom_agent_id and custom_agent_config),
            custom_agent=custom_agent_config,
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            tool_trace=tool_trace,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )

        self.storage.append("tasks.json", response.model_dump())
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": agents_used,
                "file_ids": request.file_ids,
                "filenames_used": [item.get("filename") for item in files_used],
                "file_context_used": file_context_used,
                "file_summary": file_summary.model_dump() if file_summary else None,
                "recording_ids": request.recording_ids,
                "recordings_used": [item.get("filename") for item in recordings_used],
                "recording_context_used": recording_context_used,
                "recording_summary": recording_summary.model_dump() if recording_summary else None,
                "goal_id": request.goal_id,
                "goal_task_id": request.task_id,
                "custom_agent_id": request.custom_agent_id,
                "workspace_id": workspace_id,
                "workspace_memory_used": [item.get("memory_id") for item in workspace_memory_used],
                "judge_score": judge_result.overall_score,
                "final_output_summary": final_output[:280],
                "created_at": created_at,
            }
        )
        self.storage.append(
            "evolution_logs.json",
            {
                "task_id": task_id,
                "workspace_id": workspace_id,
                "task_type": task_type,
                "recommendations": evolution_notes,
                "created_at": created_at,
            },
        )
        self.persist_agent_analytics(response)
        self.persist_chat_session(request, response)
        return response

    def security_preflight(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        task_type: str,
    ) -> tuple[QualityGates, SecurityReport, list[GovernanceEvent], RunRequest]:
        quality_gates = QualityGates()
        governance_events: list[GovernanceEvent] = []
        redacted_input, secret_result = self.secret_scanner.redact(request.user_input)
        prompt_result = self.firewall.scan(redacted_input)
        permission_level = self.permission_service.permission_for_action(
            "automation_plan" if task_type == "app_automation" else "file_analysis"
        )

        if secret_result.secrets_detected:
            quality_gates.secret_scan = "redacted"
            governance_events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="secret_redaction",
                    tool_used="SecretScanner",
                    permission_level="read_only",
                    workspace_id=request.workspace_id,
                    risk_score=15,
                    reason="Secret-like content was redacted from user input before agent execution.",
                )
            )

        if prompt_result.risk_level == "high":
            quality_gates.prompt_injection_check = "blocked"
            quality_gates.permission_check = "blocked"
            governance_events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="prompt_injection_warning",
                    tool_used="PromptInjectionFirewallAgent",
                    permission_level="blocked",
                    workspace_id=request.workspace_id,
                    blocked=True,
                    risk_score=prompt_result.risk_score,
                    reason=prompt_result.recommendation,
                )
            )
        elif prompt_result.risk_level == "medium":
            quality_gates.prompt_injection_check = "warning"
            governance_events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="prompt_injection_warning",
                    tool_used="PromptInjectionFirewallAgent",
                    permission_level=permission_level,
                    workspace_id=request.workspace_id,
                    risk_score=prompt_result.risk_score,
                    reason=prompt_result.recommendation,
                )
            )

        if task_type == "app_automation":
            quality_gates.permission_check = "approval_required"

        security_report = SecurityReport(
            prompt_injection=prompt_result,
            secret_scan=secret_result,
            permission_level="blocked" if prompt_result.risk_level == "high" else permission_level,
            risk_score=prompt_result.risk_score,
            risk_level=prompt_result.risk_level,
            recommendation=prompt_result.recommendation if prompt_result.risk_level != "low" else secret_result.recommendation,
            blocked=prompt_result.risk_level == "high",
        )
        if redacted_input != request.user_input:
            request = request.model_copy(update={"user_input": redacted_input})
        return quality_gates, security_report, governance_events, request

    def secure_context(
        self,
        context_type: str,
        context: str,
        task_id: str,
        session_id: str,
        task_type: str,
        quality_gates: QualityGates,
        security_report: SecurityReport,
        workspace_id: str | None = None,
    ) -> tuple[str, bool, list[GovernanceEvent]]:
        events: list[GovernanceEvent] = []
        if not context:
            return context, False, events

        redacted_context, secret_result = self.secret_scanner.redact(context)
        if secret_result.secrets_detected:
            quality_gates.secret_scan = "redacted"
            security_report.secret_scan = secret_result
            events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="secret_redaction",
                    tool_used="SecretScanner",
                    permission_level="read_only",
                    workspace_id=workspace_id,
                    files_accessed=[context_type],
                    risk_score=20,
                    reason=f"Secret-like content was redacted from {context_type}.",
                )
            )

        injection = self.firewall.scan(redacted_context)
        if injection.risk_score > security_report.risk_score:
            security_report.prompt_injection = injection
            security_report.risk_score = injection.risk_score
            security_report.risk_level = injection.risk_level
            security_report.recommendation = injection.recommendation
        if context_type == "file_context":
            quality_gates.file_context_check = "passed"

        if injection.risk_level == "high":
            if context_type == "file_context":
                quality_gates.file_context_check = "warning"
            quality_gates.prompt_injection_check = "warning"
            events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="prompt_injection_warning",
                    tool_used="PromptInjectionFirewallAgent",
                    files_accessed=[context_type],
                    permission_level="read_only",
                    workspace_id=workspace_id,
                    blocked=True,
                    risk_score=injection.risk_score,
                    reason=f"High-risk instructions were found in {context_type}; the context was isolated from LLM use.",
                )
            )
            return "", False, events

        if injection.risk_level == "medium":
            quality_gates.prompt_injection_check = "warning"
            if context_type == "file_context":
                quality_gates.file_context_check = "warning"
            events.append(
                self.log_governance_event(
                    task_id,
                    session_id,
                    task_type,
                    action_type="prompt_injection_warning",
                    tool_used="PromptInjectionFirewallAgent",
                    files_accessed=[context_type],
                    permission_level="read_only",
                    workspace_id=workspace_id,
                    risk_score=injection.risk_score,
                    reason=f"Suspicious embedded instructions were found in {context_type}.",
                )
            )
        return redacted_context, True, events

    def log_governance_event(self, run_id: str, session_id: str, task_type: str, **kwargs) -> GovernanceEvent:
        kwargs.setdefault("workspace_id", self.workspace.default_workspace_id())
        event = GovernanceEvent(run_id=run_id, session_id=session_id, task_type=task_type, **kwargs)
        return self.governance.log_event(event)

    def run_blocked_security_response(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        assistant_message_id: str,
        created_at: str,
        task_type: str,
        confidence: int,
        quality_gates: QualityGates,
        security_report: SecurityReport,
        governance_events: list[GovernanceEvent],
    ) -> RunResponse:
        final_output = (
            "This request was blocked because it may expose secrets, override safety rules, or perform unsafe actions."
        )
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=["Prompt Injection Firewall Agent", "Secret Scanner", "Permission Service"],
            suggested_future_agents=[],
            execution_order=["Security preflight", "Permission check", "Blocked response"],
            selection_reason="The security layer blocked this request before specialist agents ran.",
            retry_policy="Ask the user to remove secret-exposure or safety-override instructions and submit a safe request.",
        )
        workflow_trace = [
            WorkflowStep(
                step=1,
                stage="Security preflight",
                agent_name="Prompt Injection Firewall Agent",
                status="blocked",
                summary=security_report.recommendation,
            )
        ]
        judge_result = JudgeResult(
            overall_score=70,
            strengths=["Unsafe execution was blocked before model/tool use."],
            weaknesses=["The original request could not be completed safely."],
            recommendation="Revise the request without secret-exposure, deletion, or safety-override instructions.",
            classification_correct=True,
            capability_supported=False,
            reason="Security governance blocked the request.",
        )
        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            agents_used=["Prompt Injection Firewall Agent", "Secret Scanner", "Permission Service"],
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=[],
            judge_result=judge_result,
            evolution_notes=["Keep blocked security requests out of model and tool execution paths."],
            memory_saved=True,
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )
        self.storage.append("tasks.json", response.model_dump())
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "workspace_id": request.workspace_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": response.agents_used,
                "workspace_id": request.workspace_id,
                "judge_score": judge_result.overall_score,
                "final_output_summary": final_output,
                "created_at": created_at,
            }
        )
        self.persist_chat_session(request, response)
        return response

    @staticmethod
    def detect_task_type(user_input: str) -> str:
        return MasterOrchestratorAgent.detect_task_type_with_confidence(user_input)[0]

    @staticmethod
    def detect_task_type_with_confidence(user_input: str) -> tuple[str, int]:
        text = user_input.lower()
        image_edit_verbs = (
            "add ",
            "put ",
            "place ",
            "insert ",
            "include ",
            "remove ",
            "change ",
            "replace ",
            "edit ",
        )
        visual_subject_terms = (
            "image",
            "photo",
            "picture",
            "drawing",
            "illustration",
            "logo",
            "poster",
            "flower",
            "sunflower",
            "sun flower",
            "butterfly",
            "car",
            "background",
            "sky",
            "tree",
            "portrait",
            "character",
        )
        if any(text.startswith(verb) for verb in image_edit_verbs) and any(term in text for term in visual_subject_terms):
            return "image_generation", 88

        keyword_map = {
            "image_generation": [
                "create image",
                "create photo",
                "generate image",
                "generate photo",
                "make image",
                "make photo",
                "image ",
                "photo ",
                "photo of",
                "image of",
                "picture",
                "poster",
                "logo",
                "visual",
                "illustration",
                "render",
                "design image",
                "draw",
            ],
            "app_automation": [
                "add a page",
                "add a settings page",
                "settings page",
                "create a component",
                "add a component",
                "update this app",
                "fix this bug",
                "run the app",
                "run tests",
                "change the ui",
                "implement this feature",
                "edit files",
                "add dark mode",
                "add login page",
                "modify this project",
                "make this change in the codebase",
                "change in the codebase",
                "apply this change",
            ],
            "recording_summary": [
                "summarize this recording",
                "summarize audio",
                "meeting recording",
                "lecture recording",
                "transcribe this",
                "voice note summary",
            ],
            "goal_planning": [
                "build me an app",
                "create a project plan",
                "make a roadmap",
                "plan this project",
                "break this goal into tasks",
                "help me finish this by tomorrow",
                "create a full implementation plan",
                "build an ai resume analyzer",
                "create a saas app plan",
                "make me a task graph",
            ],
            "system_explanation": [
                "evolveagent ai",
                "multi-agent workflow",
                "multi-llm workflow",
                "architecture",
                "agents",
                "how the system works",
                "what the model is doing",
                "what our model is doing",
            ],
            "resume": ["resume", "internship", "job", "cover letter"],
            "coding": ["coding", "code", "bug", "api", "backend", "frontend", "python", "react"],
            "business": ["business", "startup", "market", "customer", "revenue"],
            "finance": ["stock", "price", "trading", "portfolio", "investment"],
            "pharmacy": ["icd", "prior authorization", "medication", "pharmacy", "diagnosis"],
            "research": ["research", "paper", "study", "sources", "evidence"],
        }
        best_type = "general"
        best_matches = 0
        for task_type, keywords in keyword_map.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > best_matches:
                best_type = task_type
                best_matches = matches
        if best_matches == 0:
            return "general", 62
        if best_type == "image_generation":
            return best_type, min(96, 85 + best_matches * 4)
        if best_type == "app_automation":
            return best_type, min(96, 86 + best_matches * 4)
        if best_type == "recording_summary":
            return best_type, min(94, 84 + best_matches * 4)
        if best_type == "goal_planning":
            return best_type, min(96, 86 + best_matches * 4)
        if best_type == "system_explanation":
            return best_type, min(98, 84 + best_matches * 4)
        return best_type, min(95, 72 + best_matches * 8)

    @staticmethod
    def detect_file_task_type_with_confidence(user_input: str, files_used: list[dict]) -> tuple[str, int]:
        text = user_input.lower()
        extensions = {item.get("extension", "").lower() for item in files_used}
        filenames = " ".join(item.get("filename", "").lower() for item in files_used)
        if any(word in text for word in ("resume", "cv", "internship", "job")) or "resume" in filenames:
            return "resume_review", 92
        if extensions & CODE_EXTENSIONS or any(word in text for word in ("code", "bug", "explain code", "review code")):
            return "code_review", 91
        if ".csv" in extensions or any(word in text for word in ("data", "rows", "columns", "analyze", "patterns")):
            return "data_analysis", 90
        if any(word in text for word in ("summarize", "summary", "notes", "key points", "study notes")):
            return "file_summary", 90
        return "document_analysis", 86

    @staticmethod
    def selection_reason(task_type: str, confidence: int, suggested_agents: list[str]) -> str:
        if task_type == "general":
            return (
                "The Master Agent selected the core research, logic, risk, strategy, and writing agents because "
                "the task did not strongly match a specialized category."
            )
        return (
            f"The Master Agent routed this as a {task_type} task with {confidence}% confidence, used the core "
            f"specialist workflow, and suggested future specialists: {', '.join(suggested_agents)}."
        )

    @staticmethod
    def summarize_step(output: str) -> str:
        compact = " ".join(output.split())
        return compact[:180] + ("..." if len(compact) > 180 else "")

    def run_image_generation_workflow(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        assistant_message_id: str,
        created_at: str,
        confidence: int,
        quality_gates: QualityGates | None = None,
        security_report: SecurityReport | None = None,
        governance_events: list[GovernanceEvent] | None = None,
    ) -> RunResponse:
        quality_gates = quality_gates or QualityGates()
        security_report = security_report or SecurityReport()
        governance_events = governance_events or []
        task_type = "image_generation"
        suggested_agents = self.dynamic_creator.suggest(task_type)
        image_agent_output, image_result = self.image_agent.run(request.user_input)
        agents_used = ["Image Agent", "Image Prompt Builder", "Image Safety Checker"]
        final_output = (
            "I generated an image using a safe image prompt."
            if image_result.provider != "mock_image"
            else "Real image generation failed, so I used the mock preview fallback."
            if image_result.fallback_used
            else "I created an image preview using a safe image prompt."
        )
        workflow_trace = [
            WorkflowStep(
                step=1,
                stage="Task received",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary="Received a visual/image creation request from the user.",
            ),
            WorkflowStep(
                step=2,
                stage="Classification",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Classified request as image_generation with {confidence}% confidence.",
            ),
            WorkflowStep(
                step=3,
                stage="Image Agent started",
                agent_name="Image Agent",
                status="complete",
                summary="Routed the visual request to the dedicated image workflow instead of text specialist agents.",
            ),
            WorkflowStep(
                step=4,
                stage="Prompt generated",
                agent_name="Image Prompt Builder",
                status="complete",
                summary=f"Created image prompt: {self.summarize_step(image_result.prompt)}",
            ),
            WorkflowStep(
                step=5,
                stage="Safety check completed",
                agent_name="Image Safety Checker",
                status="complete",
                summary=(
                    "Rewrote protected character wording into an inspired original prompt."
                    if image_result.safety_rewritten
                    else "No protected character rewrite was needed."
                ),
            ),
            WorkflowStep(
                step=6,
                stage="Image generated",
                agent_name="Image Agent",
                status="complete",
                summary=f"{image_result.provider}/{image_result.model}: generated preview at {image_result.image_url}.",
            ),
            WorkflowStep(
                step=7,
                stage="Persistence",
                agent_name=self.memory_agent.name,
                status="complete",
                summary="Saved image-generation metadata to JSON memory.",
            ),
        ]
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=agents_used,
            suggested_future_agents=suggested_agents,
            execution_order=[
                "Receive task",
                "Classify as image_generation",
                "Image Agent",
                "Image Prompt Builder",
                "Image Safety Checker",
                "Image Provider",
                "Memory Agent",
            ],
            selection_reason=(
                "The Master Agent detected an image creation request and used the dedicated image workflow "
                "instead of the normal text-analysis workflow."
            ),
            retry_policy="Regenerate the safe prompt and image preview if the user requests another version.",
        )
        judge_result = self.judge.evaluate([image_agent_output], final_output=final_output).model_copy(
            update={
                "recommendation": (
                    "Request was correctly classified as image_generation and routed to the Image Agent. "
                    "The system generated a safe prompt, created a preview, and saved the task metadata."
                ),
                "classification_correct": True,
                "capability_supported": True,
                "reason": f"Image generation completed with provider '{image_result.provider}'.",
            }
        )
        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            agents_used=agents_used,
            suggested_agents=suggested_agents,
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=[image_agent_output],
            consensus_candidates=[],
            judge_result=judge_result,
            evolution_notes=[
                "Keep mock_image as a fallback when real image providers fail."
            ],
            memory_saved=True,
            image_result=image_result,
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )
        self.storage.append("tasks.json", response.model_dump())
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": agents_used,
                "workspace_id": request.workspace_id,
                "judge_score": judge_result.overall_score,
                "final_safe_prompt": image_result.prompt,
                "image_provider": image_result.provider,
                "image_url": image_result.image_url,
                "safety_rewritten": image_result.safety_rewritten,
                "final_output_summary": final_output[:280],
                "created_at": created_at,
            }
        )
        self.storage.append(
            "evolution_logs.json",
            {
                "task_id": task_id,
                "workspace_id": request.workspace_id,
                "task_type": task_type,
                "recommendations": response.evolution_notes,
                "created_at": created_at,
            },
        )
        self.persist_agent_analytics(response)
        self.persist_chat_session(request, response)
        return response

    def run_goal_planning_workflow(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        assistant_message_id: str,
        created_at: str,
        confidence: int,
        quality_gates: QualityGates | None = None,
        security_report: SecurityReport | None = None,
        governance_events: list[GovernanceEvent] | None = None,
    ) -> RunResponse:
        quality_gates = quality_gates or QualityGates()
        security_report = security_report or SecurityReport()
        governance_events = governance_events or []
        task_type = "goal_planning"
        goal_output, planner_result = self.goal_planner.run(request.user_input)
        goal, task_graph = self.goal_service.create_from_plan(
            planner_result,
            source_session_id=session_id,
            source_message_id=assistant_message_id,
            workspace_id=request.workspace_id,
        )
        governance_events.append(
            self.log_governance_event(
                task_id,
                session_id,
                task_type,
                action_type="goal_created",
                tool_used="GoalPlannerAgent",
                permission_level="plan_only",
                approved=False,
                blocked=False,
                workspace_id=request.workspace_id,
                risk_score=security_report.risk_score,
                reason=f"Created Mission Control goal {goal.goal_id} with {len(task_graph.tasks)} task(s).",
            )
        )
        agents_used = ["Goal Planner Agent", "Judge Agent", "Memory Agent"]
        suggested_agents = planner_result.get("recommended_agents", [])
        task_lines = "\n".join(
            f"- [{task.status}] {task.phase}: {task.title} ({task.priority})"
            for task in task_graph.tasks
        )
        final_output = (
            f"## Mission Plan: {goal.title}\n\n"
            f"{goal.description}\n\n"
            f"### Tasks\n{task_lines}\n\n"
            f"**Next best task:** {goal.next_best_task or 'Review the mission plan.'}"
        )
        workflow_trace = [
            WorkflowStep(
                step=1,
                stage="Task received",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary="Received a large-goal planning request.",
            ),
            WorkflowStep(
                step=2,
                stage="Classification",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Classified request as goal_planning with {confidence}% confidence.",
            ),
            WorkflowStep(
                step=3,
                stage="Goal planning",
                agent_name="Goal Planner Agent",
                status="complete",
                summary=goal.description,
            ),
            WorkflowStep(
                step=4,
                stage="Mission Control persistence",
                agent_name="Goal Service",
                status="complete",
                summary=f"Saved goal and task graph with {len(task_graph.tasks)} task(s).",
            ),
            WorkflowStep(
                step=5,
                stage="Persistence",
                agent_name=self.memory_agent.name,
                status="complete",
                summary="Saved goal-planning run to task history and memory.",
            ),
        ]
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=agents_used,
            suggested_future_agents=suggested_agents,
            execution_order=[
                "Classify goal request",
                "Goal Planner Agent",
                "Goal Service",
                "Judge Agent",
                "Memory Agent",
            ],
            selection_reason="The request asks for a roadmap or task graph, so the Master Agent created a Mission Control plan.",
            retry_policy="If the plan is too broad, ask the user to narrow the goal and regenerate the task graph.",
        )
        judge_result = self.judge.evaluate([goal_output], final_output=final_output).model_copy(
            update={
                "recommendation": "Mission plan is ready for review in Mission Control.",
                "classification_correct": True,
                "capability_supported": True,
                "reason": "Goal Mode creates a task graph only; it does not execute code changes automatically.",
            }
        )
        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            agents_used=agents_used,
            suggested_agents=suggested_agents,
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=[goal_output],
            consensus_candidates=[],
            judge_result=judge_result,
            evolution_notes=[
                "Use Mission Control to run goal tasks one at a time.",
                "Tasks that edit files or run commands still require approval.",
            ],
            memory_saved=True,
            goal_created=True,
            goal=goal,
            task_graph=task_graph,
            goal_id=goal.goal_id,
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )
        self.storage.append("tasks.json", response.model_dump())
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": agents_used,
                "workspace_id": request.workspace_id,
                "goal_id": goal.goal_id,
                "goal_title": goal.title,
                "task_count": len(task_graph.tasks),
                "judge_score": judge_result.overall_score,
                "final_output_summary": final_output[:280],
                "created_at": created_at,
            }
        )
        self.storage.append(
            "evolution_logs.json",
            {
                "task_id": task_id,
                "workspace_id": request.workspace_id,
                "task_type": task_type,
                "recommendations": response.evolution_notes,
                "created_at": created_at,
            },
        )
        self.persist_agent_analytics(response)
        self.persist_chat_session(request, response)
        return response

    def run_app_automation_workflow(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        assistant_message_id: str,
        created_at: str,
        confidence: int,
        quality_gates: QualityGates | None = None,
        security_report: SecurityReport | None = None,
        governance_events: list[GovernanceEvent] | None = None,
    ) -> RunResponse:
        quality_gates = quality_gates or QualityGates(permission_check="approval_required")
        quality_gates.permission_check = "approval_required"
        security_report = security_report or SecurityReport(permission_level="plan_only")
        security_report.permission_level = "plan_only"
        governance_events = governance_events or []
        task_type = "app_automation"
        governance_events.append(
            self.log_governance_event(
                task_id,
                session_id,
                task_type,
                action_type="automation_plan",
                tool_used="ImplementationPlannerAgent",
                permission_level="plan_only",
                approved=False,
                blocked=False,
                workspace_id=request.workspace_id,
                risk_score=security_report.risk_score,
                reason="Automation request produced an approval-gated plan. No files were changed.",
            )
        )
        project_scan = self.project_scanner.scan(request.user_input)
        automation_plan = self.implementation_planner.plan(request.user_input, project_scan)
        agents_used = ["Project Scanner Agent", "Implementation Planner Agent", "Judge Agent"]
        suggested_agents = ["Patch Suggestion Agent", "Test Runner Agent", "Permission Agent"]
        final_output = (
            "I prepared a safe implementation plan. Review the files, commands, and risk level, then approve or reject it. "
            "No files have been changed."
        )
        agent_outputs = [
            AgentOutput(
                agent_name="Project Scanner Agent",
                provider="rule-based",
                model="project-scanner-v2",
                fallback_used=False,
                output=project_scan.model_dump_json(),
            ),
            AgentOutput(
                agent_name="Implementation Planner Agent",
                provider="rule-based",
                model="implementation-planner-v2",
                fallback_used=False,
                output=automation_plan.model_dump_json(),
            ),
        ]
        judge_result = self.judge.evaluate(agent_outputs, final_output=final_output).model_copy(
            update={
                "recommendation": "Automation plan is ready for human approval. Do not apply changes until approved.",
                "classification_correct": True,
                "capability_supported": True,
                "reason": "v2.0 supports safe planning and approval-gated automation.",
            }
        )
        workflow_trace = [
            WorkflowStep(
                step=1,
                stage="Task received",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary="Received an app/code automation request.",
            ),
            WorkflowStep(
                step=2,
                stage="Classification",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Classified request as app_automation with {confidence}% confidence.",
            ),
            WorkflowStep(
                step=3,
                stage="Project scan",
                agent_name="Project Scanner Agent",
                status="complete",
                summary=project_scan.scan_summary,
            ),
            WorkflowStep(
                step=4,
                stage="Implementation plan",
                agent_name="Implementation Planner Agent",
                status="complete",
                summary=automation_plan.summary,
            ),
            WorkflowStep(
                step=5,
                stage="Approval gate",
                agent_name="Safety Permission Agent",
                status="waiting_for_approval",
                summary="File edits and commands are blocked until the user approves the plan.",
            ),
        ]
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=agents_used,
            suggested_future_agents=suggested_agents,
            execution_order=[
                "Classify automation request",
                "Project Scanner Agent",
                "Implementation Planner Agent",
                "Judge Agent",
                "Approval Gate",
            ],
            selection_reason="The request asks to modify or run the codebase, so the Master Agent routed it through safe automation planning.",
            retry_policy="If the user rejects the plan, revise the plan instead of changing files.",
        )
        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            agents_used=agents_used,
            suggested_agents=suggested_agents,
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=agent_outputs,
            consensus_candidates=[],
            judge_result=judge_result,
            evolution_notes=[
                "For app automation tasks, require approval before file edits.",
                "Use a patch preview step before enabling automatic writes.",
            ],
            memory_saved=True,
            requires_approval=True,
            automation_plan=automation_plan,
            automation_status="pending_approval",
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )
        self.storage.append("tasks.json", response.model_dump())
        self.storage.append(
            "automation_runs.json",
            {
                "run_id": task_id,
                "session_id": session_id,
                "workspace_id": request.workspace_id,
                "status": "pending_approval",
                "automation_plan": automation_plan.model_dump(),
                "created_at": created_at,
            },
        )
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": agents_used,
                "workspace_id": request.workspace_id,
                "judge_score": judge_result.overall_score,
                "final_output_summary": final_output[:280],
                "created_at": created_at,
            }
        )
        self.storage.append(
            "evolution_logs.json",
            {
                "task_id": task_id,
                "workspace_id": request.workspace_id,
                "task_type": task_type,
                "recommendations": response.evolution_notes,
                "created_at": created_at,
            },
        )
        self.persist_agent_analytics(response)
        self.persist_chat_session(request, response)
        return response

    def run_recording_summary_placeholder(
        self,
        request: RunRequest,
        task_id: str,
        session_id: str,
        assistant_message_id: str,
        created_at: str,
        confidence: int,
        quality_gates: QualityGates | None = None,
        security_report: SecurityReport | None = None,
        governance_events: list[GovernanceEvent] | None = None,
    ) -> RunResponse:
        quality_gates = quality_gates or QualityGates()
        security_report = security_report or SecurityReport()
        governance_events = governance_events or []
        task_type = "recording_summary"
        final_output = (
            "Recording summary is planned for v2.1. Current v2.0 supports browser voice command transcription "
            "for short commands, but full audio upload/transcription is not enabled yet."
        )
        agents_used = ["Master Orchestrator Agent", "Memory Agent"]
        workflow_trace = [
            WorkflowStep(
                step=1,
                stage="Task received",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary="Received a recording/audio summary request.",
            ),
            WorkflowStep(
                step=2,
                stage="Classification",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Classified request as recording_summary with {confidence}% confidence.",
            ),
            WorkflowStep(
                step=3,
                stage="Capability check",
                agent_name="Master Orchestrator Agent",
                status="skipped",
                summary="Full audio transcription is deferred to v2.1; no paid transcription API was called.",
            ),
            WorkflowStep(
                step=4,
                stage="Persistence",
                agent_name=self.memory_agent.name,
                status="complete",
                summary="Saved recording-summary placeholder metadata.",
            ),
        ]
        master_plan = MasterPlan(
            detected_task_type=task_type,
            confidence=confidence,
            selected_agents=agents_used,
            suggested_future_agents=["Audio Transcription Agent", "Meeting Notes Agent"],
            execution_order=["Classify recording task", "Capability check", "Memory Agent"],
            selection_reason="The request is about audio/recording summarization, which is planned for the next version.",
            retry_policy="Ask the user to use short browser voice commands in v2.0 or wait for v2.1 audio upload support.",
        )
        judge_result = JudgeResult(
            overall_score=75,
            strengths=["Correctly classified recording-summary intent", "Avoided unsupported paid transcription path"],
            weaknesses=["Full recording upload and transcription are not implemented in v2.0"],
            recommendation="Use browser voice command input for short commands; add full audio transcription in v2.1.",
            classification_correct=True,
            capability_supported=False,
            reason="Recording upload/transcription is not integrated in the current MVP.",
        )
        response = RunResponse(
            task_id=task_id,
            run_id=task_id,
            session_id=session_id,
            message_id=assistant_message_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            agents_used=agents_used,
            suggested_agents=["Audio Transcription Agent", "Meeting Notes Agent"],
            master_plan=master_plan,
            workflow_trace=workflow_trace,
            agent_outputs=[],
            consensus_candidates=[],
            judge_result=judge_result,
            evolution_notes=["Add audio upload and transcription in v2.1 with clear file-size limits."],
            memory_saved=True,
            quality_gates=quality_gates,
            security_report=security_report,
            governance_events=governance_events,
            voice_used=request.voice_used,
            voice_transcript=request.voice_transcript,
            final_output=final_output,
            created_at=created_at,
        )
        self.storage.append("tasks.json", response.model_dump())
        self.memory_agent.remember(
            {
                "task_id": task_id,
                "task_type": task_type,
                "user_input": request.user_input,
                "agents_used": agents_used,
                "workspace_id": request.workspace_id,
                "judge_score": judge_result.overall_score,
                "final_output_summary": final_output[:280],
                "created_at": created_at,
            }
        )
        self.persist_agent_analytics(response)
        self.persist_chat_session(request, response)
        return response

    def persist_agent_analytics(self, response: RunResponse) -> None:
        outputs = response.agent_outputs + response.consensus_candidates
        total_latency = sum(item.latency_ms for item in outputs) + response.judge_result.latency_ms
        fallback_used = any(item.fallback_used for item in outputs) or response.judge_result.fallback_used
        provider_models = [
            {
                "agent_name": item.agent_name,
                "provider": item.provider,
                "model": item.model,
                "latency_ms": item.latency_ms,
                "fallback_used": item.fallback_used,
            }
            for item in outputs
        ]
        if response.image_result:
            provider_models.append(
                {
                    "agent_name": "Image Provider",
                    "provider": response.image_result.provider,
                    "model": response.image_result.model,
                    "latency_ms": 0,
                    "fallback_used": response.image_result.fallback_used,
                }
            )
            fallback_used = fallback_used or response.image_result.fallback_used
        self.storage.append(
            "agent_analytics.json",
            {
                "run_id": response.run_id,
                "session_id": response.session_id,
                "workspace_id": response.workspace_id,
                "task_type": response.task_type,
                "agents_used": response.agents_used,
                "per_agent_scores": [item.model_dump() for item in response.judge_result.per_agent_scores],
                "overall_judge_score": response.judge_result.overall_score,
                "provider_models": provider_models,
                "fallback_used": fallback_used,
                "latency_ms": total_latency,
                "file_context_used": response.file_context_used,
                "recording_context_used": response.recording_context_used,
                "recording_task": response.recording_context_used,
                "image_task": response.image_result is not None,
                "goal_id": response.goal_id,
                "goal_task_id": response.goal_task_id,
                "goal_created": response.goal_created,
                "custom_agent_used": response.custom_agent_used,
                "custom_agent_id": response.custom_agent.agent_id if response.custom_agent else None,
                "custom_agent_name": response.custom_agent.name if response.custom_agent else None,
                "created_at": response.created_at,
            },
        )
        self.workflow_strategy.update_from_run(response)
        self.persist_model_tournament(response)

    def persist_model_tournament(self, response: RunResponse) -> None:
        if not response.consensus_candidates:
            return
        records = self.storage.read_list("model_performance.json")
        for candidate in response.consensus_candidates:
            records.append(
                {
                    "record_type": "consensus_candidate",
                    "run_id": response.run_id,
                    "session_id": response.session_id,
                    "workspace_id": response.workspace_id,
                    "task_type": response.task_type,
                    "provider": candidate.provider,
                    "model": candidate.model,
                    "judge_score": response.judge_result.overall_score,
                    "latency_ms": candidate.latency_ms,
                    "fallback_used": candidate.fallback_used,
                    "selected_as_winner": candidate.agent_name == response.consensus_winner,
                    "user_feedback": None,
                    "created_at": response.created_at,
                }
            )
        self.storage.write_list("model_performance.json", records)

    def persist_chat_session(self, request: RunRequest, response: RunResponse) -> None:
        sessions = self.storage.read_list("chat_sessions.json")
        messages = self.storage.read_list("messages.json")
        now = response.created_at
        session = next((item for item in sessions if item.get("session_id") == response.session_id), None)
        if session is None:
            session = {
                "session_id": response.session_id,
                "workspace_id": response.workspace_id,
                "title": self.derive_chat_title(request.user_input),
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }
            sessions.append(session)
        session["workspace_id"] = session.get("workspace_id") or response.workspace_id
        session["updated_at"] = now
        attached_files = [item.model_dump() if hasattr(item, "model_dump") else item for item in response.files_used]
        attached_recordings = [item.model_dump() if hasattr(item, "model_dump") else item for item in response.recordings_used]
        user_message = {
            "message_id": str(uuid4()),
            "id": str(uuid4()),
            "session_id": response.session_id,
            "workspace_id": response.workspace_id,
            "role": "user",
            "content": request.user_input,
            "file_ids": request.file_ids,
            "recording_ids": request.recording_ids,
            "attached_files": attached_files,
            "attached_recordings": attached_recordings,
            "voice_used": request.voice_used,
            "voice_transcript": request.voice_transcript,
            "goal_id": request.goal_id,
            "goal_task_id": request.task_id,
            "custom_agent_id": request.custom_agent_id,
            "created_at": now,
        }
        assistant_message = {
            "message_id": response.message_id,
            "id": response.message_id,
            "session_id": response.session_id,
            "workspace_id": response.workspace_id,
            "role": "assistant",
            "content": response.final_output,
            "created_at": now,
            "run_id": response.run_id,
            "task_id": response.task_id,
            "result": response.model_dump(),
        }
        session.setdefault("messages", []).extend(
            [
                user_message,
                assistant_message,
            ]
        )
        messages.extend([user_message, assistant_message])
        self.storage.write_list("chat_sessions.json", sessions)
        self.storage.write_list("messages.json", messages)
        self.persist_workspace_memory(request, response)

    def persist_workspace_memory(self, request: RunRequest, response: RunResponse) -> None:
        if not response.workspace_id or not response.memory_saved:
            return
        self.workspace.create_memory(
            response.workspace_id,
            {
                "type": "task_result",
                "title": self.derive_chat_title(request.user_input),
                "content": response.final_output[:1200],
                "source": "chat",
                "importance": "high" if response.judge_result.overall_score >= 85 else "medium",
                "tags": [response.task_type],
            },
        )

    def get_recent_conversation_context(self, session_id: str, limit: int = 8) -> str:
        messages = [
            item
            for item in self.storage.read_list("messages.json")
            if item.get("session_id") == session_id and item.get("role") in {"user", "assistant"}
        ]
        if not messages:
            session = next((item for item in self.storage.read_list("chat_sessions.json") if item.get("session_id") == session_id), None)
            messages = (session or {}).get("messages", [])
        recent = messages[-limit:]
        return "\n".join(f"{item.get('role', 'message')}: {item.get('content', '')}" for item in recent if item.get("content"))

    @staticmethod
    def derive_chat_title(user_input: str) -> str:
        compact = " ".join(user_input.split())
        if len(compact) <= 44:
            return compact
        return compact[:41].rstrip() + "..."

    @staticmethod
    def run_consensus_candidates(user_input: str, shared_context: str) -> list[AgentOutput]:
        system_prompt = (
            "You are a consensus candidate model. Answer the task independently, focusing on completeness, "
            "clear reasoning, safety, and useful next steps. Do not judge other models."
        )
        user_prompt = f"User task:\n{user_input}\n\nShared context:\n{shared_context}"
        candidates = llm_router.consensus_routes()
        outputs: list[AgentOutput] = []
        for route in candidates:
            result = llm_router.generate_for_provider(route.provider, route.model, system_prompt, user_prompt)
            label = route.label or llm_router.provider_label(route.provider)
            outputs.append(
                AgentOutput(
                    agent_name=f"{label} Consensus Candidate",
                    provider=result.provider,
                    model=result.model,
                    latency_ms=result.latency_ms,
                    success=result.success,
                    fallback_used=result.fallback_used,
                    error=result.error,
                    output=result.output,
                )
            )
        return outputs

    @staticmethod
    def summarize_consensus(candidates: list[AgentOutput]) -> tuple[str | None, str | None, list[str]]:
        if not candidates:
            return None, None, []
        winner = next((candidate for candidate in candidates if candidate.success and not candidate.fallback_used), candidates[0])
        fallback_count = sum(1 for candidate in candidates if candidate.fallback_used)
        providers = ", ".join(dict.fromkeys(candidate.provider for candidate in candidates))
        reason = (
            f"Selected {winner.agent_name} because it completed successfully through {winner.provider}/{winner.model}. "
            f"The Judge Agent used the candidates as comparison material during final synthesis."
        )
        notes = [
            f"Consensus compared {len(candidates)} candidate outputs across: {providers}.",
            f"{fallback_count} candidate route(s) used fallback." if fallback_count else "No consensus candidate used fallback.",
        ]
        return winner.agent_name, reason, notes

    def risk_retry(
        self,
        user_input: str,
        shared_context: str,
        agent_outputs: list[AgentOutput],
        previous_score: int,
        writing_provider: str,
    ) -> dict:
        retry_trace: list[WorkflowStep] = [
            WorkflowStep(
                step=0,
                stage="Retry decision",
                agent_name="Master Orchestrator Agent",
                status="complete",
                summary=f"Judge score {previous_score}/100 was below threshold, so Risk Agent and Writing Agent were rerun.",
            )
        ]
        risk_retry = self.specialists[2].run_with_metadata(
            user_input,
            context=f"{shared_context}\n\nRetry focus: be more specific and actionable.",
        )
        risk_retry.agent_name = "Risk Agent Retry"
        agent_outputs.append(risk_retry)
        retry_trace.append(
            WorkflowStep(
                step=0,
                stage="Retry execution",
                agent_name="Risk Agent",
                status="complete",
                summary=f"{risk_retry.provider}/{risk_retry.model}: {self.summarize_step(risk_retry.output)}",
            )
        )
        writing_retry = self.writer.run_final_with_metadata(
            user_input,
            agent_outputs,
            judge_summary=f"Previous score was {previous_score}. Improve risk handling and final readiness.",
            avoid_provider=writing_provider,
        )
        writing_retry.agent_name = "Writing Agent Retry"
        final_output = writing_retry.output
        agent_outputs.append(writing_retry)
        judge_result = self.judge.evaluate(agent_outputs, final_output=final_output, avoid_provider=writing_retry.provider)
        retry_trace.append(
            WorkflowStep(
                step=0,
                stage="Retry review",
                agent_name=self.judge.name,
                status="complete",
                summary=f"Retry score is {judge_result.overall_score}/100.",
            )
        )
        return {"final_output": final_output, "agent_outputs": agent_outputs, "judge_result": judge_result, "workflow_trace": retry_trace}
