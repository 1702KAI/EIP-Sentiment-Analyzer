import os
import logging
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
from sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

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

# Global dictionary to track processing jobs
processing_jobs = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv_background(job_id, filepath, output_dir):
    """Background task to process CSV file through sentiment analysis pipeline"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['stage'] = 'Initializing sentiment analyzer...'
        
        analyzer = SentimentAnalyzer()
        
        processing_jobs[job_id]['stage'] = 'Stage 1: Running VADER sentiment analysis...'
        stage1_output = analyzer.run_stage1(filepath, output_dir)
        processing_jobs[job_id]['progress'] = 33
        
        processing_jobs[job_id]['stage'] = 'Stage 2: Fetching EIPs Insight data...'
        stage2_output = analyzer.run_stage2(output_dir)
        processing_jobs[job_id]['progress'] = 66
        
        processing_jobs[job_id]['stage'] = 'Stage 3: Merging and finalizing data...'
        final_output = analyzer.run_stage3(output_dir)
        processing_jobs[job_id]['progress'] = 100
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['stage'] = 'Analysis completed successfully!'
        processing_jobs[job_id]['output_files'] = final_output
        
    except Exception as e:
        logging.error(f"Error processing job {job_id}: {str(e)}")
        processing_jobs[job_id]['status'] = 'error'
        processing_jobs[job_id]['error'] = str(e)

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
        
        # Create job
        job_id = str(uuid.uuid4())
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        processing_jobs[job_id] = {
            'status': 'queued',
            'filename': unique_filename,
            'created_at': datetime.now(),
            'progress': 0,
            'stage': 'Queued for processing...',
            'output_files': []
        }
        
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
    if job_id not in processing_jobs:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    job = processing_jobs[job_id]
    return render_template('results.html', job_id=job_id, job=job)

@app.route('/api/job/<job_id>/status')
def api_job_status(job_id):
    if job_id not in processing_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(processing_jobs[job_id])

@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    if job_id not in processing_jobs:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], job_id, filename)
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('job_status', job_id=job_id))
    
    return send_file(file_path, as_attachment=True)

@app.route('/results')
def results():
    # Show all completed jobs
    completed_jobs = {k: v for k, v in processing_jobs.items() if v['status'] == 'completed'}
    return render_template('results.html', jobs=completed_jobs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
