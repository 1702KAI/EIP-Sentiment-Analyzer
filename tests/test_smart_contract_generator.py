"""
Tests for Smart Contract Generator functionality
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from smart_contract_generator import EIPCodeGenerator


class TestEIPCodeGenerator:
    """Test EIPCodeGenerator class functionality"""
    
    def test_generator_initialization(self):
        """Test EIP code generator initializes correctly"""
        generator = EIPCodeGenerator()
        assert generator is not None
        assert hasattr(generator, 'client')
    
    @patch('smart_contract_generator.OpenAI')
    def test_generate_eip_implementation(self, mock_openai):
        """Test EIP implementation generation"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        ```solidity
        pragma solidity ^0.8.0;
        
        contract TestERC20 {
            string public name = "Test Token";
            string public symbol = "TEST";
            uint8 public decimals = 18;
        }
        ```
        """
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        
        eip_data = {
            'eip': '20',
            'title': 'EIP-20: Token Standard',
            'category': 'ERC',
            'status': 'Final'
        }
        
        result = generator.generate_eip_implementation(eip_data, 'ERC20')
        
        assert result['success'] is True
        assert 'contract_code' in result
        assert 'TestERC20' in result['contract_code']
    
    @patch('smart_contract_generator.OpenAI')
    def test_analyze_contract_security(self, mock_openai):
        """Test contract security analysis"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        # Security Analysis Report
        
        ## High Severity Issues
        - Reentrancy vulnerability in withdraw function
        - Missing access control on critical functions
        
        ## Medium Severity Issues
        - Integer overflow potential
        - Unchecked external calls
        """
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        contract_code = """
        contract TestContract {
            function withdraw() public {
                // Vulnerable code
            }
        }
        """
        
        result = generator.analyze_contract_security(contract_code)
        
        assert result['success'] is True
        assert 'analysis' in result
        assert 'Security Analysis' in result['analysis']
    
    @patch('smart_contract_generator.OpenAI')
    def test_generate_test_suite(self, mock_openai):
        """Test test suite generation"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        ```javascript
        const { expect } = require("chai");
        
        describe("TestContract", function() {
            it("Should deploy correctly", async function() {
                const TestContract = await ethers.getContractFactory("TestContract");
                const contract = await TestContract.deploy();
                expect(contract.address).to.be.properAddress;
            });
        });
        ```
        """
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        contract_code = "contract TestContract {}"
        
        result = generator.generate_test_suite(contract_code, "TestContract")
        
        assert result['success'] is True
        assert 'test_code' in result
        assert 'describe("TestContract"' in result['test_code']
    
    @patch('smart_contract_generator.OpenAI')
    def test_analyze_code_and_recommend_eips(self, mock_openai):
        """Test code analysis and EIP recommendations"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        {
            "recommendations": [
                {
                    "eip": "20",
                    "relevance_score": 0.9,
                    "reasoning": "Contract implements token functionality",
                    "title": "EIP-20: Token Standard",
                    "status": "Final",
                    "category": "ERC"
                },
                {
                    "eip": "165",
                    "relevance_score": 0.7,
                    "reasoning": "Contract could benefit from interface detection",
                    "title": "EIP-165: Standard Interface Detection",
                    "status": "Final",
                    "category": "ERC"
                }
            ]
        }
        """
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        contract_code = """
        contract Token {
            mapping(address => uint256) public balances;
            function transfer(address to, uint256 amount) public returns (bool) {
                balances[msg.sender] -= amount;
                balances[to] += amount;
                return true;
            }
        }
        """
        
        eip_data_list = [
            MagicMock(eip='20', title='EIP-20: Token Standard', status='Final', category='ERC'),
            MagicMock(eip='165', title='EIP-165: Interface Detection', status='Final', category='ERC')
        ]
        
        result = generator.analyze_code_and_recommend_eips(
            contract_code, 'comprehensive', eip_data_list
        )
        
        assert result['success'] is True
        assert 'recommendations' in result
        assert len(result['recommendations']) == 2
    
    def test_format_eip_list(self):
        """Test EIP list formatting for AI prompts"""
        generator = EIPCodeGenerator()
        
        eip_data_list = [
            MagicMock(
                eip='20',
                title='EIP-20: Token Standard',
                status='Final',
                category='ERC',
                author='Fabian Vogelsteller',
                unified_compound=0.5
            ),
            MagicMock(
                eip='721',
                title='EIP-721: NFT Standard',
                status='Final',
                category='ERC',
                author='William Entriken',
                unified_compound=-0.1
            )
        ]
        
        formatted_list = generator._format_eip_list(eip_data_list)
        
        assert 'EIP-20' in formatted_list
        assert 'EIP-721' in formatted_list
        assert 'Token Standard' in formatted_list
        assert 'NFT Standard' in formatted_list


class TestSmartContractGeneratorErrorHandling:
    """Test error handling in smart contract generator"""
    
    @patch('smart_contract_generator.OpenAI')
    def test_openai_api_error_handling(self, mock_openai):
        """Test handling of OpenAI API errors"""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        
        eip_data = {
            'eip': '20',
            'title': 'EIP-20: Token Standard'
        }
        
        result = generator.generate_eip_implementation(eip_data, 'ERC20')
        
        assert result['success'] is False
        assert 'error' in result
    
    @patch('smart_contract_generator.OpenAI')
    def test_invalid_json_response_handling(self, mock_openai):
        """Test handling of invalid JSON responses"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        contract_code = "contract Test {}"
        eip_data_list = []
        
        result = generator.analyze_code_and_recommend_eips(
            contract_code, 'comprehensive', eip_data_list
        )
        
        # Should handle gracefully even with invalid JSON
        assert 'success' in result
    
    def test_empty_contract_code(self):
        """Test handling of empty contract code"""
        generator = EIPCodeGenerator()
        
        result = generator.analyze_contract_security("")
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_missing_eip_data(self):
        """Test handling of missing EIP data"""
        generator = EIPCodeGenerator()
        
        result = generator.generate_eip_implementation({}, 'ERC20')
        
        # Should handle missing data gracefully
        assert 'success' in result


class TestSmartContractGeneratorIntegration:
    """Integration tests for smart contract generator"""
    
    @patch('smart_contract_generator.OpenAI')
    def test_full_workflow_generation_to_analysis(self, mock_openai):
        """Test complete workflow from generation to analysis"""
        mock_client = MagicMock()
        
        # Mock contract generation response
        generation_response = MagicMock()
        generation_response.choices[0].message.content = """
        ```solidity
        pragma solidity ^0.8.0;
        
        contract GeneratedToken {
            string public name = "Generated Token";
            mapping(address => uint256) public balances;
            
            function transfer(address to, uint256 amount) public returns (bool) {
                require(balances[msg.sender] >= amount, "Insufficient balance");
                balances[msg.sender] -= amount;
                balances[to] += amount;
                return true;
            }
        }
        ```
        """
        
        # Mock security analysis response
        analysis_response = MagicMock()
        analysis_response.choices[0].message.content = """
        # Security Analysis
        
        ## Issues Found
        - Missing access control
        - No events emitted
        
        ## Recommendations
        - Add owner access control
        - Emit Transfer events
        """
        
        # Configure mock to return different responses based on call
        mock_client.chat.completions.create.side_effect = [
            generation_response,
            analysis_response
        ]
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        
        # Step 1: Generate contract
        eip_data = {
            'eip': '20',
            'title': 'EIP-20: Token Standard',
            'category': 'ERC'
        }
        
        generation_result = generator.generate_eip_implementation(eip_data, 'ERC20')
        assert generation_result['success'] is True
        
        # Step 2: Analyze generated contract
        generated_code = generation_result['contract_code']
        analysis_result = generator.analyze_contract_security(generated_code)
        assert analysis_result['success'] is True
        
        # Verify both results contain expected content
        assert 'GeneratedToken' in generated_code
        assert 'Security Analysis' in analysis_result['analysis']
    
    @patch('smart_contract_generator.OpenAI')
    def test_eip_status_filtering_recommendations(self, mock_openai):
        """Test EIP recommendations with different status filters"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        {
            "recommendations": [
                {
                    "eip": "20",
                    "relevance_score": 0.9,
                    "reasoning": "Token functionality detected",
                    "title": "EIP-20: Token Standard",
                    "status": "Final",
                    "category": "ERC"
                },
                {
                    "eip": "1234",
                    "relevance_score": 0.6,
                    "reasoning": "Experimental feature",
                    "title": "EIP-1234: Draft Standard",
                    "status": "Draft",
                    "category": "ERC"
                }
            ]
        }
        """
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = EIPCodeGenerator()
        contract_code = "contract Token {}"
        
        # Test with Final status only
        final_eips = [
            MagicMock(eip='20', status='Final', title='EIP-20: Token Standard')
        ]
        
        result_final = generator.analyze_code_and_recommend_eips(
            contract_code, 'comprehensive', final_eips, 'final_only'
        )
        
        assert result_final['success'] is True
        
        # Test with all statuses
        all_eips = [
            MagicMock(eip='20', status='Final', title='EIP-20: Token Standard'),
            MagicMock(eip='1234', status='Draft', title='EIP-1234: Draft Standard')
        ]
        
        result_all = generator.analyze_code_and_recommend_eips(
            contract_code, 'comprehensive', all_eips, 'all_statuses'
        )
        
        assert result_all['success'] is True