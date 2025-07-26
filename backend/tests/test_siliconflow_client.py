import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.siliconflow_client import SiliconFlowClient, AnalysisResult


class TestSiliconFlowClient(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "sk-test123456789012345678901234567890"
        self.client = SiliconFlowClient(
            api_key=self.api_key,
            base_url="https://api.siliconflow.cn/v1",
            model="gpt-3.5-turbo",
            max_tokens=4000,
            temperature=0.7,
            timeout=60
        )
    
    def test_init(self):
        """Test client initialization"""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.model, "gpt-3.5-turbo")
        self.assertEqual(self.client.max_tokens, 4000)
        self.assertEqual(self.client.temperature, 0.7)
        self.assertEqual(self.client.timeout, 60)
    
    def test_build_analysis_prompt_with_custom_prompt(self):
        """Test building analysis prompt with custom prompt"""
        content = "Test content"
        custom_prompt = "Custom analysis prompt"
        
        prompt = self.client._build_analysis_prompt(content, custom_prompt)
        
        self.assertIn(custom_prompt, prompt)
        self.assertIn(content, prompt)
        self.assertIn("以下是需要分析的内容", prompt)
    
    def test_build_analysis_prompt_without_custom_prompt(self):
        """Test building analysis prompt without custom prompt"""
        content = "Test content"
        
        prompt = self.client._build_analysis_prompt(content)
        
        self.assertIn("请分析以下文档内容", prompt)
        self.assertIn(content, prompt)
        self.assertIn("以下是需要分析的内容", prompt)
    
    def test_build_request_payload(self):
        """Test building request payload"""
        prompt = "Test prompt"
        
        payload = self.client._build_request_payload(prompt)
        
        expected_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.7,
            "stream": False
        }
        
        self.assertEqual(payload, expected_payload)
    
    def test_analyze_content_empty_content(self):
        """Test analysis with empty content"""
        result = self.client.analyze_content("")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("No content provided", result.error_message)
    
    def test_analyze_content_whitespace_only(self):
        """Test analysis with whitespace-only content"""
        result = self.client.analyze_content("   \n\t  ")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("No content provided", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_success(self, mock_post):
        """Test successful content analysis"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test-id",
            "model": "gpt-3.5-turbo",
            "created": 1234567890,
            "choices": [
                {
                    "message": {
                        "content": "This is the analysis result."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "total_tokens": 100,
                "prompt_tokens": 50,
                "completion_tokens": 50
            }
        }
        mock_post.return_value = mock_response
        
        result = self.client.analyze_content("Test content to analyze")
        
        self.assertTrue(result.success)
        self.assertEqual(result.content, "This is the analysis result.")
        self.assertIsNone(result.error_message)
        self.assertEqual(result.model_used, "gpt-3.5-turbo")
        self.assertEqual(result.tokens_used, 100)
        self.assertIsNotNone(result.processing_time)
        self.assertIsNotNone(result.metadata)
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_api_error_401(self, mock_post):
        """Test analysis with 401 authentication error"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_post.return_value = mock_response
        
        result = self.client.analyze_content("Test content")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("Authentication failed", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_api_error_429(self, mock_post):
        """Test analysis with 429 rate limit error"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_post.return_value = mock_response
        
        result = self.client.analyze_content("Test content")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("Rate limit exceeded", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_api_error_400(self, mock_post):
        """Test analysis with 400 bad request error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Bad request"}}
        mock_post.return_value = mock_response
        
        result = self.client.analyze_content("Test content")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("Bad request", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_timeout(self, mock_post):
        """Test analysis with timeout error"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = self.client.analyze_content("Test content")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("timeout", result.error_message.lower())
    
    @patch('services.siliconflow_client.requests.post')
    def test_analyze_content_connection_error(self, mock_post):
        """Test analysis with connection error"""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = self.client.analyze_content("Test content")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("Connection error", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_retry_logic_success_after_failure(self, mock_post):
        """Test retry logic with success after initial failure"""
        # First call fails with 429, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 429
        mock_response_fail.json.return_value = {"error": {"message": "Rate limited"}}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}],
            "usage": {"total_tokens": 50}
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = self.client.analyze_content("Test content")
        
        self.assertTrue(result.success)
        self.assertEqual(result.content, "Success after retry")
        self.assertEqual(mock_post.call_count, 2)
    
    def test_extract_error_message_dict_error(self):
        """Test error message extraction from dict error"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": {"message": "Test error message"}}
        
        error_msg = self.client._extract_error_message(mock_response)
        
        self.assertEqual(error_msg, "Test error message")
    
    def test_extract_error_message_string_error(self):
        """Test error message extraction from string error"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "String error message"}
        
        error_msg = self.client._extract_error_message(mock_response)
        
        self.assertEqual(error_msg, "String error message")
    
    def test_extract_error_message_fallback(self):
        """Test error message extraction fallback"""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Raw error text"
        
        error_msg = self.client._extract_error_message(mock_response)
        
        self.assertEqual(error_msg, "Raw error text")
    
    def test_handle_api_response_no_choices(self):
        """Test handling API response with no choices"""
        response_data = {"usage": {"total_tokens": 0}}
        
        result = self.client._handle_api_response(response_data, time.time())
        
        self.assertFalse(result.success)
        self.assertIn("No response choices", result.error_message)
    
    def test_handle_api_response_empty_content(self):
        """Test handling API response with empty content"""
        response_data = {
            "choices": [{"message": {"content": ""}}],
            "usage": {"total_tokens": 10}
        }
        
        result = self.client._handle_api_response(response_data, time.time())
        
        self.assertFalse(result.success)
        self.assertIn("Empty response content", result.error_message)
    
    @patch('services.siliconflow_client.requests.post')
    def test_test_connection_success(self, mock_post):
        """Test successful connection test"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello"}}]}
        mock_post.return_value = mock_response
        
        result = self.client.test_connection()
        
        self.assertTrue(result['success'])
        self.assertTrue(result['api_accessible'])
        self.assertTrue(result['authentication_valid'])
        self.assertIsNone(result['error_message'])
        self.assertIsNotNone(result['response_time'])
    
    @patch('services.siliconflow_client.requests.post')
    def test_test_connection_auth_failure(self, mock_post):
        """Test connection test with authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        result = self.client.test_connection()
        
        self.assertFalse(result['success'])
        self.assertTrue(result['api_accessible'])
        self.assertFalse(result['authentication_valid'])
        self.assertIn("Authentication failed", result['error_message'])
    
    @patch('services.siliconflow_client.requests.post')
    def test_test_connection_timeout(self, mock_post):
        """Test connection test with timeout"""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = self.client.test_connection()
        
        self.assertFalse(result['success'])
        self.assertFalse(result['api_accessible'])
        self.assertFalse(result['authentication_valid'])
        self.assertIn("timeout", result['error_message'].lower())
    
    def test_get_model_info(self):
        """Test getting model information"""
        info = self.client.get_model_info()
        
        expected_info = {
            'model': 'gpt-3.5-turbo',
            'max_tokens': 4000,
            'temperature': 0.7,
            'base_url': 'https://api.siliconflow.cn/v1',
            'timeout': 60
        }
        
        self.assertEqual(info, expected_info)
    
    def test_rate_limiting(self):
        """Test rate limiting enforcement"""
        # Set a very recent last request time
        self.client.last_request_time = time.time()
        self.client.min_request_interval = 0.1
        
        start_time = time.time()
        self.client._enforce_rate_limit()
        end_time = time.time()
        
        # Should have slept for at least the minimum interval
        elapsed = end_time - start_time
        self.assertGreaterEqual(elapsed, 0.05)  # Allow some tolerance


if __name__ == '__main__':
    unittest.main()