"""
LLM-based metric extraction service - stub.
Future: extract metrics from free-text chat messages.
"""

from typing import Any


class ExtractionService:
    """
    Extracts structured metrics from unstructured chat content.
    Stub: no LLM calls. Real implementation will use embeddings/NER/LLM.
    """

    async def extract_metrics(self, text: str) -> list[dict[str, Any]]:
        """
        Extract metric values and confidence from text.
        Returns list of dicts: [{metric_id, value, confidence, snippet}, ...]
        """
        return []
