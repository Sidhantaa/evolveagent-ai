import re

from app.models.response_models import AgentOutput, ImageResult
from app.services.image_service import ImageService


class ImageAgent:
    name = "Image Agent"

    protected_terms = {
        "spider-man": "a comic-book style masked web-slinging superhero inspired character",
        "spider man": "a comic-book style masked web-slinging superhero inspired character",
        "spiderman": "a comic-book style masked web-slinging superhero inspired character",
        "spidermen": "a comic-book style masked web-slinging superhero inspired character",
        "batman": "a dark masked vigilante inspired superhero character",
        "superman": "a hopeful cape-wearing flying superhero inspired character",
        "pikachu": "a cute yellow electric creature inspired character",
    }

    def __init__(self, image_service: ImageService | None = None):
        self.image_service = image_service or ImageService()

    def run(self, user_input: str) -> tuple[AgentOutput, ImageResult]:
        safe_prompt, safety_rewritten = self.build_safe_prompt(user_input)
        image_result = self.image_service.generate(safe_prompt, safety_rewritten=safety_rewritten)
        image_result.original_prompt = user_input
        output = (
            "Generated a safe image prompt and created an image preview. "
            f"Prompt: {safe_prompt}"
        )
        agent_output = AgentOutput(
            agent_name=self.name,
            provider=image_result.provider,
            model=image_result.model,
            latency_ms=0,
            success=True,
            fallback_used=image_result.fallback_used,
            output=output,
        )
        return agent_output, image_result

    def build_safe_prompt(self, user_input: str) -> tuple[str, bool]:
        text = self.clean_image_subject(user_input)
        lower_text = text.lower()
        for protected_term, replacement in self.protected_terms.items():
            if protected_term in lower_text:
                if protected_term in {"spider-man", "spider man", "spiderman", "spidermen"}:
                    return (
                        self.clean_prompt_punctuation(
                            f"{replacement}, red and blue suit, swinging between city skyscrapers at sunset, "
                            "cinematic lighting, dynamic action pose, high detail."
                        ),
                        True,
                    )
                return (
                    self.clean_prompt_punctuation(
                        f"{replacement}, original design, cinematic lighting, polished composition, high detail."
                    ),
                    True,
                )

        cleaned = text or "an original visual concept"
        normalized_cleaned = re.sub(r"^(?:a|an|the)\s+", "", cleaned, flags=re.IGNORECASE).lower()
        if normalized_cleaned == "futuristic ai assistant":
            return (
                self.clean_prompt_punctuation(
                    "A futuristic AI assistant in a sleek holographic interface, glowing blue and silver accents, "
                    "cinematic lighting, polished composition, high-detail sci-fi environment, professional digital art style."
                ),
                False,
            )
        return (
            self.clean_prompt_punctuation(
                f"High quality image of {cleaned}, polished composition, cinematic lighting, detailed style."
            ),
            False,
        )

    @staticmethod
    def clean_image_subject(text: str) -> str:
        cleaned = " ".join(text.strip().split())
        cleaned = re.sub(r"^(?:\d+[\.)]\s*)+", "", cleaned).strip()
        cleaned = re.sub(r"^(?:prompt|option)\s*\d+\s*:\s*", "", cleaned, flags=re.IGNORECASE).strip()

        command_patterns = [
            r"generate\s+(?:an?\s+)?image\s+prompt\s+for\s+",
            r"create\s+(?:an?\s+)?image\s+prompt\s+for\s+",
            r"make\s+(?:an?\s+)?image\s+prompt\s+for\s+",
            r"give\s+(?:me\s+)?(?:an?\s+)?image\s+of\s+",
            r"give\s+(?:me\s+)?(?:a\s+)?photo\s+of\s+",
            r"give\s+(?:me\s+)?(?:a\s+)?picture\s+of\s+",
            r"create\s+(?:me\s+)?(?:an?\s+)?image\s+of\s+",
            r"generate\s+(?:me\s+)?(?:an?\s+)?image\s+of\s+",
            r"make\s+(?:me\s+)?(?:an?\s+)?image\s+of\s+",
            r"create\s+(?:me\s+)?(?:a\s+)?photo\s+of\s+",
            r"generate\s+(?:me\s+)?(?:a\s+)?photo\s+of\s+",
            r"make\s+(?:me\s+)?(?:a\s+)?photo\s+of\s+",
            r"draw\s+",
            r"image\s+of\s+",
            r"image\s+",
            r"picture\s+of\s+",
        ]
        changed = True
        while changed:
            changed = False
            for pattern in command_patterns:
                next_cleaned = re.sub(rf"^{pattern}", "", cleaned, flags=re.IGNORECASE).strip()
                if next_cleaned != cleaned:
                    cleaned = next_cleaned
                    changed = True
        return ImageAgent.clean_prompt_subject(cleaned)

    @staticmethod
    def clean_prompt_subject(text: str) -> str:
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", text.strip())
        cleaned = re.sub(r"([,.;:!?]){2,}", r"\1", cleaned)
        return cleaned.rstrip(" ,.;:")

    @staticmethod
    def clean_prompt_punctuation(prompt: str) -> str:
        cleaned = re.sub(r"\s+([,.;:!?])", r"\1", prompt.strip())
        replacements = {
            ".,": ",",
            "..": ".",
            ",,": ",",
            ",.": ".",
            " ,": ",",
            " .": ".",
        }
        changed = True
        while changed:
            changed = False
            for bad, good in replacements.items():
                if bad in cleaned:
                    cleaned = cleaned.replace(bad, good)
                    changed = True
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned
