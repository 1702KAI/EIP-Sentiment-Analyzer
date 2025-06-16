"""
Authentication and authorization tests for EIP Sentiment Analyzer
"""

import pytest
from flask import url_for
from app import app, db
from models import User


class TestAuthentication:
    """Test authentication functionality"""
    
    def test_login_page_accessible(self, client):
        """Test that login page loads correctly"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data
    
    def test_valid_admin_login(self, client, test_app):
        """Test successful admin login with valid credentials"""
        response = client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Logged in successfully!' in response.data
    
    def test_invalid_login_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/login', data={
            'email': 'invalid@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    def test_logout_functionality(self, client, test_app):
        """Test user logout functionality"""
        # First login
        client.post('/login', data={
            'email': 'admin@example.com',
            'password': 'admin123'
        })
        
        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Logged out successfully' in response.data


class TestAuthorization:
    """Test authorization and access control"""
    
    def test_upload_page_requires_admin(self, client):
        """Test that upload page requires admin authentication"""
        response = client.get('/upload', follow_redirects=True)
        assert response.status_code == 200
        assert b'Please log in' in response.data or b'Admin Login' in response.data
    
    def test_results_page_requires_admin(self, client):
        """Test that results page requires admin authentication"""
        response = client.get('/results', follow_redirects=True)
        assert response.status_code == 200
        assert b'Please log in' in response.data or b'Admin Login' in response.data
    
    def test_admin_can_access_upload(self, client, test_app):
        """Test that authenticated admin can access upload page"""
        with test_app.app_context():
            # Create admin user within the test context
            admin = User()
            admin.id = 'test-admin-upload'
            admin.email = 'admin@upload.test'
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = admin.id
                sess['_fresh'] = True
            
            response = client.get('/upload')
            assert response.status_code == 200
            assert b'Upload CSV' in response.data
    
    def test_admin_can_access_results(self, client, test_app):
        """Test that authenticated admin can access results page"""
        with test_app.app_context():
            # Create admin user within the test context
            admin = User()
            admin.id = 'test-admin-results'
            admin.email = 'admin@results.test'
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = admin.id
                sess['_fresh'] = True
            
            response = client.get('/results')
            assert response.status_code == 200
            assert b'Analysis Results' in response.data or b'completed jobs' in response.data
    
    def test_public_can_access_homepage(self, client):
        """Test that homepage is publicly accessible"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'EIP Sentiment Analyzer' in response.data
    
    def test_public_can_access_smart_contracts(self, client):
        """Test that smart contract generator is publicly accessible"""
        response = client.get('/smart-contract')
        assert response.status_code == 200
        assert b'Smart Contract Generator' in response.data
    
    def test_public_can_access_dashboard(self, client):
        """Test that dashboard is publicly accessible"""
        response = client.get('/dashboard')
        assert response.status_code == 200
        # Dashboard might redirect or show empty state, but should be accessible