"""
LLM-based value normalization service - stub.
Future: normalize extracted values to canonical metric scales.
"""

from typing import Any


class NormalizationService:
    """
    Normalizes extracted values to metric scale types.
    Stub: no LLM calls. Real implementation will handle
    categorical mapping, unit conversion, etc.
    """

    async def normalize(
        self, value: str | float | int | bool, scale_type: str
    ) -> tuple[str, float]:
        """
        Normalize value for given scale_type.
        Returns (normalized_value_str, confidence).
        """
        return (str(value), 1.0)
