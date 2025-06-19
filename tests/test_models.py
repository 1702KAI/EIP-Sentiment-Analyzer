"""
Database model tests for EIP Sentiment Analyzer
"""

import pytest
from datetime import datetime
from app import app, db
from models import User, AnalysisJob, EIPSentiment, OutputFile


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, test_app):
        """Test creating a new user"""
        with test_app.app_context():
            user = User()
            user.id = 'test-123'
            user.email = 'test@example.com'
            user.first_name = 'Test'
            user.last_name = 'User'
            user.is_admin = False
            
            db.session.add(user)
            db.session.commit()
            
            retrieved_user = User.query.get('test-123')
            assert retrieved_user is not None
            assert retrieved_user.email == 'test@example.com'
            assert retrieved_user.is_admin is False
    
    def test_admin_user_creation(self, test_app):
        """Test creating an admin user"""
        with test_app.app_context():
            admin = User()
            admin.id = 'admin-456'
            admin.email = 'admin@example.com'
            admin.is_admin = True
            
            db.session.add(admin)
            db.session.commit()
            
            retrieved_admin = User.query.get('admin-456')
            assert retrieved_admin.is_admin is True
    
    def test_user_string_representation(self, test_app, admin_user):
        """Test user string representation"""
        with test_app.app_context():
            db.session.add(admin_user)
            user_str = str(admin_user)
            assert admin_user.email in user_str or admin_user.id in user_str


class TestAnalysisJobModel:
    """Test AnalysisJob model functionality"""
    
    def test_job_creation(self, test_app):
        """Test creating a new analysis job"""
        with test_app.app_context():
            job = AnalysisJob()
            job.id = 'job-789'
            job.filename = 'test.csv'
            job.original_filename = 'original.csv'
            job.status = 'queued'
            
            db.session.add(job)
            db.session.commit()
            
            retrieved_job = AnalysisJob.query.get('job-789')
            assert retrieved_job is not None
            assert retrieved_job.status == 'queued'
            assert retrieved_job.filename == 'test.csv'
    
    def test_job_status_updates(self, test_app):
        """Test updating job status"""
        with test_app.app_context():
            job = AnalysisJob()
            job.id = 'job-update-test'
            job.filename = 'test.csv'
            job.original_filename = 'test.csv'
            job.status = 'queued'
            
            db.session.add(job)
            db.session.commit()
            
            # Update status
            job.status = 'processing'
            job.progress = 50
            job.stage = 'Processing data...'
            db.session.commit()
            
            updated_job = AnalysisJob.query.get('job-update-test')
            assert updated_job.status == 'processing'
            assert updated_job.progress == 50
    
    def test_job_completion(self, test_app):
        """Test marking job as completed"""
        with test_app.app_context():
            job = AnalysisJob()
            job.id = 'job-complete-test'
            job.filename = 'test.csv'
            job.original_filename = 'test.csv'
            job.status = 'processing'
            
            db.session.add(job)
            db.session.commit()
            
            # Mark as completed
            job.status = 'completed'
            job.progress = 100
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            completed_job = AnalysisJob.query.get('job-complete-test')
            assert completed_job.status == 'completed'
            assert completed_job.completed_at is not None


class TestEIPSentimentModel:
    """Test EIPSentiment model functionality"""
    
    def test_eip_sentiment_creation(self, test_app, analysis_job):
        """Test creating EIP sentiment data"""
        with test_app.app_context():
            db.session.add(analysis_job)
            job_id = analysis_job.id
            
            sentiment = EIPSentiment()
            sentiment.job_id = job_id
            sentiment.eip = '20'
            sentiment.unified_compound = 0.5
            sentiment.unified_pos = 0.7
            sentiment.unified_neg = 0.1
            sentiment.unified_neu = 0.2
            sentiment.total_comment_count = 150
            sentiment.category = 'ERC'
            sentiment.status = 'Final'
            sentiment.title = 'EIP-20: Token Standard'
            sentiment.author = 'Test Author'
            
            db.session.add(sentiment)
            db.session.commit()
            
            retrieved_sentiment = EIPSentiment.query.filter_by(
                job_id=analysis_job.id, eip='20'
            ).first()
            
            assert retrieved_sentiment is not None
            assert retrieved_sentiment.unified_compound == 0.5
            assert retrieved_sentiment.category == 'ERC'
    
    def test_eip_sentiment_filtering(self, test_app, eip_sentiment_data, analysis_job):
        """Test filtering EIP sentiment data"""
        with test_app.app_context():
            db.session.add(analysis_job)
            for item in eip_sentiment_data:
                db.session.add(item)
            db.session.commit()
            job_id = analysis_job.id
            
            # Filter by status
            final_eips = EIPSentiment.query.filter_by(
                job_id=job_id, status='Final'
            ).all()
            
            assert len(final_eips) == 3  # All test data is Final status
            
            # Filter by category
            erc_eips = EIPSentiment.query.filter_by(
                job_id=job_id, category='ERC'
            ).all()
            
            assert len(erc_eips) == 2  # EIP-20 and EIP-721
    
    def test_negative_sentiment_filtering(self, test_app, eip_sentiment_data, analysis_job):
        """Test filtering EIPs with negative sentiment"""
        with test_app.app_context():
            db.session.add(analysis_job)
            for item in eip_sentiment_data:
                db.session.add(item)
            db.session.commit()
            job_id = analysis_job.id
            
            negative_eips = EIPSentiment.query.filter(
                EIPSentiment.job_id == job_id,
                EIPSentiment.unified_compound < 0
            ).all()
            
            assert len(negative_eips) == 1  # Only EIP-721 has negative sentiment


class TestOutputFileModel:
    """Test OutputFile model functionality"""
    
    def test_output_file_creation(self, test_app, analysis_job):
        """Test creating output file records"""
        with test_app.app_context():
            db.session.add(analysis_job)
            job_id = analysis_job.id
            
            output_file = OutputFile()
            output_file.job_id = job_id
            output_file.filename = 'stage1_output.csv'
            output_file.file_path = '/path/to/stage1_output.csv'
            output_file.file_type = 'csv'
            output_file.file_size = 1024
            
            db.session.add(output_file)
            db.session.commit()
            
            retrieved_file = OutputFile.query.filter_by(
                job_id=job_id,
                filename='stage1_output.csv'
            ).first()
            
            assert retrieved_file is not None
            assert retrieved_file.file_size == 1024
            assert retrieved_file.file_type == 'csv'
    
    def test_job_output_relationship(self, test_app, analysis_job):
        """Test relationship between jobs and output files"""
        with test_app.app_context():
            db.session.add(analysis_job)
            job_id = analysis_job.id
            
            # Create multiple output files for the job
            for i in range(3):
                output_file = OutputFile()
                output_file.job_id = job_id
                output_file.filename = f'output_{i}.csv'
                output_file.file_path = f'/path/to/output_{i}.csv'
                output_file.file_type = 'csv'
                
                db.session.add(output_file)
            
            db.session.commit()
            
            # Test relationship
            job = AnalysisJob.query.get(job_id)
            assert len(job.output_files) == 3
            
            # Test cascading delete
            db.session.delete(job)
            db.session.commit()
            
            remaining_files = OutputFile.query.filter_by(job_id=job_id).all()
            assert len(remaining_files) == 0  # Should be deleted due to cascade


class TestModelValidation:
    """Test model validation and constraints"""
    
    def test_unique_user_email(self, test_app):
        """Test unique email constraint for users"""
        with test_app.app_context():
            user1 = User()
            user1.id = 'user1'
            user1.email = 'duplicate@example.com'
            
            user2 = User()
            user2.id = 'user2'
            user2.email = 'duplicate@example.com'
            
            db.session.add(user1)
            db.session.commit()
            
            db.session.add(user2)
            
            # This should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()
    
    def test_eip_job_index(self, test_app, analysis_job):
        """Test EIP-job compound index functionality"""
        with test_app.app_context():
            db.session.add(analysis_job)
            job_id = analysis_job.id
            
            # Create two sentiment records for same EIP in same job
            sentiment1 = EIPSentiment()
            sentiment1.job_id = job_id
            sentiment1.eip = '1559'
            sentiment1.unified_compound = 0.3
            
            sentiment2 = EIPSentiment()
            sentiment2.job_id = job_id
            sentiment2.eip = '1559'
            sentiment2.unified_compound = 0.5
            
            db.session.add(sentiment1)
            db.session.add(sentiment2)
            db.session.commit()
            
            # Both should be added (no unique constraint on eip+job)
            eip_records = EIPSentiment.query.filter_by(
                job_id=analysis_job.id, eip='1559'
            ).all()
            
            assert len(eip_records) == 2