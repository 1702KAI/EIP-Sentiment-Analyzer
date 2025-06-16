"""
Pytest configuration and fixtures for EIP Sentiment Analyzer tests
"""

import pytest
import tempfile
import os
from app import app, db
from models import User, AnalysisJob, EIPSentiment, OutputFile
from werkzeug.datastructures import FileStorage
from io import BytesIO

@pytest.fixture
def test_app():
    """Create a test Flask application instance"""
    # Create a temporary database
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture
def client(test_app):
    """Create a test client"""
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    """Create a test CLI runner"""
    return test_app.test_cli_runner()

@pytest.fixture
def admin_user(test_app):
    """Create an admin user for testing"""
    with test_app.app_context():
        admin = User()
        admin.id = 'test-admin-123'
        admin.email = 'admin@test.com'
        admin.first_name = 'Test'
        admin.last_name = 'Admin'
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        
        # Detach from session to avoid DetachedInstanceError
        db.session.expunge(admin)
        return admin

@pytest.fixture
def regular_user(test_app):
    """Create a regular user for testing"""
    with test_app.app_context():
        user = User()
        user.id = 'test-user-456'
        user.email = 'user@test.com'
        user.first_name = 'Test'
        user.last_name = 'User'
        user.is_admin = False
        db.session.add(user)
        db.session.commit()
        
        # Detach from session to avoid DetachedInstanceError
        db.session.expunge(user)
        return user

@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing uploads"""
    csv_content = """paragraphs,headings,unordered_lists,topic,compound,pos,neu,neg
"Test paragraph about EIP-1","EIP-1 Heading","- Item 1","eip-1",0.5,0.7,0.2,0.1
"Another paragraph about ERC-20","ERC-20 Token","- Feature 1","erc-20",0.3,0.6,0.3,0.1
"Discussion about EIP-721","NFT Standard","- Property 1","eip-721",-0.2,0.4,0.5,0.1
"""
    return BytesIO(csv_content.encode('utf-8'))

@pytest.fixture
def analysis_job(test_app):
    """Create a sample analysis job for testing"""
    with test_app.app_context():
        job = AnalysisJob()
        job.id = 'test-job-789'
        job.filename = 'test.csv'
        job.original_filename = 'test_upload.csv'
        job.status = 'completed'
        job.progress = 100
        db.session.add(job)
        db.session.commit()
        
        # Detach from session to avoid DetachedInstanceError
        db.session.expunge(job)
        return job

@pytest.fixture
def eip_sentiment_data(test_app, analysis_job):
    """Create sample EIP sentiment data for testing"""
    with test_app.app_context():
        sentiment_data = []
        
        # Create EIP sentiment records using the provided analysis_job
        eip1 = EIPSentiment()
        eip1.job_id = analysis_job.id
        eip1.eip = '1'
        eip1.unified_compound = 0.5
        eip1.unified_pos = 0.7
        eip1.unified_neg = 0.1
        eip1.unified_neu = 0.2
        eip1.total_comment_count = 100
        eip1.category = 'Core'
        eip1.status = 'Final'
        eip1.title = 'EIP-1: EIP Purpose and Guidelines'
        eip1.author = 'Martin Becze, Hudson Jameson'
        sentiment_data.append(eip1)
        
        eip20 = EIPSentiment()
        eip20.job_id = job.id
        eip20.eip = '20'
        eip20.unified_compound = 0.3
        eip20.unified_pos = 0.6
        eip20.unified_neg = 0.2
        eip20.unified_neu = 0.2
        eip20.total_comment_count = 250
        eip20.category = 'ERC'
        eip20.status = 'Final'
        eip20.title = 'EIP-20: Token Standard'
        eip20.author = 'Fabian Vogelsteller, Vitalik Buterin'
        sentiment_data.append(eip20)
        
        eip721 = EIPSentiment()
        eip721.job_id = job.id
        eip721.eip = '721'
        eip721.unified_compound = -0.1
        eip721.unified_pos = 0.4
        eip721.unified_neg = 0.4
        eip721.unified_neu = 0.2
        eip721.total_comment_count = 180
        eip721.category = 'ERC'
        eip721.status = 'Final'
        eip721.title = 'EIP-721: Non-Fungible Token Standard'
        eip721.author = 'William Entriken'
        sentiment_data.append(eip721)
        
        for sentiment in sentiment_data:
            db.session.add(sentiment)
        db.session.commit()
        return sentiment_data