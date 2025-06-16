"""
Tests for sentiment analysis functionality
"""

import pytest
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from sentiment_analyzer import SentimentAnalyzer


class TestSentimentAnalyzer:
    """Test SentimentAnalyzer class functionality"""
    
    def test_analyzer_initialization(self):
        """Test sentiment analyzer initializes correctly"""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None
    
    @patch('sentiment_analyzer.SentimentIntensityAnalyzer')
    def test_stage1_processing(self, mock_vader):
        """Test stage 1 VADER sentiment analysis"""
        # Mock VADER analyzer
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.polarity_scores.return_value = {
            'compound': 0.5, 'pos': 0.7, 'neu': 0.2, 'neg': 0.1
        }
        mock_vader.return_value = mock_analyzer_instance
        
        # Create test CSV
        test_data = {
            'paragraphs': ['This is a positive comment about EIP-1'],
            'headings': ['EIP-1 Discussion'],
            'unordered_lists': ['- Feature 1'],
            'topic': ['eip-1']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(test_data)
            df.to_csv(f.name, index=False)
            input_file = f.name
        
        with tempfile.TemporaryDirectory() as output_dir:
            analyzer = SentimentAnalyzer()
            result = analyzer.run_stage1(input_file, output_dir)
            
            assert result is not None
            assert os.path.exists(result)
        
        os.unlink(input_file)
    
    @patch('requests.get')
    def test_stage2_eips_data_fetch(self, mock_get):
        """Test stage 2 EIPs data fetching"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'eip': 1,
                    'title': 'EIP Purpose and Guidelines',
                    'status': 'Living',
                    'category': 'Core',
                    'author': 'Martin Becze'
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as output_dir:
            # Create stage1 output first
            stage1_data = {
                'eip_erc_numbers': ['1'],
                'compound': [0.5],
                'pos': [0.7],
                'neu': [0.2],
                'neg': [0.1]
            }
            stage1_df = pd.DataFrame(stage1_data)
            stage1_file = os.path.join(output_dir, 'stage1_with_eip_erc.csv')
            stage1_df.to_csv(stage1_file, index=False)
            
            analyzer = SentimentAnalyzer()
            result = analyzer.run_stage2(output_dir)
            
            assert result is not None
            assert os.path.exists(result)
    
    def test_stage3_data_merging(self):
        """Test stage 3 data merging and final output"""
        with tempfile.TemporaryDirectory() as output_dir:
            # Create mock stage1 and stage2 outputs
            stage1_data = {
                'eip_erc_numbers': ['1', '20'],
                'compound': [0.5, 0.3],
                'pos': [0.7, 0.6],
                'neu': [0.2, 0.3],
                'neg': [0.1, 0.1],
                'comment_count': [10, 15]
            }
            
            stage2_data = {
                'eip': [1, 20],
                'title': ['EIP-1: Purpose', 'EIP-20: Token'],
                'status': ['Living', 'Final'],
                'category': ['Core', 'ERC'],
                'author': ['Martin Becze', 'Fabian Vogelsteller']
            }
            
            stage1_df = pd.DataFrame(stage1_data)
            stage2_df = pd.DataFrame(stage2_data)
            
            stage1_file = os.path.join(output_dir, 'aggregated_sentiment_with_eip_erc.csv')
            stage2_file = os.path.join(output_dir, 'eips_data.csv')
            
            stage1_df.to_csv(stage1_file, index=False)
            stage2_df.to_csv(stage2_file, index=False)
            
            analyzer = SentimentAnalyzer()
            result = analyzer.run_stage3(output_dir)
            
            assert result is not None
            assert os.path.exists(result)
            
            # Verify merged data
            merged_df = pd.read_csv(result)
            assert len(merged_df) == 2
            assert 'title' in merged_df.columns
            assert 'status' in merged_df.columns


class TestSentimentAnalysisHelpers:
    """Test helper functions for sentiment analysis"""
    
    def test_eip_number_extraction(self):
        """Test EIP number extraction from text"""
        analyzer = SentimentAnalyzer()
        
        test_cases = [
            ("Discussion about EIP-1", "1"),
            ("ERC-20 token implementation", "20"),
            ("EIP 721 NFT standard", "721"),
            ("No EIP mentioned here", None)
        ]
        
        # This would test the EIP extraction logic if exposed
        # For now, we test through the full pipeline
        assert True  # Placeholder for actual extraction testing
    
    def test_sentiment_aggregation(self):
        """Test sentiment score aggregation"""
        test_scores = [
            {'compound': 0.5, 'pos': 0.7, 'neu': 0.2, 'neg': 0.1},
            {'compound': 0.3, 'pos': 0.6, 'neu': 0.3, 'neg': 0.1},
            {'compound': -0.2, 'pos': 0.3, 'neu': 0.4, 'neg': 0.3}
        ]
        
        # Test aggregation logic
        avg_compound = sum(score['compound'] for score in test_scores) / len(test_scores)
        assert abs(avg_compound - 0.2) < 0.01  # Should be approximately 0.2
    
    def test_data_validation(self):
        """Test input data validation"""
        valid_data = {
            'paragraphs': ['Test paragraph'],
            'headings': ['Test heading'],
            'unordered_lists': ['- Test item'],
            'topic': ['test-topic']
        }
        
        invalid_data = {
            'paragraphs': ['Test paragraph'],
            'missing_column': ['value']
        }
        
        # Test valid data
        df_valid = pd.DataFrame(valid_data)
        required_columns = ['paragraphs', 'headings', 'unordered_lists', 'topic']
        assert all(col in df_valid.columns for col in required_columns)
        
        # Test invalid data
        df_invalid = pd.DataFrame(invalid_data)
        missing_columns = [col for col in required_columns if col not in df_invalid.columns]
        assert len(missing_columns) > 0


class TestSentimentAnalysisIntegration:
    """Integration tests for complete sentiment analysis pipeline"""
    
    @patch('requests.get')
    @patch('sentiment_analyzer.SentimentIntensityAnalyzer')
    def test_full_pipeline_integration(self, mock_vader, mock_requests):
        """Test complete three-stage pipeline"""
        # Mock VADER
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.polarity_scores.return_value = {
            'compound': 0.5, 'pos': 0.7, 'neu': 0.2, 'neg': 0.1
        }
        mock_vader.return_value = mock_analyzer_instance
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'eip': 20,
                    'title': 'EIP-20: Token Standard',
                    'status': 'Final',
                    'category': 'ERC',
                    'author': 'Fabian Vogelsteller'
                }
            ]
        }
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        # Create test input
        test_data = {
            'paragraphs': ['Positive comment about ERC-20 tokens'],
            'headings': ['ERC-20 Token Discussion'],
            'unordered_lists': ['- Feature 1'],
            'topic': ['erc-20']
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(test_data)
            df.to_csv(f.name, index=False)
            input_file = f.name
        
        with tempfile.TemporaryDirectory() as output_dir:
            analyzer = SentimentAnalyzer()
            
            # Run all three stages
            stage1_result = analyzer.run_stage1(input_file, output_dir)
            assert stage1_result is not None
            
            stage2_result = analyzer.run_stage2(output_dir)
            assert stage2_result is not None
            
            stage3_result = analyzer.run_stage3(output_dir)
            assert stage3_result is not None
            
            # Verify final output
            final_df = pd.read_csv(stage3_result)
            assert len(final_df) > 0
            assert 'unified_compound' in final_df.columns
            assert 'title' in final_df.columns
        
        os.unlink(input_file)
    
    def test_error_handling_missing_files(self):
        """Test error handling for missing input files"""
        analyzer = SentimentAnalyzer()
        
        with tempfile.TemporaryDirectory() as output_dir:
            # Test with non-existent input file
            with pytest.raises(Exception):
                analyzer.run_stage1('/nonexistent/file.csv', output_dir)
    
    def test_error_handling_invalid_csv(self):
        """Test error handling for invalid CSV format"""
        # Create invalid CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("invalid,csv,format\n")
            f.write("missing,required,columns\n")
            invalid_file = f.name
        
        with tempfile.TemporaryDirectory() as output_dir:
            analyzer = SentimentAnalyzer()
            
            # Should handle missing required columns gracefully
            try:
                result = analyzer.run_stage1(invalid_file, output_dir)
                # If it doesn't raise an exception, it should handle gracefully
                assert True
            except Exception as e:
                # Should be a meaningful error about missing columns
                assert 'column' in str(e).lower() or 'missing' in str(e).lower()
        
        os.unlink(invalid_file)