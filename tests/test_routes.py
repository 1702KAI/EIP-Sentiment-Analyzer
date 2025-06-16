"""
Route and endpoint tests for EIP Sentiment Analyzer
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from io import BytesIO


class TestPublicRoutes:
    """Test publicly accessible routes"""
    
    def test_homepage_loads(self, client):
        """Test homepage loads with correct content"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'EIP Sentiment Analyzer' in response.data
        assert b'Smart Contract Generator' in response.data
        assert b'Dashboard' in response.data
    
    def test_smart_contract_page_loads(self, client):
        """Test smart contract generator page loads"""
        response = client.get('/smart-contract')
        assert response.status_code == 200
        assert b'Smart Contract Generator' in response.data
        # Check for contract generation functionality
        assert b'Generate' in response.data or b'Smart Contract' in response.data
    
    def test_dashboard_loads(self, client):
        """Test dashboard page loads"""
        response = client.get('/dashboard')
        assert response.status_code == 200
        # Dashboard should be accessible even without data
    
    def test_login_page_loads(self, client):
        """Test login page loads correctly"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Admin Login' in response.data


class TestFileUpload:
    """Test CSV file upload functionality"""
    
    def test_upload_without_login_redirects(self, client):
        """Test upload page redirects without authentication"""
        response = client.get('/upload')
        assert response.status_code == 302 or response.status_code == 200
        # Should redirect to login or show login form
    
    def test_upload_with_valid_csv(self, client, test_app, sample_csv_file):
        """Test successful CSV upload with admin user"""
        with test_app.app_context():
            from app import db
            from models import User
            
            # Create admin user within test context
            admin = User()
            admin.id = 'test-admin-csv'
            admin.email = 'admin@csv.test'
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            
            with client.session_transaction() as sess:
                sess['_user_id'] = admin.id
                sess['_fresh'] = True
            
            data = {
                'file': (sample_csv_file, 'test.csv')
            }
            
            response = client.post('/upload', data=data, follow_redirects=True)
            assert response.status_code == 200
    
    def test_upload_without_file(self, client, admin_user):
        """Test upload without selecting a file"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.post('/upload', data={}, follow_redirects=True)
        assert response.status_code == 200
        assert b'No file selected' in response.data
    
    def test_upload_invalid_file_type(self, client, admin_user):
        """Test upload with invalid file type"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        data = {
            'file': (BytesIO(b'invalid content'), 'test.txt')
        }
        
        response = client.post('/upload', data=data, follow_redirects=True)
        assert response.status_code == 200


class TestAPIEndpoints:
    """Test API endpoints for AJAX requests"""
    
    @patch('app.EIPCodeGenerator')
    def test_generate_contract_api(self, mock_generator, client):
        """Test smart contract generation API"""
        mock_instance = MagicMock()
        mock_instance.generate_eip_implementation.return_value = {
            'success': True,
            'contract_code': 'contract TestContract {}'
        }
        mock_generator.return_value = mock_instance
        
        data = {
            'eip_number': '20',
            'contract_type': 'ERC20',
            'contract_name': 'TestToken'
        }
        
        response = client.post('/api/generate-contract', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    @patch('app.EIPCodeGenerator')
    def test_analyze_security_api(self, mock_generator, client):
        """Test security analysis API"""
        mock_instance = MagicMock()
        mock_instance.analyze_contract_security.return_value = {
            'success': True,
            'analysis': 'Security analysis results'
        }
        mock_generator.return_value = mock_instance
        
        data = {
            'contract_code': 'contract TestContract {}'
        }
        
        response = client.post('/api/analyze-security',
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
    
    def test_job_status_api(self, client, analysis_job):
        """Test job status API endpoint"""
        response = client.get(f'/api/job-status/{analysis_job.id}')
        assert response.status_code == 200
        
        response_data = json.loads(response.data)
        assert 'status' in response_data
        assert response_data['job_id'] == analysis_job.id
    
    def test_job_status_invalid_id(self, client):
        """Test job status API with invalid job ID"""
        response = client.get('/api/job-status/invalid-id')
        assert response.status_code == 404


class TestDashboardData:
    """Test dashboard data endpoints"""
    
    def test_dashboard_with_data(self, client, eip_sentiment_data, analysis_job):
        """Test dashboard loads with sentiment data"""
        response = client.get(f'/dashboard?job_id={analysis_job.id}')
        assert response.status_code == 200
        assert b'EIP Sentiment Analysis' in response.data or b'dashboard' in response.data.lower()
    
    def test_export_dashboard_data(self, client, admin_user, eip_sentiment_data, analysis_job):
        """Test dashboard data export"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.get(f'/export-dashboard/{analysis_job.id}')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_handling(self, client):
        """Test 404 error handling for non-existent routes"""
        response = client.get('/non-existent-route')
        assert response.status_code == 404
    
    def test_invalid_job_id_download(self, client, admin_user):
        """Test download with invalid job ID"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
            sess['_fresh'] = True
        
        response = client.get('/download/invalid-job/file.csv')
        assert response.status_code == 302 or response.status_code == 404
    
    def test_api_without_json_data(self, client):
        """Test API endpoints without JSON data"""
        response = client.post('/api/generate-contract')
        assert response.status_code == 400 or response.status_code == 500
    
    def test_api_with_invalid_json(self, client):
        """Test API endpoints with invalid JSON"""
        response = client.post('/api/generate-contract',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400 or response.status_code == 500