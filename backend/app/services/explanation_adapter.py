"""
Service for adapting explanations to different reading levels
"""
from typing import Optional


def adjust_explanation_for_reading_level(
    explanation: str,
    reading_level: str = "normal"
) -> str:
    """
    Adjust explanation text based on reading level.
    
    Args:
        explanation: Original explanation text
        reading_level: "simple", "normal", or "expert"
    
    Returns:
        Adjusted explanation text
    """
    if not explanation:
        return explanation
    
    if reading_level == "simple":
        # For simple level, we'd ideally regenerate with simpler prompts
        # For now, return as-is with a note that this is a simplified version
        # In production, you'd call the AI again with a "ELI12" style prompt
        return explanation  # TODO: Implement proper simplification
    
    elif reading_level == "expert":
        # For expert level, we'd add more technical details
        # For now, return as-is
        return explanation  # TODO: Implement expert-level enhancement
    
    else:  # normal
        return explanation


def get_reading_level_instruction(reading_level: str) -> str:
    """
    Get instruction text to add to AI prompts for reading level adjustment.
    """
    if reading_level == "simple":
        return """Write the explanation as if explaining to a 12-year-old:
- Use short, simple sentences
- Avoid technical jargon
- Use analogies when helpful
- Keep it under 200 words"""
    
    elif reading_level == "expert":
        return """Write a detailed, technical explanation:
- Use precise terminology
- Include relevant context and background
- Reference specific data points
- Provide nuanced analysis"""
    
    else:  # normal
        return """Write a clear, informative explanation suitable for general audience:
- Balance simplicity with accuracy
- Use accessible language
- Provide context when needed"""

