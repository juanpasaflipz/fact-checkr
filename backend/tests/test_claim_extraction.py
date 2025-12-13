import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents import FactChecker

# Patch the scrapers to avoid network calls during init
@patch("app.agent.MockScraper")
@patch("app.agent.TwitterScraper")
@patch("app.agent.GoogleNewsScraper")
@patch("app.agent.FacebookScraper")
@patch("app.agent.InstagramScraper")
@patch("app.agent.DuplicateDetector")
@patch("app.agent.os.getenv")
@pytest.mark.asyncio
async def test_extract_claim_anthropic(mock_getenv, mock_dup, mock_insta, mock_fb, mock_google, mock_twitter, mock_mock_scraper):
    # Setup mocks
    mock_getenv.return_value = "fake-key" # For API keys
    
    # Mock Anthropic client
    with patch("app.agent.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Setup response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Verify this claim"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        checker = FactChecker()
        
        claim = await checker._extract_claim("Original content mentioning policies")
        
        assert claim == "Verify this claim"
        mock_client.messages.create.assert_called_once()

@patch("app.agent.MockScraper")
@patch("app.agent.TwitterScraper")
@patch("app.agent.GoogleNewsScraper")
@patch("app.agent.FacebookScraper")
@patch("app.agent.InstagramScraper")
@patch("app.agent.DuplicateDetector")
@patch("app.agent.os.getenv")
@pytest.mark.asyncio
async def test_extract_claim_skip(mock_getenv, mock_dup, mock_insta, mock_fb, mock_google, mock_twitter, mock_mock_scraper):
    mock_getenv.return_value = "fake-key"
    
    with patch("app.agent.anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        # Setup SKIP response
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "SKIP"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        
        checker = FactChecker()
        
        claim = await checker._extract_claim("Just some noise")
        
        assert claim == "SKIP"
