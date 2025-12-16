import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.verification_team import VerificationOrchestrator, VerificationContext

@pytest.mark.asyncio
async def test_verification_orchestrator_integration():
    """
    Integration test for the full multi-agent verification flow.
    Mocks the underlying LLM calls but tests the orchestration logic,
    parallel execution, and result synthesis.
    """
    
    # Define the mock responses for each agent based on prompt keywords
    async def mock_llm_side_effect(system_prompt, user_prompt, **kwargs):
        if "Analiza la credibilidad de estas fuentes" in user_prompt:
            return json.dumps({
                "overall_source_quality": "high",
                "most_credible_sources": ["http://reliable-news.com"],
                "concerns": [],
                "bias_detected": "none",
                "has_official_sources": True,
                "recommendation": "Trustworthy source"
            })
        elif "Analiza el contexto histórico" in user_prompt:
            return json.dumps({
                "contradicts_known_facts": False,
                "contradicting_facts": [],
                "is_repeat_misinformation": False,
                "historical_context": "No contradictory historical record found.",
                "similar_debunked_patterns": [],
                "confidence_in_analysis": 0.8
            })
        elif "Analiza la consistencia lógica" in user_prompt:
            return json.dumps({
                "is_logically_consistent": True,
                "fallacies_detected": [],
                "manipulation_techniques": [],
                "factual_claims": ["Sky is blue"],
                "opinion_claims": [],
                "emotional_manipulation_level": "none",
                "overall_assessment": "factual"
            })
        elif "Analiza la evidencia encontrada" in user_prompt:
            return json.dumps({
                "supports_claim": "yes",
                "evidence_strength": "strong",
                "key_supporting_points": ["Scientific consensus", "Spectroscopy"],
                "key_refuting_points": [],
                "source_consistency": "consistent",
                "evidence_gaps": [],
                "preliminary_verdict": "likely_true",
                "verdict_confidence": 0.95
            })
        elif "Eres el Editor en Jefe" in user_prompt or "Sintetiza los análisis" in user_prompt:
            # Final verdict synthesis
            return json.dumps({
                "status": "Verified",
                "confidence": 0.92,
                "explanation": "All agents confirm the sky is blue based on evidence and logic.",
                "key_evidence": ["Scientific consensus", "High quality sources"],
                "source_types": ["Académico"],
                "caveats": [],
                "agent_agreement": "high",
                "recommended_action": "publish"
            })
        else:
            return json.dumps({"error": "Unknown prompt"})

    # Patch the _call_llm method on BaseAgent
    with patch("app.agents.base_agent.BaseAgent._call_llm", side_effect=mock_llm_side_effect) as mock_call_llm:
        
        # Instantiate Orchestrator
        orchestrator = VerificationOrchestrator()
        
        # Prepare context
        context: VerificationContext = {
            "evidence_urls": ["http://reliable-news.com/article"],
            "evidence_texts": ["Scientific study confirms Rayleigh scattering causes blue sky."],
            "source_credibility": {"domain": "reliable-news.com", "tier": "A", "credibility_score": 0.95},
            "web_evidence": [{"url": "http://reliable-news.com/article", "credibility_tier": "A"}],
            "similar_claims": [],
            "entity_facts": [],
            "has_prior_debunked": False,
            "original_text": "Look at the blue sky."
        }
        
        # Run verification
        claim = "The sky is blue"
        result = await orchestrator.verify_claim(claim, context)
        
        # Assertions
        assert result is not None
        assert "final_verdict" in result
        
        # Check verdict structure
        verdict = result["final_verdict"]
        assert verdict["status"] == "Verified"
        assert verdict["confidence"] > 0.9
        assert verdict["agent_agreement"] == "high"
        
        # Check that all agents ran
        agent_results = result["agent_results"]
        # We expect 4 agents (SourceCredib, Historical, Logical, Evidence)
        assert len(agent_results) == 4
        
        agent_names = [r["agent"] for r in agent_results]
        assert "SourceCredibilityAgent" in agent_names
        assert "HistoricalContextAgent" in agent_names
        assert "LogicalConsistencyAgent" in agent_names
        assert "EvidenceAnalysisAgent" in agent_names
        
        # Check timings
        assert "processing_time_seconds" in result
        assert result["processing_time_seconds"] >= 0
        
        # Verify call count (4 agents + 1 synthesis = 5 calls)
        assert mock_call_llm.call_count == 5
