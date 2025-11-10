"""
Title generation step - generates concise chat thread titles.
"""
from typing import Dict, Any
from ia_modules.pipeline.core import Step


class TitleGenerationStep(Step):
    """Generate a concise title for a chat thread based on the first message."""

    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate title using LLM."""
        message = data.get('message', '')

        # Get LLM service from services registry
        llm_service = self.services.get('llm_provider')

        if not llm_service:
            raise RuntimeError("LLM service not available")

        # Prompt to generate concise title
        title_prompt = f"""Generate a short, concise title (3-6 words maximum) for a chat conversation that starts with this user message:

"{message}"

Return ONLY the title, nothing else. The title should capture the main topic or intent."""

        # Generate title
        response = await llm_service.generate_completion(
            messages=[{"role": "user", "content": title_prompt}],
            temperature=self.config.get('temperature', 0.3),  # Lower temp for more focused titles
            max_tokens=self.config.get('max_tokens', 20)  # Short titles only
        )

        # Extract title and clean it up
        title = response['content'].strip()

        # Remove quotes if LLM wrapped it
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
        if title.startswith("'") and title.endswith("'"):
            title = title[1:-1]

        # Ensure it's not too long (max 60 chars)
        if len(title) > 60:
            title = title[:57] + "..."

        return {
            'title': title,
            'title_metadata': {
                'model': response['model'],
                'tokens': response['usage'].get('total_tokens', 0)
            }
        }
