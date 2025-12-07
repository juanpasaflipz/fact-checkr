import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.intelligence_service import IntelligenceService
from app.database.models import Claim, Entity

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_embedding_service():
    with patch('app.services.intelligence_service.EmbeddingService') as MockService:
        service_instance = MockService.return_value
        service_instance.find_similar_claims = AsyncMock(return_value=[])
        service_instance.find_contradicting_facts = AsyncMock(return_value=[])
        yield service_instance

@pytest.fixture
def service(mock_db, mock_embedding_service):
    return IntelligenceService(mock_db)

@pytest.mark.asyncio
async def test_find_similar_claims(service, mock_embedding_service):
    # Arrange
    query = "test claim"
    expected_result = [{"id": "1", "text": "similar claim", "similarity": 0.9}]
    mock_embedding_service.find_similar_claims.return_value = expected_result
    
    # Act
    result = await service.find_similar_claims(query, limit=5, threshold=0.8)
    
    # Assert
    assert result == expected_result
    mock_embedding_service.find_similar_claims.assert_called_once_with(
        query_text=query,
        limit=5,
        threshold=0.8,
        status_filter=None
    )

@pytest.mark.asyncio
async def test_check_contradictions_no_issues(service, mock_embedding_service):
    # Arrange
    mock_embedding_service.find_contradicting_facts.return_value = []
    mock_embedding_service.find_similar_claims.return_value = []
    
    # Act
    result = await service.check_contradictions("some claim")
    
    # Assert
    assert result["alert_level"] == "none"
    assert result["potential_contradictions"] == []

@pytest.mark.asyncio
async def test_check_contradictions_with_issues(service, mock_embedding_service):
    # Arrange
    mock_embedding_service.find_contradicting_facts.return_value = [{"fact": "contradiction"}]
    
    # Act
    result = await service.check_contradictions("some claim")
    
    # Assert
    assert result["alert_level"] == "high"
    assert len(result["potential_contradictions"]) == 1

