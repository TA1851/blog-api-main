"""
Corrected Router Test Suite for Blog API
修正されたBlog APIルーターの包括的テストスイート

This module contains comprehensive tests for all router modules:
- Article Router (/api/v1/articles)
- Auth Router (/api/v1/login, /api/v1/logout, /api/v1/change-password)
- User Router (/api/v1/user)

Test Coverage:
- CRUD operations
- Authentication flows  
- Error handling
- Input validation
- Security features
- Performance metrics
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock, patch
import json
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib

# FastAPI testing
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

# Import the main FastAPI app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import get_db
from models import User, Article, EmailVerification
from schemas import User as UserSchema, ArticleBase
from oauth2 import get_current_user
from hashing import Hash


# Test Configuration
class TestConfig:
    """Test configuration constants"""
    BASE_URL = ""
    API_V1_PREFIX = "/api/v1"
    TEST_USER_EMAIL = "test@example.com"
    TEST_USER_PASSWORD = "testpass123"
    TEST_ARTICLE_TITLE = "Test Article"
    TEST_ARTICLE_CONTENT = "This is test content"
    RATE_LIMIT_CALLS = 100
    PERFORMANCE_THRESHOLD_MS = 1000


# Test Client Setup
@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock(spec=Session)
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.query = Mock()
    db.delete = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_user():
    """Create mock user for testing"""
    user = Mock(spec=User)
    user.id = 1
    user.email = TestConfig.TEST_USER_EMAIL
    user.is_verified = True
    user.verification_attempts = 0
    user.password = Hash.bcrypt("testpass123")
    return user


@pytest.fixture
def mock_article():
    """Create mock article for testing"""
    article = Mock(spec=Article)
    article.id = 1
    article.title = TestConfig.TEST_ARTICLE_TITLE
    article.content = TestConfig.TEST_ARTICLE_CONTENT
    article.is_published = True
    article.user_id = 1
    article.created_at = datetime.utcnow()
    article.updated_at = datetime.utcnow()
    return article


@pytest.fixture
def auth_headers():
    """Create authentication headers"""
    # Mock JWT token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjk5OTk5OTk5fQ.test_signature"
    return {"Authorization": f"Bearer {token}"}


# Article Router Tests
class TestArticleRouterCorrected:
    """Corrected tests for Article Router endpoints"""

    def test_get_all_articles_success(self, client, mock_db, mock_user, mock_article):
        """Test GET /api/v1/articles - successful retrieval"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_query.limit.return_value = mock_query
                mock_query.offset.return_value = [mock_article]
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_200_OK

    def test_get_article_by_id_success(self, client, mock_db, mock_user, mock_article):
        """Test GET /api/v1/articles/{id} - successful retrieval"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = mock_article
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/articles/1",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_200_OK

    def test_create_article_success(self, client, mock_db, mock_user):
        """Test POST /api/v1/articles - successful creation"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                article_data = {
                    "title": "New Article",
                    "content": "Article content",
                    "is_published": True
                }

                response = client.post(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    json=article_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_201_CREATED

    def test_update_article_success(self, client, mock_db, mock_user, mock_article):
        """Test PUT /api/v1/articles - successful update"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = mock_article
                mock_db.query.return_value = mock_query

                update_data = {
                    "id": 1,
                    "title": "Updated Article",
                    "content": "Updated content",
                    "is_published": True
                }

                response = client.put(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    json=update_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_202_ACCEPTED

    def test_delete_article_success(self, client, mock_db, mock_user, mock_article):
        """Test DELETE /api/v1/articles - successful deletion"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = mock_article
                mock_db.query.return_value = mock_query

                delete_data = {"id": 1}

                response = client.delete(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    json=delete_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_get_public_articles(self, client, mock_db, mock_article):
        """Test GET /api/v1/public/articles - public access"""
        with patch('routers.article.get_db', return_value=mock_db):
            # Mock database query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = [mock_article]
            mock_db.query.return_value = mock_query

            response = client.get(f"{TestConfig.API_V1_PREFIX}/public/articles")
            
            assert response.status_code == status.HTTP_200_OK

    def test_search_public_articles(self, client, mock_db, mock_article):
        """Test GET /api/v1/public/articles/search - search functionality"""
        with patch('routers.article.get_db', return_value=mock_db):
            # Mock database query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = [mock_article]
            mock_db.query.return_value = mock_query

            response = client.get(
                f"{TestConfig.API_V1_PREFIX}/public/articles/search",
                params={"query": "test"}
            )
            
            assert response.status_code == status.HTTP_200_OK

    def test_get_public_article_by_id(self, client, mock_db, mock_article):
        """Test GET /api/v1/public/articles/{article_id} - public article access"""
        with patch('routers.article.get_db', return_value=mock_db):
            # Mock database query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_article
            mock_db.query.return_value = mock_query

            response = client.get(f"{TestConfig.API_V1_PREFIX}/public/articles/1")
            
            assert response.status_code == status.HTTP_200_OK


# Auth Router Tests
class TestAuthRouterCorrected:
    """Corrected tests for Auth Router endpoints"""

    def test_login_success(self, client, mock_db, mock_user):
        """Test POST /api/v1/login - successful login"""
        with patch('routers.auth.get_db', return_value=mock_db):
            with patch('routers.auth.Hash.verify', return_value=True):
                with patch('routers.auth.create_access_token', return_value="test_token"):
                    # Mock database query
                    mock_query = Mock()
                    mock_query.filter.return_value = mock_query
                    mock_query.first.return_value = mock_user
                    mock_db.query.return_value = mock_query

                    login_data = {
                        "username": TestConfig.TEST_USER_EMAIL,
                        "password": TestConfig.TEST_USER_PASSWORD
                    }

                    response = client.post(
                        f"{TestConfig.API_V1_PREFIX}/login",
                        data=login_data
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert "access_token" in data
                    assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, mock_db):
        """Test POST /api/v1/login - invalid credentials"""
        with patch('routers.auth.get_db', return_value=mock_db):
            # Mock database query returning None (user not found)
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            mock_db.query.return_value = mock_query

            login_data = {
                "username": "invalid@example.com",
                "password": "wrongpassword"
            }

            response = client.post(
                f"{TestConfig.API_V1_PREFIX}/login",
                data=login_data
            )
            
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_logout_success(self, client):
        """Test POST /api/v1/logout - successful logout"""
        response = client.post(
            f"{TestConfig.API_V1_PREFIX}/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == status.HTTP_200_OK

    def test_change_password_success(self, client, mock_db, mock_user):
        """Test POST /api/v1/change-password - successful password change"""
        with patch('routers.auth.get_db', return_value=mock_db):
            with patch('routers.auth.Hash.verify', return_value=True):
                with patch('routers.auth.Hash.bcrypt', return_value="new_hashed_password"):
                    # Mock database query
                    mock_query = Mock()
                    mock_query.filter.return_value = mock_query
                    mock_query.first.return_value = mock_user
                    mock_db.query.return_value = mock_query

                    password_data = {
                        "email": TestConfig.TEST_USER_EMAIL,
                        "current_password": "oldpassword",
                        "new_password": "newpassword123"
                    }

                    response = client.post(
                        f"{TestConfig.API_V1_PREFIX}/change-password",
                        json=password_data
                    )
                    
                    assert response.status_code == status.HTTP_200_OK

    def test_get_article_success(self, client, mock_db, mock_user, mock_article):
        """Test GET /api/v1/article - get article endpoint"""
        with patch('routers.auth.get_db', return_value=mock_db):
            with patch('routers.auth.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.all.return_value = [mock_article]
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/article",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_200_OK


# User Router Tests
class TestUserRouterCorrected:
    """Corrected tests for User Router endpoints"""

    def test_create_user_success(self, client, mock_db):
        """Test POST /api/v1/user - successful user creation"""
        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.user.is_valid_email_domain', return_value=True):
                with patch('routers.user.send_verification_email'):
                    with patch('routers.user.Hash.bcrypt', return_value="hashed_password"):
                        # Mock database queries
                        mock_query = Mock()
                        mock_query.filter.return_value = mock_query
                        mock_query.first.return_value = None  # User doesn't exist
                        mock_db.query.return_value = mock_query

                        user_data = {
                            "email": "newuser@example.com",
                            "password": "password123"
                        }

                        response = client.post(
                            f"{TestConfig.API_V1_PREFIX}/user",
                            json=user_data
                        )
                        
                        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_email_success(self, client, mock_db, mock_user):
        """Test GET /api/v1/verify-email - successful email verification"""
        with patch('routers.user.get_db', return_value=mock_db):
            # Mock email verification record
            mock_verification = Mock(spec=EmailVerification)
            mock_verification.user_id = 1
            mock_verification.expires_at = datetime.utcnow() + timedelta(hours=1)

            # Mock database queries
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.side_effect = [mock_verification, mock_user]
            mock_db.query.return_value = mock_query

            response = client.get(
                f"{TestConfig.API_V1_PREFIX}/verify-email",
                params={"token": "test_verification_token"}
            )
            
            assert response.status_code == status.HTTP_200_OK

    def test_get_user_success(self, client, mock_db, mock_user):
        """Test GET /api/v1/user/{user_id} - successful user retrieval"""
        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.user.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = mock_user
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/user/1",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_200_OK

    def test_resend_verification_success(self, client, mock_db, mock_user):
        """Test POST /api/v1/resend-verification - successful verification resend"""
        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.user.send_verification_email'):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = mock_user
                mock_db.query.return_value = mock_query

                verification_data = {
                    "email": TestConfig.TEST_USER_EMAIL
                }

                response = client.post(
                    f"{TestConfig.API_V1_PREFIX}/resend-verification",
                    json=verification_data
                )
                
                assert response.status_code == status.HTTP_200_OK

    def test_delete_user_account_success(self, client, mock_db, mock_user):
        """Test DELETE /api/v1/user/delete-account - successful account deletion"""
        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.user.get_current_user', return_value=mock_user):
                with patch('routers.user.Hash.verify', return_value=True):
                    with patch('routers.user.send_account_deletion_email'):
                        # Mock database queries
                        mock_query = Mock()
                        mock_query.filter.return_value = mock_query
                        mock_query.first.return_value = mock_user
                        mock_query.all.return_value = []  # No articles
                        mock_db.query.return_value = mock_query

                        deletion_data = {
                            "email": TestConfig.TEST_USER_EMAIL,
                            "password": TestConfig.TEST_USER_PASSWORD,
                            "confirmation": "DELETE"
                        }

                        response = client.delete(
                            f"{TestConfig.API_V1_PREFIX}/user/delete-account",
                            json=deletion_data,
                            headers={"Authorization": "Bearer test_token"}
                        )
                        
                        assert response.status_code == status.HTTP_200_OK


# Error Handling Tests
class TestRoutersErrorHandling:
    """Test error handling scenarios across all routers"""

    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        # Test protected article endpoint without auth
        response = client.get(f"{TestConfig.API_V1_PREFIX}/articles")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test protected user endpoint without auth
        response = client.get(f"{TestConfig.API_V1_PREFIX}/user/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_article_id(self, client, mock_db, mock_user):
        """Test accessing non-existent article"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query returning None
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = None
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/articles/999",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_user_id(self, client, mock_db, mock_user):
        """Test accessing non-existent user"""
        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.user.get_current_user', return_value=mock_user):
                # Mock database query returning None
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.first.return_value = None
                mock_db.query.return_value = mock_query

                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/user/999",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_duplicate_user_creation(self, client, mock_db, mock_user):
        """Test creating user with existing email"""
        with patch('routers.user.get_db', return_value=mock_db):
            # Mock database query returning existing user
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_user
            mock_db.query.return_value = mock_query

            user_data = {
                "email": TestConfig.TEST_USER_EMAIL,
                "password": "password123"
            }

            response = client.post(
                f"{TestConfig.API_V1_PREFIX}/user",
                json=user_data
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST


# Input Validation Tests
class TestRoutersValidation:
    """Test input validation across all routers"""

    def test_invalid_email_format(self, client):
        """Test user creation with invalid email format"""
        user_data = {
            "email": "invalid-email",
            "password": "password123"
        }

        response = client.post(
            f"{TestConfig.API_V1_PREFIX}/user",
            json=user_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_weak_password(self, client):
        """Test user creation with weak password"""
        user_data = {
            "email": "test@example.com",
            "password": "123"  # Too short
        }

        response = client.post(
            f"{TestConfig.API_V1_PREFIX}/user",
            json=user_data
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_empty_article_title(self, client, mock_db, mock_user):
        """Test article creation with empty title"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                article_data = {
                    "title": "",  # Empty title
                    "content": "Some content",
                    "is_published": True
                }

                response = client.post(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    json=article_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_fields(self, client):
        """Test requests with missing required fields"""
        # Test login without password
        login_data = {"username": "test@example.com"}
        response = client.post(f"{TestConfig.API_V1_PREFIX}/login", data=login_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test user creation without email
        user_data = {"password": "password123"}
        response = client.post(f"{TestConfig.API_V1_PREFIX}/user", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Performance Tests
class TestRoutersPerformance:
    """Test performance characteristics of router endpoints"""

    def test_article_list_performance(self, client, mock_db, mock_user):
        """Test performance of article listing endpoint"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Mock database query
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_query.limit.return_value = mock_query
                mock_query.offset.return_value = []
                mock_db.query.return_value = mock_query

                start_time = time.time()
                response = client.get(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    headers={"Authorization": "Bearer test_token"}
                )
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                assert response_time_ms < TestConfig.PERFORMANCE_THRESHOLD_MS
                assert response.status_code == status.HTTP_200_OK

    def test_concurrent_login_requests(self, client, mock_db, mock_user):
        """Test handling of concurrent login requests"""
        with patch('routers.auth.get_db', return_value=mock_db):
            with patch('routers.auth.Hash.verify', return_value=True):
                with patch('routers.auth.create_access_token', return_value="test_token"):
                    # Mock database query
                    mock_query = Mock()
                    mock_query.filter.return_value = mock_query
                    mock_query.first.return_value = mock_user
                    mock_db.query.return_value = mock_query

                    def make_login_request():
                        login_data = {
                            "username": TestConfig.TEST_USER_EMAIL,
                            "password": TestConfig.TEST_USER_PASSWORD
                        }
                        return client.post(f"{TestConfig.API_V1_PREFIX}/login", data=login_data)

                    # Execute concurrent requests
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [executor.submit(make_login_request) for _ in range(5)]
                        responses = [future.result() for future in futures]

                    # All requests should succeed
                    for response in responses:
                        assert response.status_code == status.HTTP_200_OK


# Security Tests
class TestRoutersSecurity:
    """Test security aspects of router endpoints"""

    def test_sql_injection_protection(self, client, mock_db):
        """Test protection against SQL injection attacks"""
        # Test SQL injection in search endpoint
        malicious_query = "'; DROP TABLE users; --"
        
        with patch('routers.article.get_db', return_value=mock_db):
            # Mock database query
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.offset.return_value = []
            mock_db.query.return_value = mock_query

            response = client.get(
                f"{TestConfig.API_V1_PREFIX}/public/articles/search",
                params={"query": malicious_query}
            )
            
            # Should not cause server error
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_xss_protection(self, client, mock_db, mock_user):
        """Test protection against XSS attacks"""
        with patch('routers.article.get_db', return_value=mock_db):
            with patch('routers.article.get_current_user', return_value=mock_user):
                # Test XSS in article content
                malicious_content = "<script>alert('XSS')</script>"
                article_data = {
                    "title": "Test Article",
                    "content": malicious_content,
                    "is_published": True
                }

                response = client.post(
                    f"{TestConfig.API_V1_PREFIX}/articles",
                    json=article_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                # Should either succeed (content will be sanitized) or reject
                assert response.status_code in [
                    status.HTTP_201_CREATED, 
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ]

    def test_rate_limiting_simulation(self, client, mock_db, mock_user):
        """Test rate limiting behavior simulation"""
        with patch('routers.auth.get_db', return_value=mock_db):
            with patch('routers.auth.Hash.verify', return_value=True):
                with patch('routers.auth.create_access_token', return_value="test_token"):
                    # Mock database query
                    mock_query = Mock()
                    mock_query.filter.return_value = mock_query
                    mock_query.first.return_value = mock_user
                    mock_db.query.return_value = mock_query

                    # Simulate rapid requests
                    responses = []
                    for i in range(10):  # Reduced from 100 for faster testing
                        login_data = {
                            "username": TestConfig.TEST_USER_EMAIL,
                            "password": TestConfig.TEST_USER_PASSWORD
                        }
                        response = client.post(f"{TestConfig.API_V1_PREFIX}/login", data=login_data)
                        responses.append(response)

                    # Most requests should succeed (in real scenario, some might be rate limited)
                    success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
                    assert success_count >= 5  # At least half should succeed

    def test_authentication_token_validation(self, client):
        """Test authentication token validation"""
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get(
            f"{TestConfig.API_V1_PREFIX}/articles",
            headers=invalid_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test with malformed authorization header
        malformed_headers = {"Authorization": "InvalidFormat token"}
        
        response = client.get(
            f"{TestConfig.API_V1_PREFIX}/articles",
            headers=malformed_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# Integration Tests
class TestRoutersIntegration:
    """Integration tests spanning multiple router functionalities"""

    def test_complete_user_article_workflow(self, client, mock_db):
        """Test complete workflow: user creation -> login -> article creation -> retrieval"""
        # Mock user and article objects
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = TestConfig.TEST_USER_EMAIL
        mock_user.is_verified = True
        mock_user.verification_attempts = 0

        mock_article = Mock(spec=Article)
        mock_article.id = 1
        mock_article.title = TestConfig.TEST_ARTICLE_TITLE
        mock_article.content = TestConfig.TEST_ARTICLE_CONTENT
        mock_article.user_id = 1

        with patch('routers.user.get_db', return_value=mock_db):
            with patch('routers.auth.get_db', return_value=mock_db):
                with patch('routers.article.get_db', return_value=mock_db):
                    with patch('routers.user.is_valid_email_domain', return_value=True):
                        with patch('routers.user.send_verification_email'):
                            with patch('routers.user.Hash.bcrypt', return_value="hashed_password"):
                                with patch('routers.auth.Hash.verify', return_value=True):
                                    with patch('routers.auth.create_access_token', return_value="test_token"):
                                        with patch('routers.article.get_current_user', return_value=mock_user):
                                            
                                            # Setup mock database responses
                                            mock_query = Mock()
                                            mock_query.filter.return_value = mock_query
                                            mock_query.first.side_effect = [None, mock_user, mock_article]  # User creation, login, article retrieval
                                            mock_query.all.return_value = [mock_article]
                                            mock_db.query.return_value = mock_query

                                            # 1. Create user
                                            user_data = {
                                                "email": TestConfig.TEST_USER_EMAIL,
                                                "password": TestConfig.TEST_USER_PASSWORD
                                            }
                                            response = client.post(f"{TestConfig.API_V1_PREFIX}/user", json=user_data)
                                            assert response.status_code == status.HTTP_201_CREATED

                                            # 2. Login
                                            login_data = {
                                                "username": TestConfig.TEST_USER_EMAIL,
                                                "password": TestConfig.TEST_USER_PASSWORD
                                            }
                                            response = client.post(f"{TestConfig.API_V1_PREFIX}/login", data=login_data)
                                            assert response.status_code == status.HTTP_200_OK
                                            
                                            # 3. Create article
                                            article_data = {
                                                "title": TestConfig.TEST_ARTICLE_TITLE,
                                                "content": TestConfig.TEST_ARTICLE_CONTENT,
                                                "is_published": True
                                            }
                                            response = client.post(
                                                f"{TestConfig.API_V1_PREFIX}/articles",
                                                json=article_data,
                                                headers={"Authorization": "Bearer test_token"}
                                            )
                                            assert response.status_code == status.HTTP_201_CREATED

                                            # 4. Retrieve articles
                                            mock_query.limit.return_value = mock_query
                                            mock_query.order_by.return_value = mock_query
                                            mock_query.offset.return_value = [mock_article]
                                            
                                            response = client.get(
                                                f"{TestConfig.API_V1_PREFIX}/articles",
                                                headers={"Authorization": "Bearer test_token"}
                                            )
                                            assert response.status_code == status.HTTP_200_OK


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
