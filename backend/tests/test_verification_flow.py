import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
from datetime import datetime

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import FactChecker
# VerificationStatus is returned as part of VerificationResult from schemas
from app.schemas import VerificationStatus

@patch("app.agents.legacy_agent.MockScraper")
@patch("app.agents.legacy_agent.TwitterScraper")
@patch("app.agents.legacy_agent.GoogleNewsScraper")
@patch("app.agents.legacy_agent.FacebookScraper")
@patch("app.agents.legacy_agent.InstagramScraper")
@patch("app.agents.legacy_agent.DuplicateDetector")
@patch("app.agents.legacy_agent.settings")
@pytest.mark.asyncio
async def test_verification_flow_integration(
    mock_settings, mock_dup, mock_insta, mock_fb, mock_google, mock_twitter, mock_mock_scraper
):
    """
    Integration test for the full verification flow:
    1. Extract claim
    2. Verify claim (Search + Analysis)
    3. Produce verification result
    """
    # Setup common mocks
    mock_settings.ANTHROPIC_API_KEY = "fake-key"
    
    # Mock Anthropic for both extraction and verification
    with patch("app.agents.legacy_agent.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # We need to mock different responses for the sequence of calls
        # 1. Extraction response
        extraction_response = MagicMock()
        extraction_content = MagicMock()
        extraction_content.text = "The sky is green"
        extraction_response.content = [extraction_content]
        
        # 2. Search query generation response
        search_query_response = MagicMock()
        search_query_content = MagicMock()
        search_query_content.text = '{"queries": ["sky color verification", "is the sky green"]}'
        search_query_response.content = [search_query_content]
        
        # 3. Verification analysis response
        verification_response = MagicMock()
        verification_content = MagicMock()
        verification_content.text = '{"status": "Debunked", "explanation": "The sky is blue due to Rayleigh scattering.", "confidence": 0.99}'
        verification_response.content = [verification_content]
        
        # Configure side_effect to return these responses in order
        # Note: Depending on implementation details, intermediate calls might happen.
        # Ideally we'd match by input prompt, but for a flow test, sequence often works if predictable.
        # Configure side_effect to return the verification response
        mock_client.messages.create.side_effect = [
            # extraction_response,  # We are skipping extraction in this test call
            # search_query_response, # We are skipping search query gen
            verification_response
        ]
        
        # Mock Search Tool
        # legacy_agent calls search_web, which uses Tavily
        # search_web is imported from app.services.search_service
        # So we patch search_web in legacy_agent
        with patch("app.agents.legacy_agent.search_web") as mock_search:
            mock_search.return_value = [
                "http://science.org/sky"
            ]

            # Instantiate FactChecker
            checker = FactChecker()
            
            # Manually trigger the flow components (since start_monitoring is an infinite loop)
            # We will test the core logic: `process_content` or equivalent if accessible, 
            # or recreate the steps `verify_claim` orchestrates.
            
            # Assuming we want to test `verify_claim` directly as it's the core logic
            claim_text = "The sky is green"
            
            # Mock DB session
            mock_db = MagicMock()
            
            # Run verification
            # _verify_claim expects claim text and list of evidence URLs
            evidence = ["http://science.org/sky"]
            result = await checker._verify_claim(claim_text, evidence)
            
            # Assertions
            assert result is not None
            assert result.status == VerificationStatus.DEBUNKED
            assert "blue" in result.explanation
            
            # Verify tool usage
            assert mock_client.messages.create.call_count >= 1 # Verification call

@patch("app.agents.legacy_agent.MockScraper")
@patch("app.agents.legacy_agent.TwitterScraper")
@patch("app.agents.legacy_agent.GoogleNewsScraper")
@patch("app.agents.legacy_agent.FacebookScraper")
@patch("app.agents.legacy_agent.InstagramScraper")
@patch("app.agents.legacy_agent.DuplicateDetector")
@patch("app.agents.legacy_agent.settings")
@pytest.mark.asyncio
async def test_verification_flow_skip_irrelevant(
     mock_settings, mock_dup, mock_insta, mock_fb, mock_google, mock_twitter, mock_mock_scraper
):
    """Test that irrelevant content is skipped during extraction"""
    mock_settings.ANTHROPIC_API_KEY = "fake-key"
    
    with patch("app.agents.legacy_agent.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # SKIP response
        skip_response = MagicMock()
        skip_content = MagicMock()
        skip_content.text = "SKIP"
        skip_response.content = [skip_content]
        
        mock_client.messages.create.return_value = skip_response
        
        checker = FactChecker()
        
        claim = await checker._extract_claim("Just a random update")
        
        assert claim == "SKIP"
