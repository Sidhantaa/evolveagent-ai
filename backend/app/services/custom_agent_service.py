from datetime import UTC, datetime
from uuid import uuid4

from app.agents.base_agent import BaseAgent
from app.models.response_models import AgentOutput, CustomAgentResult
from app.services.llm_router import llm_router
from app.services.storage_service import StorageService

# model_preference (validated by Create/UpdateCustomAgentRequest as one of
# default|openai|claude|gemini|mock) -> real LLMRouter provider id. "claude"
# is the only one that needs a name translation; the rest already match.
_MODEL_PREFERENCE_PROVIDER = {"openai": "openai", "claude": "anthropic", "gemini": "gemini", "mock": "mock"}


class RuntimeCustomAgent(BaseAgent):
    def __init__(self, config: dict):
        self.name = config.get("name", "Custom Agent")
        self.system_prompt = config.get("prompt") or config.get("role") or "You are a careful custom specialist agent."
        # model_preference was validated, persisted, and API-exposed but never
        # actually honored at execution time -- a custom agent explicitly
        # pinned to (e.g.) "gemini" for cost/privacy reasons silently ran on
        # whatever the default agent-name routing picked instead. "default"
        # (or anything unrecognized) keeps the original agent-name routing
        # unchanged, matching prior behavior exactly.
        self.model_preference = _MODEL_PREFERENCE_PROVIDER.get(str(config.get("model_preference") or "").lower())

    def run_with_metadata(self, user_input: str, context: str = "", avoid_provider: str | None = None) -> AgentOutput:
        if self.model_preference is None:
            return super().run_with_metadata(user_input, context, avoid_provider=avoid_provider)
        prompt = f"User task:\n{user_input}\n\nShared context:\n{context}".strip()
        model = llm_router.model_for_provider(self.model_preference)
        result = llm_router.generate_for_provider(self.model_preference, model, self.system_prompt, prompt)
        return AgentOutput(
            agent_name=self.name,
            provider=result.provider,
            model=result.model,
            latency_ms=result.latency_ms,
            success=result.success,
            fallback_used=result.fallback_used,
            error=result.error,
            output=result.output,
        )


class CustomAgentService:
    def __init__(self, storage: StorageService, memory_v2=None):
        self.storage = storage
        # v140 Workspace Brain: optional MemoryService (v2) collaborator. Agents
        # are the last of the workspace's own "chats, files, goals, agents, and
        # memory" context pillars to reach real semantic recall. Best-effort,
        # never blocks agent creation.
        self.memory_v2 = memory_v2

    def _mirror_to_memory_v2(self, agent: CustomAgentResult) -> None:
        if self.memory_v2 is None or not agent.workspace_id:
            return
        try:
            text = f"Agent: {agent.name}\n{agent.role}\n{agent.description}".strip()
            if not text:
                return
            self.memory_v2.add(
                text, kind="agent", source="custom_agent_service",
                metadata={"workspace_id": agent.workspace_id, "agent_id": agent.agent_id},
            )
        except Exception:
            pass

    @staticmethod
    def templates() -> list[dict]:
        return [
            {
                "name": "Resume Agent",
                "role": "Improve resumes for target roles using evidence, keywords, and concise bullets.",
                "description": "Optimizes resumes and internship applications.",
                "default_prompt": "You are a Resume Agent. Improve resumes with clear impact, ATS keywords, and honest evidence.",
                "tools_allowed": [],
                "approval_level": "read_only",
                "recommended_use_case": "Resume review and job application improvement.",
            },
            {
                "name": "Code Review Agent",
                "role": "Review code quality, architecture, risks, and tests.",
                "description": "Finds code issues and suggests safe improvements.",
                "default_prompt": "You are a Code Review Agent. Focus on bugs, maintainability, security, and missing tests.",
                "tools_allowed": ["file_read"],
                "approval_level": "plan_only",
                "recommended_use_case": "Code review and architecture feedback.",
            },
            {
                "name": "Meeting Notes Agent",
                "role": "Turn transcripts into notes, action items, and decisions.",
                "description": "Summarizes meetings and recordings.",
                "default_prompt": "You are a Meeting Notes Agent. Extract decisions, action items, owners, and follow-ups.",
                "tools_allowed": ["recording_read"],
                "approval_level": "read_only",
                "recommended_use_case": "Meeting and lecture summaries.",
            },
            {
                "name": "File Summary Agent",
                "role": "Summarize uploaded documents and extract key points.",
                "description": "Analyzes files and documents.",
                "default_prompt": "You are a File Summary Agent. Summarize document structure, key claims, and action items.",
                "tools_allowed": ["file_read"],
                "approval_level": "read_only",
                "recommended_use_case": "PDF, DOCX, CSV, code, and text file analysis.",
            },
            {
                "name": "Pharmacy PA Agent",
                "role": "Organize prior authorization information for human review.",
                "description": "Structures pharmacy PA criteria and missing information.",
                "default_prompt": "You are a Pharmacy PA Agent. Organize PA criteria and flag missing details. Do not provide medical advice.",
                "tools_allowed": [],
                "approval_level": "read_only",
                "recommended_use_case": "Pharmacy prior authorization support.",
            },
            {
                "name": "Construction Bid Agent",
                "role": "Break construction bid requirements into scope, risks, and checklist items.",
                "description": "Helps analyze construction bid documents.",
                "default_prompt": "You are a Construction Bid Agent. Extract scope, exclusions, risks, and required next steps.",
                "tools_allowed": ["file_read"],
                "approval_level": "read_only",
                "recommended_use_case": "Bid review and scope summaries.",
            },
            {
                "name": "Business Analyst Agent",
                "role": "Analyze business ideas, market risks, and next steps.",
                "description": "Evaluates business concepts and strategy.",
                "default_prompt": "You are a Business Analyst Agent. Assess market, customer, risks, and practical next steps.",
                "tools_allowed": [],
                "approval_level": "read_only",
                "recommended_use_case": "Business idea and startup analysis.",
            },
            {
                "name": "Startup Strategy Agent",
                "role": "Create startup validation plans and launch roadmaps.",
                "description": "Plans startup experiments and milestones.",
                "default_prompt": "You are a Startup Strategy Agent. Prioritize validation, traction, and implementation steps.",
                "tools_allowed": [],
                "approval_level": "read_only",
                "recommended_use_case": "Startup roadmaps and go-to-market planning.",
            },
            {
                "name": "Bug Fix Agent",
                "role": "Diagnose bugs and propose safe implementation steps.",
                "description": "Creates bug-fix plans with test ideas.",
                "default_prompt": "You are a Bug Fix Agent. Identify likely causes, safe fixes, and tests before editing.",
                "tools_allowed": ["file_read"],
                "approval_level": "plan_only",
                "recommended_use_case": "Bug triage and implementation planning.",
            },
            {
                "name": "Study Notes Agent",
                "role": "Create study notes, Q&A, and review plans.",
                "description": "Turns material into study guides.",
                "default_prompt": "You are a Study Notes Agent. Create clear notes, practice questions, and review checklists.",
                "tools_allowed": ["file_read", "recording_read"],
                "approval_level": "read_only",
                "recommended_use_case": "Study notes and exam preparation.",
            },
        ]

    def create(self, data: dict) -> CustomAgentResult:
        now = datetime.now(UTC).isoformat()
        if data.get("template_name"):
            template = self.template_by_name(data["template_name"])
            if template:
                data = {
                    "name": template["name"],
                    "description": template["description"],
                    "role": template["role"],
                    "prompt": template["default_prompt"],
                    "tools_allowed": template["tools_allowed"],
                    "approval_level": template["approval_level"],
                    "template_name": template["name"],
                    **{key: value for key, value in data.items() if value not in (None, "", [])},
                }
        agent = CustomAgentResult(
            agent_id=str(uuid4()),
            workspace_id=data.get("workspace_id"),
            name=data.get("name") or "Custom Agent",
            description=data.get("description") or "",
            role=data.get("role") or "",
            prompt=data.get("prompt") or data.get("role") or "You are a helpful custom specialist agent.",
            tools_allowed=data.get("tools_allowed", []),
            model_preference=data.get("model_preference", "default"),
            memory_scope=data.get("memory_scope", "session"),
            approval_level=data.get("approval_level", "read_only"),
            created_at=now,
            updated_at=now,
            enabled=data.get("enabled", True),
            template_name=data.get("template_name"),
        )
        items = self.storage.read_list("custom_agents.json")
        items.append(agent.model_dump())
        self.storage.write_list("custom_agents.json", items)
        self._mirror_to_memory_v2(agent)
        return agent

    def list(self, workspace_id: str | None = None) -> list[dict]:
        items = self.storage.read_list("custom_agents.json")
        if workspace_id:
            items = [item for item in items if item.get("workspace_id") == workspace_id]
        return sorted(items, key=lambda item: item.get("updated_at") or "", reverse=True)

    def get(self, agent_id: str) -> dict | None:
        return next((item for item in self.storage.read_list("custom_agents.json") if item.get("agent_id") == agent_id), None)

    def update(self, agent_id: str, updates: dict) -> dict | None:
        items = self.storage.read_list("custom_agents.json")
        agent = next((item for item in items if item.get("agent_id") == agent_id), None)
        if agent is None:
            return None
        for key in (
            "name",
            "description",
            "role",
            "prompt",
            "tools_allowed",
            "model_preference",
            "memory_scope",
            "approval_level",
            "enabled",
        ):
            if key in updates and updates[key] is not None:
                agent[key] = updates[key]
        agent["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.write_list("custom_agents.json", items)
        return agent

    def delete(self, agent_id: str) -> dict | None:
        return self.update(agent_id, {"enabled": False})

    def run(self, agent_id: str, user_input: str, context: str = "") -> tuple[AgentOutput | None, dict | None]:
        config = self.get(agent_id)
        if config is None or not config.get("enabled", True):
            return None, config
        if config.get("approval_level") == "blocked":
            return AgentOutput(
                agent_name=config.get("name", "Custom Agent"),
                provider="rule-based",
                model="permission-blocked",
                success=False,
                fallback_used=False,
                error="Custom agent is blocked by its approval level.",
                output="This custom agent is disabled by its permission level.",
            ), config
        agent = RuntimeCustomAgent(config)
        return agent.run_with_metadata(user_input, context), config

    @classmethod
    def template_by_name(cls, name: str) -> dict | None:
        lowered = name.lower()
        return next((item for item in cls.templates() if item["name"].lower() == lowered), None)
