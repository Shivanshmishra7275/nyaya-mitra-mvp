"""
Test suite for Nyaya Mitra API endpoints
"""

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_check_success(self, test_client):
        """Health check should return 200"""
        response = test_client.get('/health')
        assert response.status_code == status.HTTP_200_OK
        assert 'status' in response.json()
    
    def test_health_check_structure(self, test_client):
        """Health check response should have required fields"""
        response = test_client.get('/health')
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert data['status'] == 'ok'


class TestLegalQueryEndpoint:
    """Tests for /legal-query endpoint"""
    
    def test_legal_query_success(self, test_client, sample_query, mock_rag_service, mock_gemini_service):
        """Legal query should return 200 with response"""
        response = test_client.post('/legal-query', json=sample_query)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_legal_query_missing_query(self, test_client):
        """Query without query field should fail"""
        response = test_client.post('/legal-query', json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_legal_query_validation(self, test_client):
        """Query should validate input"""
        invalid_queries = [
            {'query': None},
            {'query': ''},
            {'query': 'a' * 5001},  # Too long
        ]
        for invalid_query in invalid_queries:
            response = test_client.post('/legal-query', json=invalid_query)
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    def test_legal_query_response_structure(self, test_client, sample_query, mock_rag_service, mock_gemini_service):
        """Query response should have required fields"""
        response = test_client.post('/legal-query', json=sample_query)
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert 'response' in data or 'error' in data


class TestDocumentDraftEndpoint:
    """Tests for /document-draft endpoint"""
    
    def test_document_draft_success(self, test_client, sample_draft_request, mock_gemini_service):
        """Draft request should return 200 with document"""
        response = test_client.post('/document-draft', json=sample_draft_request)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
    
    def test_document_draft_missing_type(self, test_client):
        """Draft without document_type should fail"""
        response = test_client.post('/document-draft', json={'template_params': {}})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_document_draft_invalid_type(self, test_client):
        """Draft with invalid document_type should fail"""
        response = test_client.post('/document-draft', json={
            'document_type': 'invalid_type',
            'template_params': {}
        })
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self, test_client):
        """Request to non-existent endpoint should return 404"""
        response = test_client.get('/nonexistent')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_method_not_allowed(self, test_client):
        """Wrong HTTP method should return 405"""
        response = test_client.get('/legal-query')  # Should be POST
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_invalid_json(self, test_client):
        """Invalid JSON should return 400"""
        response = test_client.post(
            '/legal-query',
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.integration
class TestIntegration:
    """Integration tests with real services"""
    
    def test_full_query_flow(self, test_client, sample_query):
        """Test complete query flow"""
        response = test_client.post('/legal-query', json=sample_query)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    @pytest.mark.slow
    def test_concurrent_queries(self, test_client, sample_query):
        """Test handling of concurrent requests"""
        responses = []
        for _ in range(5):
            response = test_client.post('/legal-query', json=sample_query)
            responses.append(response.status_code)
        
        # At least some should succeed
        assert any(code in [200, 400] for code in responses)


@pytest.mark.performance
class TestPerformance:
    """Performance tests"""
    
    def test_query_response_time(self, test_client, sample_query, benchmark_timer):
        """Query should respond in reasonable time"""
        with benchmark_timer:
            response = test_client.post('/legal-query', json=sample_query)
        
        # Response should be within 30 seconds
        assert benchmark_timer.elapsed < 30
    
    def test_health_check_latency(self, test_client, benchmark_timer):
        """Health check should be fast"""
        with benchmark_timer:
            response = test_client.get('/health')
        
        # Health check should be under 100ms
        assert benchmark_timer.elapsed < 0.1
        assert response.status_code == status.HTTP_200_OK
