import os
import json
import logging
from openai import OpenAI

class EIPCodeGenerator:
    def __init__(self):
        """Initialize the EIP code generator with OpenAI client"""
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
    def generate_eip_implementation(self, eip_data, contract_type, custom_prompt=None):
        """
        Generate Solidity smart contract code for EIP implementation
        
        Args:
            eip_data: Dictionary containing EIP metadata
            contract_type: Type of contract to generate (e.g., "ERC20", "ERC721", "Governance")
            custom_prompt: Optional custom prompt for specific requirements
        """
        try:
            # Construct intelligent prompt
            system_prompt = f"""
You are an expert Solidity developer specializing in Ethereum Improvement Proposals.
Generate production-ready, secure, and gas-optimized smart contract code.

EIP Details:
- Number: {eip_data.get('eip', 'N/A')}
- Title: {eip_data.get('title', 'N/A')}
- Status: {eip_data.get('status', 'N/A')}
- Category: {eip_data.get('category', 'N/A')}
- Author: {eip_data.get('author', 'N/A')}

Contract Type: {contract_type}
"""

            user_prompt = custom_prompt or f"""
Generate a complete Solidity implementation for EIP-{eip_data.get('eip', 'N/A')}: {eip_data.get('title', 'N/A')}.

Requirements:
1. Follow the exact specification from the EIP
2. Include comprehensive error handling
3. Implement gas optimization patterns
4. Add detailed NatSpec documentation
5. Include security considerations
6. Provide deployment and testing examples
7. Use Solidity version ^0.8.0 or higher
8. Follow OpenZeppelin patterns where applicable

Focus on {contract_type} implementation patterns.
Make sure the contract is complete and deployable.
"""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistent code generation
            )

            generated_code = response.choices[0].message.content

            return {
                "success": True,
                "eip_number": eip_data.get('eip', 'N/A'),
                "contract_type": contract_type,
                "generated_code": generated_code,
                "eip_metadata": eip_data
            }

        except Exception as e:
            logging.error(f"Code generation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Code generation failed: {str(e)}",
                "eip_number": eip_data.get('eip', 'N/A'),
                "contract_type": contract_type
            }
    
    def analyze_contract_security(self, contract_code):
        """
        AI-powered security analysis of smart contract code
        """
        try:
            analysis_prompt = f"""
Analyze this Solidity smart contract for security vulnerabilities, gas optimization opportunities, and best practices:

```solidity
{contract_code}
```

Provide a comprehensive analysis including:
1. Security vulnerabilities (reentrancy, overflow, access control, etc.)
2. Gas optimization opportunities
3. Code quality and best practices
4. EIP compliance verification
5. Recommended improvements

Format the response as structured text with clear sections and severity levels.
"""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2000,
                temperature=0.2
            )

            return {
                "success": True,
                "analysis": response.choices[0].message.content
            }

        except Exception as e:
            logging.error(f"Security analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"Security analysis failed: {str(e)}"
            }

    def generate_test_suite(self, contract_code, contract_name):
        """
        Generate comprehensive test suite for the smart contract
        """
        try:
            test_prompt = f"""
Generate a comprehensive test suite for this Solidity smart contract using Hardhat and Chai:

Contract Name: {contract_name}

```solidity
{contract_code}
```

Requirements:
1. Test all public functions
2. Include edge cases and error conditions
3. Test access control and permissions
4. Include gas usage tests
5. Test events emission
6. Use modern testing patterns
7. Include setup and teardown functions

Format as complete JavaScript test files ready to run with Hardhat.
"""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": test_prompt}],
                max_tokens=3000,
                temperature=0.1
            )

            return {
                "success": True,
                "test_code": response.choices[0].message.content
            }

        except Exception as e:
            logging.error(f"Test generation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Test generation failed: {str(e)}"
            }

    def analyze_code_and_recommend_eips(self, contract_code, analysis_type, eip_data_list):
        """
        Analyze smart contract code and recommend relevant EIPs with sentiment warnings
        """
        try:
            analysis_prompt = f"""
Analyze this Solidity smart contract code and identify which Ethereum Improvement Proposals (EIPs) are most relevant:

```solidity
{contract_code}
```

Analysis Focus: {analysis_type}

Based on the code patterns, functionality, and standards used, identify the top 5 most relevant EIPs from this list and explain why each is relevant:

Available EIPs:
{self._format_eip_list(eip_data_list)}

For each relevant EIP, provide:
1. EIP number
2. Brief explanation of why it's relevant to this code
3. Confidence level (0.0 to 1.0)
4. Specific code patterns or features that relate to the EIP

Format your response as a JSON object with this structure:
{{
  "recommendations": [
    {{
      "eip_number": "20",
      "reason": "Code implements token functionality with transfer methods",
      "confidence": 0.95,
      "code_patterns": ["transfer function", "balanceOf mapping"]
    }}
  ]
}}

Focus on EIPs that are actually implemented or could be implemented by this code.
"""

            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=2000,
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            import json
            content = response.choices[0].message.content or ""
            if not content.strip():
                return {"success": False, "error": "Empty response from AI"}
            recommendations = json.loads(content)
            
            # Also get general analysis
            general_analysis = self.analyze_contract_security(contract_code)
            
            # Extract analysis text properly
            if isinstance(general_analysis, dict) and general_analysis.get("success"):
                analysis_text = general_analysis.get("analysis", "Analysis completed")
            else:
                analysis_text = "Security analysis completed"
            
            # Extract recommendations properly
            if isinstance(recommendations, dict) and "recommendations" in recommendations:
                eip_recs = recommendations["recommendations"]
            elif isinstance(recommendations, list):
                eip_recs = recommendations
            else:
                eip_recs = []
            
            return {
                "success": True,
                "analysis": analysis_text,
                "eip_recommendations": eip_recs
            }

        except Exception as e:
            logging.error(f"Code analysis and EIP recommendation failed: {str(e)}")
            return {
                "success": False,
                "error": f"Code analysis failed: {str(e)}"
            }

    def _format_eip_list(self, eip_data_list):
        """Format EIP list for AI prompt"""
        formatted = []
        for eip in eip_data_list[:50]:  # Limit to first 50 EIPs to avoid token limits
            formatted.append(f"EIP-{eip.eip}: {eip.title} (Status: {eip.status}, Category: {eip.category})")
        return "\n".join(formatted)