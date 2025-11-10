"""
Simple chat step that calls LLM directly.
"""
from typing import Dict, Any
from ia_modules.pipeline.core import Step


class SimpleChatStep(Step):
    """Simple LLM chat step."""

    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chat with LLM."""
        message = data.get('message', '')
        chat_history = data.get('chat_history', [])

        # Get LLM service from services registry
        llm_service = self.services.get('llm_provider')

        if not llm_service:
            raise RuntimeError("LLM service not available")

        # Build messages list with history + new message
        messages = chat_history + [{"role": "user", "content": message}]

        # Generate response using messages format with history
        response = await llm_service.generate_completion(
            messages=messages,
            temperature=self.config.get('temperature', 0.7),
            max_tokens=self.config.get('max_tokens', 500)
        )

        return {
            'response': response['content'],
            'metadata': {
                'provider': response['metadata'].get('provider_name', 'unknown'),
                'model': response['model'],
                'tokens': response['usage'].get('total_tokens', 0),
                'cost_usd': response['usage'].get('cost_usd', 0.0)
            }
        }
