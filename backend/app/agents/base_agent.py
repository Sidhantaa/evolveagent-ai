from app.models.response_models import AgentOutput
from app.services.llm_router import llm_router


class BaseAgent:
    name = "Base Agent"
    system_prompt = "You are a helpful specialist agent."

    def run(self, user_input: str, context: str = "") -> str:
        return self.run_with_metadata(user_input, context).output

    def run_with_metadata(
        self, user_input: str, context: str = "", avoid_provider: str | None = None, workspace_id: str | None = None,
    ) -> AgentOutput:
        prompt = f"User task:\n{user_input}\n\nShared context:\n{context}".strip()
        result = llm_router.generate(self.name, self.system_prompt, prompt, avoid_provider=avoid_provider, workspace_id=workspace_id)
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
