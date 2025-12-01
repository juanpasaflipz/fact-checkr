"""
Base Agent for Multi-Agent Verification System

Each agent specializes in a specific aspect of fact-checking.
Agents run in parallel and their findings are synthesized by the orchestrator.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from pydantic import BaseModel
import anthropic
import openai
import os
import logging

logger = logging.getLogger(__name__)


class AgentResult(BaseModel):
    """Standardized result from any verification agent"""
    agent_name: str
    confidence: float  # 0.0 to 1.0
    findings: str  # JSON string with detailed findings
    verdict: Optional[str] = None  # Agent's suggested verdict
    sources_used: list = []
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all verification agents"""
    
    def __init__(self):
        # Try Anthropic first (primary)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        self.anthropic_client = None
        self.openai_client = None
        
        if anthropic_key:
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
            except Exception as e:
                logger.warning(f"Failed to init Anthropic: {e}")
        
        if openai_key:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
            except Exception as e:
                logger.warning(f"Failed to init OpenAI: {e}")
        
        self.primary_model = "claude-sonnet-4-20250514"
        self.fallback_model = "gpt-4o-mini"
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent specializes in"""
        pass
    
    @abstractmethod
    async def analyze(self, claim: str, context: Dict) -> AgentResult:
        """Main analysis method - must be implemented by each agent"""
        pass
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2
    ) -> str:
        """Call LLM with automatic fallback"""
        
        # Try Anthropic first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model=self.primary_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text.strip()
            except Exception as e:
                logger.warning(f"Anthropic call failed: {e}")
        
        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI call also failed: {e}")
        
        raise RuntimeError("No LLM available for agent")
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks"""
        import json
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            # Find the actual JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                response = response[json_start:json_end]
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nResponse was: {response[:200]}")
            return {"error": "Failed to parse response", "raw": response[:500]}

