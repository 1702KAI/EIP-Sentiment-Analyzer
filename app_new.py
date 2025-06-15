import os
import logging
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
import pandas as pd
from sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sentiment_analyzer.db"

db.init_app(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Define models here to avoid circular imports
class AnalysisJob(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='queued')
    progress = db.Column(db.Integer, default=0)
    stage = db.Column(db.String(255), default='Queued for processing...')
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    output_files = db.relationship('OutputFile', backref='job', lazy=True, cascade='all, delete-orphan')

class OutputFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('analysis_job.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
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
    
    __table_args__ = (db.Index('idx_eip_job', 'eip', 'job_id'),)

# Initialize database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv_background(job_id, filepath, output_dir):
    """Background task to process CSV file through sentiment analysis pipeline"""
    try:
        with app.app_context():
            job = AnalysisJob.query.get(job_id)
            if not job:
                return
            
            job.status = 'processing'
            job.stage = 'Initializing sentiment analyzer...'
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
            analyzer = SentimentAnalyzer()
            
            # Stage 1
            job.stage = 'Stage 1: Running VADER sentiment analysis...'
            job.progress = 10
            db.session.commit()
            
            stage1_output = analyzer.run_stage1(filepath, output_dir)
            job.progress = 33
            db.session.commit()
            
            # Stage 2
            job.stage = 'Stage 2: Fetching EIPs Insight data...'
            db.session.commit()
            
            stage2_output = analyzer.run_stage2(output_dir)
            job.progress = 66
            db.session.commit()
            
            # Stage 3
            job.stage = 'Stage 3: Merging and finalizing data...'
            db.session.commit()
            
            final_output = analyzer.run_stage3(output_dir)
            
            # Save output files to database
            for file_path in final_output:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    file_type = 'unknown'
                    if 'final_merged' in filename:
                        file_type = 'final_analysis'
                    elif 'summary' in filename:
                        file_type = 'summary'
                    elif 'enriched' in filename:
                        file_type = 'enriched'
                    
                    output_file = OutputFile(
                        job_id=job_id,
                        filename=filename,
                        file_path=file_path,
                        file_type=file_type,
                        file_size=os.path.getsize(file_path)
                    )
                    db.session.add(output_file)
            
            # Save sentiment data if final merged file exists
            final_file = next((f for f in final_output if 'final_merged' in f), None)
            if final_file and os.path.exists(final_file):
                try:
                    df = pd.read_csv(final_file)
                    for _, row in df.iterrows():
                        sentiment = EIPSentiment(
                            job_id=job_id,
                            eip=str(row.get('eip', '')),
                            unified_compound=row.get('unified_compound'),
                            unified_pos=row.get('unified_pos'),
                            unified_neg=row.get('unified_neg'),
                            unified_neu=row.get('unified_neu'),
                            total_comment_count=row.get('total_comment_count'),
                            category=row.get('category'),
                            status=row.get('status'),
                            title=row.get('title'),
                            author=row.get('author')
                        )
                        db.session.add(sentiment)
                except Exception as e:
                    logging.warning(f"Could not save sentiment data: {e}")
            
            # Complete the job
            job.status = 'completed'
            job.stage = 'Analysis completed successfully!'
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            db.session.commit()
            
    except Exception as e:
        logging.error(f"Error processing job {job_id}: {str(e)}")
        with app.app_context():
            job = AnalysisJob.query.get(job_id)
            if job:
                job.status = 'error'
                job.error_message = str(e)
                job.updated_at = datetime.utcnow()
                db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(str(file.filename))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Validate CSV structure
        try:
            df = pd.read_csv(filepath)
            required_columns = ['paragraphs', 'headings', 'unordered_lists', 'topic']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                flash(f'CSV missing required columns: {", ".join(missing_columns)}', 'error')
                os.remove(filepath)
                return redirect(request.url)
        except Exception as e:
            flash(f'Error reading CSV file: {str(e)}', 'error')
            os.remove(filepath)
            return redirect(request.url)
        
        # Create job in database
        job_id = str(uuid.uuid4())
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        job = AnalysisJob(
            id=job_id,
            filename=unique_filename,
            original_filename=file.filename,
            status='queued',
            progress=0,
            stage='Queued for processing...'
        )
        db.session.add(job)
        db.session.commit()
        
        # Start background processing
        thread = threading.Thread(target=process_csv_background, args=(job_id, filepath, output_dir))
        thread.daemon = True
        thread.start()
        
        flash('File uploaded successfully! Processing started.', 'success')
        return redirect(url_for('job_status', job_id=job_id))
    
    flash('Invalid file type. Please upload a CSV file.', 'error')
    return redirect(request.url)

@app.route('/job/<job_id>')
def job_status(job_id):
    job = AnalysisJob.query.get(job_id)
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('results.html', job_id=job_id, job=job)

@app.route('/api/job/<job_id>/status')
def api_job_status(job_id):
    job = AnalysisJob.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'status': job.status,
        'progress': job.progress,
        'stage': job.stage,
        'error': job.error_message,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None
    })

@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    job = AnalysisJob.query.get(job_id)
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    output_file = OutputFile.query.filter_by(job_id=job_id, filename=filename).first()
    if not output_file or not os.path.exists(output_file.file_path):
        flash('File not found', 'error')
        return redirect(url_for('job_status', job_id=job_id))
    
    return send_file(output_file.file_path, as_attachment=True)

@app.route('/results')
def results():
    # Show all completed jobs
    completed_jobs = AnalysisJob.query.filter_by(status='completed').order_by(AnalysisJob.completed_at.desc()).all()
    return render_template('results.html', jobs=completed_jobs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)