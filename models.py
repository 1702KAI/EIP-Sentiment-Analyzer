from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Text, JSON

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class AnalysisJob(db.Model):
    id = db.Column(db.String(36), primary_key=True)  # UUID
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='queued')  # queued, processing, completed, error
    progress = db.Column(db.Integer, default=0)
    stage = db.Column(db.String(255), default='Queued for processing...')
    error_message = db.Column(Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    output_files = db.relationship('OutputFile', backref='job', lazy=True, cascade='all, delete-orphan')

class OutputFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('analysis_job.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))  # enriched, summary, transitions, etc.
    file_size = db.Column(db.Integer)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EIPSentiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('analysis_job.id'), nullable=False)
    eip = db.Column(db.String(10), nullable=False)
    unified_compound = db.Column(db.Float)
    unified_pos = db.Column(db.Float)
    unified_neg = db.Column(db.Float)
    unified_neu = db.Column(db.Float)
    total_comment_count = db.Column(db.Integer)
    category = db.Column(db.String(100))
    status = db.Column(db.String(50))
    title = db.Column(db.String(500))
    author = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for faster queries
    __table_args__ = (
        db.Index('idx_eip_job', 'eip', 'job_id'),
    )