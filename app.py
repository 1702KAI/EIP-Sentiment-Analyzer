import os
import logging
import uuid
import threading
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
import pandas as pd
from sentiment_analyzer import SentimentAnalyzer
from smart_contract_generator import EIPCodeGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

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

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, user_id)

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            flash('Admin access required for this feature.', 'error')
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function

# Initialize database tables after app configuration
with app.app_context():
    from models import User, AnalysisJob, OutputFile, EIPSentiment
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_csv_background(job_id, filepath, output_dir):
    """Background task to process CSV file through sentiment analysis pipeline"""
    
    try:
        with app.app_context():
            from models import AnalysisJob, OutputFile, EIPSentiment
            # Update job status to processing
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
                    
                    output_file = OutputFile()
                    output_file.job_id = job_id
                    output_file.filename = filename
                    output_file.file_path = file_path
                    output_file.file_type = file_type
                    output_file.file_size = os.path.getsize(file_path)
                    db.session.add(output_file)
            
            # Save sentiment data if final merged file exists
            final_file = next((f for f in final_output if 'final_merged' in f), None)
            if final_file and os.path.exists(final_file):
                try:
                    df = pd.read_csv(final_file)
                    
                    # Handle numeric fields with proper type conversion
                    def safe_float(val):
                        if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                            return None
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            return None
                    
                    def safe_int(val):
                        if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                            return None
                        try:
                            return int(float(val))
                        except (ValueError, TypeError):
                            return None
                    
                    def safe_str(val):
                        if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'none', 'null']:
                            return None
                        return str(val).strip()
                    
                    # Process in batches to avoid bulk insert issues
                    batch_size = 100
                    batch_count = 0
                    
                    for _, row in df.iterrows():
                        # Skip rows with invalid or missing EIP values
                        eip_val = row.get('eip', '')
                        try:
                            if eip_val is None or str(eip_val).strip() == '' or str(eip_val).lower() == 'nan':
                                continue
                        except:
                            continue
                            
                        sentiment = EIPSentiment()
                        sentiment.job_id = job_id
                        sentiment.eip = str(eip_val).strip()
                        sentiment.unified_compound = safe_float(row.get('unified_compound'))
                        sentiment.unified_pos = safe_float(row.get('unified_pos'))
                        sentiment.unified_neg = safe_float(row.get('unified_neg'))
                        sentiment.unified_neu = safe_float(row.get('unified_neu'))
                        sentiment.total_comment_count = safe_int(row.get('total_comment_count'))
                        sentiment.category = safe_str(row.get('category_y'))
                        sentiment.status = safe_str(row.get('status'))
                        sentiment.title = safe_str(row.get('title'))
                        sentiment.author = safe_str(row.get('author'))
                        
                        db.session.add(sentiment)
                        batch_count += 1
                        
                        # Commit in batches
                        if batch_count >= batch_size:
                            try:
                                db.session.commit()
                                batch_count = 0
                            except Exception as batch_error:
                                logging.warning(f"Batch commit error: {batch_error}")
                                db.session.rollback()
                                batch_count = 0
                    
                    # Commit any remaining records
                    if batch_count > 0:
                        try:
                            db.session.commit()
                        except Exception as final_error:
                            logging.warning(f"Final batch commit error: {final_error}")
                            db.session.rollback()
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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Simple admin authentication - you can replace this with your preferred method
    admin_credentials = {
        'admin@example.com': 'admin123',
        'admin@sentiment.com': 'password123'
    }
    
    if email in admin_credentials and admin_credentials[email] == password:
        # Create or get user
        from models import User
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('upload_page'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/upload')
@require_admin
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
@require_admin
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
        from models import AnalysisJob
        job_id = str(uuid.uuid4())
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        os.makedirs(output_dir, exist_ok=True)
        
        job = AnalysisJob()
        job.id = job_id
        job.filename = unique_filename
        job.original_filename = file.filename
        job.status = 'queued'
        job.progress = 0
        job.stage = 'Queued for processing...'
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
    from models import AnalysisJob
    job = AnalysisJob.query.get(job_id)
    if not job:
        flash('Job not found', 'error')
        return redirect(url_for('index'))
    
    return render_template('results.html', job_id=job_id, job=job)

@app.route('/api/job/<job_id>/status')
def api_job_status(job_id):
    from models import AnalysisJob
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
    from models import AnalysisJob, OutputFile
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
@require_admin
def results():
    from models import AnalysisJob
    # Show all completed jobs
    completed_jobs = AnalysisJob.query.filter_by(status='completed').order_by(AnalysisJob.created_at.desc()).all()
    return render_template('results.html', jobs=completed_jobs)

@app.route('/dashboard')
def dashboard():
    """Dashboard with sentiment analysis visualizations"""
    from models import AnalysisJob, EIPSentiment
    # Get all completed jobs for selection
    jobs = AnalysisJob.query.filter_by(status='completed').order_by(AnalysisJob.created_at.desc()).all()
    
    # Get selected job ID from query parameter
    selected_job_id = request.args.get('job_id')
    
    # If no job selected, use the most recent one
    if not selected_job_id and jobs:
        selected_job_id = jobs[0].id
    
    sentiment_data = []
    dashboard_stats = {}
    
    if selected_job_id:
        # Get sentiment data for the selected job
        sentiment_data = EIPSentiment.query.filter_by(job_id=selected_job_id).all()
        
        if sentiment_data:
            # Calculate dashboard statistics
            total_eips = len(sentiment_data)
            
            # Count sentiment categories
            positive_sentiment = sum(1 for s in sentiment_data if s.unified_compound and s.unified_compound > 0.1)
            negative_sentiment = sum(1 for s in sentiment_data if s.unified_compound and s.unified_compound < -0.1)
            neutral_sentiment = total_eips - positive_sentiment - negative_sentiment
            
            # Category distribution
            categories = {}
            for s in sentiment_data:
                cat = s.category or 'Unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            category_labels = list(categories.keys())
            category_counts = list(categories.values())
            
            # Status distribution
            statuses = {}
            for s in sentiment_data:
                status = s.status or 'Unknown'
                statuses[status] = statuses.get(status, 0) + 1
            
            status_labels = list(statuses.keys())
            status_counts = list(statuses.values())
            
            # Sentiment score histogram
            valid_scores = [s.unified_compound for s in sentiment_data if s.unified_compound is not None]
            
            if valid_scores:
                import numpy as np
                # Create bins for histogram
                bins = np.linspace(-1, 1, 11)  # 10 bins from -1 to 1
                hist, bin_edges = np.histogram(valid_scores, bins=bins)
                
                # Create bin labels
                sentiment_bins = []
                for i in range(len(bin_edges)-1):
                    sentiment_bins.append(f"{bin_edges[i]:.1f} to {bin_edges[i+1]:.1f}")
                
                sentiment_hist = hist.tolist()
            else:
                sentiment_bins = []
                sentiment_hist = []
            
            dashboard_stats = {
                'total_eips': total_eips,
                'positive_sentiment': positive_sentiment,
                'negative_sentiment': negative_sentiment,
                'neutral_sentiment': neutral_sentiment,
                'category_labels': category_labels,
                'category_counts': category_counts,
                'status_labels': status_labels,
                'status_counts': status_counts,
                'sentiment_bins': sentiment_bins,
                'sentiment_hist': sentiment_hist
            }
    
    return render_template('dashboard.html', 
                         jobs=jobs, 
                         selected_job_id=selected_job_id,
                         sentiment_data=sentiment_data,
                         **dashboard_stats)

@app.route('/api/export/dashboard/<job_id>')
@require_admin
def export_dashboard_data(job_id):
    """Export dashboard data as CSV"""
    from models import AnalysisJob, EIPSentiment
    job = AnalysisJob.query.get_or_404(job_id)
    sentiment_data = EIPSentiment.query.filter_by(job_id=job_id).all()
    
    if not sentiment_data:
        flash('No data available for export', 'error')
        return redirect(url_for('dashboard'))
    
    # Create CSV response
    import io
    output = io.StringIO()
    import csv
    
    writer = csv.writer(output)
    
    # Write headers
    headers = [
        'EIP', 'Title', 'Author', 'Category', 'Status', 
        'Unified_Compound', 'Unified_Positive', 'Unified_Negative', 'Unified_Neutral',
        'Total_Comment_Count', 'Created_At'
    ]
    writer.writerow(headers)
    
    # Write data rows
    for eip in sentiment_data:
        writer.writerow([
            eip.eip,
            eip.title or '',
            eip.author or '',
            eip.category or '',
            eip.status or '',
            eip.unified_compound if eip.unified_compound is not None else '',
            eip.unified_pos if eip.unified_pos is not None else '',
            eip.unified_neg if eip.unified_neg is not None else '',
            eip.unified_neu if eip.unified_neu is not None else '',
            eip.total_comment_count if eip.total_comment_count is not None else '',
            eip.created_at.strftime('%Y-%m-%d %H:%M:%S') if eip.created_at else ''
        ])
    
    # Create response
    output.seek(0)
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=sentiment_analysis_{job.original_filename}_{job_id[:8]}.csv'
    
    return response

@app.route('/smart-contract')
def smart_contract():
    """Smart Contract Generator page"""
    from models import AnalysisJob, EIPSentiment
    # Get all completed jobs for selection
    jobs = AnalysisJob.query.filter_by(status='completed').order_by(AnalysisJob.created_at.desc()).all()
    
    # Get selected job ID from query parameter
    selected_job_id = request.args.get('job_id')
    
    # If no job selected, use the most recent one
    if not selected_job_id and jobs:
        selected_job_id = jobs[0].id
    
    sentiment_data = []
    
    if selected_job_id:
        # Get sentiment data for the selected job
        sentiment_data = EIPSentiment.query.filter_by(job_id=selected_job_id).all()
    
    return render_template('smart_contract.html', 
                         jobs=jobs, 
                         selected_job_id=selected_job_id,
                         sentiment_data=sentiment_data)

@app.route('/api/generate-contract', methods=['POST'])
def generate_contract():
    """Generate smart contract code using OpenAI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        job_id = data.get('job_id')
        eip_number = data.get('eip_number')
        contract_type = data.get('contract_type')
        custom_prompt = data.get('custom_prompt')
        
        if not job_id or not eip_number or not contract_type:
            return jsonify({'success': False, 'error': 'Missing required parameters'})
        
        # Get EIP data from database
        from models import EIPSentiment
        eip_data_obj = EIPSentiment.query.filter_by(job_id=job_id, eip=eip_number).first()
        
        if not eip_data_obj:
            return jsonify({'success': False, 'error': 'EIP not found in database'})
        
        # Convert to dictionary for the generator
        eip_data = {
            'eip': eip_data_obj.eip,
            'title': eip_data_obj.title,
            'status': eip_data_obj.status,
            'category': eip_data_obj.category,
            'author': eip_data_obj.author
        }
        
        # Initialize code generator
        generator = EIPCodeGenerator()
        
        # Generate the contract
        result = generator.generate_eip_implementation(eip_data, contract_type, custom_prompt)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Contract generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analyze-security', methods=['POST'])
def analyze_security():
    """Analyze smart contract security using OpenAI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        contract_code = data.get('contract_code')
        
        if not contract_code:
            return jsonify({'success': False, 'error': 'Contract code is required'})
        
        # Initialize code generator
        generator = EIPCodeGenerator()
        
        # Analyze security
        result = generator.analyze_contract_security(contract_code)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Security analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-tests', methods=['POST'])
def generate_tests():
    """Generate test suite for smart contract using OpenAI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        contract_code = data.get('contract_code')
        contract_name = data.get('contract_name', 'Contract')
        
        if not contract_code:
            return jsonify({'success': False, 'error': 'Contract code is required'})
        
        # Initialize code generator
        generator = EIPCodeGenerator()
        
        # Generate tests
        result = generator.generate_test_suite(contract_code, contract_name)
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Test generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analyze-code-and-recommend', methods=['POST'])
def analyze_code_and_recommend():
    """Analyze smart contract code and recommend EIPs with sentiment warnings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        job_id = data.get('job_id')
        contract_code = data.get('contract_code')
        analysis_type = data.get('analysis_type', 'comprehensive')
        eip_status_filter = data.get('eip_status_filter', 'final_only')
        
        if not contract_code:
            return jsonify({'success': False, 'error': 'Contract code is required'})
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Job ID is required'})
        
        # Get EIP data based on status filter
        from models import EIPSentiment
        query = EIPSentiment.query.filter_by(job_id=job_id)
        
        if eip_status_filter == 'final_only':
            eip_data_list = query.filter(EIPSentiment.status == 'Final').all()
        elif eip_status_filter == 'final_living':
            eip_data_list = query.filter(EIPSentiment.status.in_(['Final', 'Living'])).all()
        elif eip_status_filter == 'draft_review':
            eip_data_list = query.filter(EIPSentiment.status.in_(['Draft', 'Review'])).all()
        elif eip_status_filter == 'exclude_withdrawn':
            eip_data_list = query.filter(EIPSentiment.status != 'Withdrawn').all()
        else:  # all_statuses
            eip_data_list = query.all()
        
        if not eip_data_list:
            return jsonify({'success': False, 'error': 'No EIP data found for the selected job'})
        
        # Initialize code generator
        generator = EIPCodeGenerator()
        
        # Analyze code and get EIP recommendations
        result = generator.analyze_code_and_recommend_eips(contract_code, analysis_type, eip_data_list, eip_status_filter)
        
        if not result['success']:
            return jsonify(result)
        
        # Process recommendations and add sentiment data
        recommendations = []
        eip_recommendations = result.get('eip_recommendations', [])
        
        for rec in eip_recommendations:
            eip_number = str(rec.get('eip_number', ''))
            
            # Find matching EIP in database
            eip_data = next((eip for eip in eip_data_list if str(eip.eip) == eip_number), None)
            
            if eip_data:
                recommendation = {
                    'eip_number': eip_number,
                    'title': eip_data.title or 'Untitled',
                    'status': eip_data.status or 'Unknown',
                    'category': eip_data.category or 'Unknown',
                    'author': eip_data.author or 'Unknown',
                    'sentiment_score': eip_data.unified_compound or 0.0,
                    'comment_count': eip_data.total_comment_count or 0,
                    'reason': rec.get('reason', 'Relevant to your code'),
                    'confidence': rec.get('confidence', 0.5),
                    'code_patterns': rec.get('code_patterns', [])
                }
                recommendations.append(recommendation)
        
        # Sort by confidence and sentiment score
        recommendations.sort(key=lambda x: (x['confidence'], x['sentiment_score']), reverse=True)
        
        return jsonify({
            'success': True,
            'analysis': result['analysis'],
            'recommendations': recommendations[:10]  # Limit to top 10
        })
        
    except Exception as e:
        logging.error(f"Code analysis and recommendation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
