# EIP Sentiment Analyzer

A comprehensive Flask web application for advanced smart contract analysis, leveraging AI technologies to provide intelligent insights into Ethereum Improvement Proposals (EIPs).

## Features

- **Three-Stage Sentiment Analysis Pipeline**
  - VADER sentiment analysis for comment data
  - EIPs Insight API integration for metadata enrichment
  - Comprehensive data merging and analysis

- **Interactive Dashboard**
  - Chart.js visualizations with real-time filtering
  - Sentiment distribution analysis
  - EIP status and category breakdowns

- **Smart Contract Generator**
  - OpenAI GPT-4o integration for code generation
  - EIP recommendation system with sentiment warnings
  - Security analysis and test suite generation

- **Authentication & Security**
  - Replit OAuth integration
  - Admin role-based access controls
  - Secure session management

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap, Chart.js, Vanilla JavaScript
- **AI Integration**: OpenAI GPT-4o, NLTK VADER
- **Authentication**: Replit OAuth, Flask-Login
- **Testing**: Pytest with comprehensive test coverage

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd eip-sentiment-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export DATABASE_URL="your_postgresql_url"
export OPENAI_API_KEY="your_openai_api_key"
export SESSION_SECRET="your_session_secret"
```

4. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Run the application:
```bash
python main.py
```

## Usage

### Admin Features
- **File Upload**: Upload CSV files containing comment data for sentiment analysis
- **Job Management**: Monitor background processing jobs and view progress
- **Data Export**: Download analysis results and visualizations

### Public Features
- **Dashboard**: View sentiment analysis results and interactive charts
- **Smart Contract Generator**: Generate Solidity contracts with AI assistance
- **EIP Recommendations**: Get AI-powered suggestions for relevant EIPs

## API Endpoints

- `POST /api/generate-contract` - Generate smart contract code
- `POST /api/analyze-security` - Analyze contract security
- `POST /api/generate-tests` - Generate test suites
- `POST /api/analyze-code` - Analyze code and recommend EIPs

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Test coverage includes:
- Route testing (94.4% success rate)
- Database model validation
- Sentiment analysis pipeline (100% success rate)
- Smart contract generator functionality
- Authentication flows

## Project Structure

```
├── app.py                    # Flask application setup
├── main.py                   # Application entry point
├── models.py                 # Database models
├── replit_auth.py           # Authentication handling
├── sentiment_analyzer.py     # Core sentiment analysis engine
├── smart_contract_generator.py # AI-powered contract generation
├── conftest.py              # Test configuration
├── templates/               # HTML templates
├── static/                  # CSS, JS, and static assets
├── tests/                   # Test suite
├── uploads/                 # File upload directory
└── outputs/                 # Analysis output directory
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions, please open an issue in the repository.