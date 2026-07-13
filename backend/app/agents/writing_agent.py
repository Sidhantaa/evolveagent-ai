from app.agents.base_agent import BaseAgent
from app.models.response_models import AgentOutput


class WritingAgent(BaseAgent):
    name = "Writing Agent"
    system_prompt = (
        "You are the Writing Agent. Your job is to combine all agent outputs into one clear, polished, "
        "user-facing final answer."
    )

    def run_final(self, user_input: str, agent_outputs: list[AgentOutput], judge_summary: str) -> str:
        return self.run_final_with_metadata(user_input, agent_outputs, judge_summary).output

    def run_final_with_metadata(
        self,
        user_input: str,
        agent_outputs: list[AgentOutput],
        judge_summary: str,
        avoid_provider: str | None = None,
        workspace_id: str | None = None,
    ) -> AgentOutput:
        context = "\n\n".join(f"{item.agent_name}:\n{item.output}" for item in agent_outputs)
        return self.run_with_metadata(
            user_input,
            context=f"{context}\n\nJudge summary:\n{judge_summary}",
            avoid_provider=avoid_provider,
            workspace_id=workspace_id,
        )
