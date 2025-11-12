"""
Simple chat step that calls LLM directly.
"""
from typing import Dict, Any
from ia_modules.pipeline.core import Step


class SimpleChatStep(Step):
    """Simple LLM chat step."""

    async def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chat with LLM, including optional document context with RAG-style citations."""
        message = data.get('message', '')
        chat_history = data.get('chat_history', [])
        system_prompt = data.get('system_prompt')
        document_context = data.get('document_context', '')
        document_count = data.get('document_count', 0)
        chunk_mapping = data.get('chunk_mapping', [])

        # Get LLM service from services registry
        llm_service = self.services.get('llm_provider')

        if not llm_service:
            raise RuntimeError("LLM service not available")

        # Build messages list with optional system prompt + document context + history + new message
        messages = []

        # Add system message with document context if provided
        if system_prompt or document_context:
            system_content_parts = []

            if system_prompt:
                system_content_parts.append(system_prompt)

            if document_context:
                system_content_parts.append("\n\n" + document_context)
                system_content_parts.append(
                    "\n**IMPORTANT CITATION INSTRUCTIONS**:\n"
                    "When using information from the documents above, you MUST cite your sources.\n"
                    "- Each document chunk has a citation ID in square brackets like [doc1_chunk0]\n"
                    "- Include these citation IDs inline as you write, immediately after the relevant information\n"
                    "- Use the exact format shown in the documents (e.g., [doc1_chunk0], [doc2_chunk1])\n"
                    "- You can cite multiple chunks for the same statement if needed\n"
                    "- Example: 'According to [doc1_chunk0], the primary cause was climate change.'\n"
                    "- Example: 'The study found [doc2_chunk1] that temperatures increased by 2°C [doc2_chunk2].'\n"
                    "\nAlways cite your sources to help users verify the information."
                )

            messages.append({
                "role": "system",
                "content": "\n".join(system_content_parts)
            })

        # Add chat history and current message
        messages.extend(chat_history)
        messages.append({"role": "user", "content": message})

        # Increase max_tokens if documents are present (longer context needs longer responses)
        max_tokens = self.config.get('max_tokens', 1000 if document_count > 0 else 500)

        # Generate response using messages format with history
        response = await llm_service.generate_completion(
            messages=messages,
            temperature=self.config.get('temperature', 0.7),
            max_tokens=max_tokens
        )

        return {
            'response': response['content'],
            'metadata': {
                'provider': response['metadata'].get('provider_name', 'unknown'),
                'model': response['model'],
                'tokens': response['usage'].get('total_tokens', 0),
                'cost_usd': response['usage'].get('cost_usd', 0.0),
                'documents_used': document_count,
                'chunk_mapping': chunk_mapping  # Pass through for frontend citations
            }
        }
