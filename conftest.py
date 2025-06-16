"""
Pytest configuration and fixtures for EIP Sentiment Analyzer tests
"""

import pytest
import tempfile
import os
from app import app, db, User, AnalysisJob, EIPSentiment, OutputFile
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
        admin = User(
            id='test-admin-123',
            email='admin@test.com',
            first_name='Test',
            last_name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        return admin

@pytest.fixture
def regular_user(test_app):
    """Create a regular user for testing"""
    with test_app.app_context():
        user = User(
            id='test-user-456',
            email='user@test.com',
            first_name='Test',
            last_name='User',
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
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
        job = AnalysisJob(
            id='test-job-789',
            filename='test.csv',
            original_filename='test_upload.csv',
            status='completed'
        )
        db.session.add(job)
        db.session.commit()
        return job

@pytest.fixture
def eip_sentiment_data(test_app, analysis_job):
    """Create sample EIP sentiment data for testing"""
    with test_app.app_context():
        sentiment_data = [
            EIPSentiment(
                job_id=analysis_job.id,
                eip='1',
                unified_compound=0.5,
                unified_pos=0.7,
                unified_neg=0.1,
                unified_neu=0.2,
                total_comment_count=100,
                category='Core',
                status='Final',
                title='EIP-1: EIP Purpose and Guidelines',
                author='Martin Becze, Hudson Jameson'
            ),
            EIPSentiment(
                job_id=analysis_job.id,
                eip='20',
                unified_compound=0.3,
                unified_pos=0.6,
                unified_neg=0.2,
                unified_neu=0.2,
                total_comment_count=250,
                category='ERC',
                status='Final',
                title='EIP-20: Token Standard',
                author='Fabian Vogelsteller, Vitalik Buterin'
            ),
            EIPSentiment(
                job_id=analysis_job.id,
                eip='721',
                unified_compound=-0.1,
                unified_pos=0.4,
                unified_neg=0.4,
                unified_neu=0.2,
                total_comment_count=180,
                category='ERC',
                status='Final',
                title='EIP-721: Non-Fungible Token Standard',
                author='William Entriken'
            )
        ]
        
        for sentiment in sentiment_data:
            db.session.add(sentiment)
        db.session.commit()
        return sentiment_data