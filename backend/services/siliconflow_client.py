import requests
import json
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnalysisResult:
    """Result of AI analysis"""
    success: bool
    content: str
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class SiliconFlowClient:
    """Client for SiliconFlow API integration"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1", 
                 model: str = "Qwen/Qwen2.5-7B-Instruct", max_tokens: int = 2000, 
                 temperature: float = 0.7, timeout: int = 120):
        """
        Initialize SiliconFlow client
        
        Args:
            api_key: SiliconFlow API key
            base_url: Base URL for API endpoints
            model: Model to use for analysis
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Reduce interval for faster processing
        
        # Retry configuration
        self.max_retries = 1  # Further reduce retries to avoid long waits
        self.retry_delay = 3.0  # Initial retry delay in seconds
        self.backoff_multiplier = 1.2  # Minimal backoff multiplier
        
        # Timeout optimization
        self.connection_timeout = 15  # Connection timeout
        self.read_timeout = max(self.timeout - 15, 60)  # Read timeout, minimum 60s
    
    def analyze_content(self, content: str, custom_prompt: str = None) -> AnalysisResult:
        """
        Analyze content using SiliconFlow API
        
        Args:
            content: Content to analyze
            custom_prompt: Optional custom prompt for analysis
            
        Returns:
            AnalysisResult with analysis or error information
        """
        if not content or not content.strip():
            return AnalysisResult(
                success=False,
                content="",
                error_message="No content provided for analysis"
            )
        
        start_time = time.time()
        
        try:
            # Build the prompt
            prompt = self._build_analysis_prompt(content, custom_prompt)
            
            # Create request payload
            payload = self._build_request_payload(prompt)
            
            # Make API request with retries
            response_data = self._make_request_with_retry(payload)
            
            # Process response
            result = self._handle_api_response(response_data, start_time)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Analysis failed: {str(e)}")
            
            return AnalysisResult(
                success=False,
                content="",
                error_message=f"Analysis failed: {str(e)}",
                processing_time=processing_time
            )
    
    def _build_analysis_prompt(self, content: str, custom_prompt: str = None) -> str:
        """
        Build analysis prompt combining custom prompt with content
        
        Args:
            content: Content to analyze
            custom_prompt: Optional custom prompt
            
        Returns:
            Complete prompt for analysis
        """
        # Limit content length to avoid timeout
        max_content_length = 8000  # Reduce content length for faster processing
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[内容已截断，以上为文档前半部分]"
        
        if custom_prompt:
            prompt = f"{custom_prompt}\n\n以下是需要分析的内容：\n\n{content}"
        else:
            default_prompt = "请简要分析以下文档内容，提供主要内容总结和关键建议。"
            prompt = f"{default_prompt}\n\n以下是需要分析的内容：\n\n{content}"
        
        return prompt
    
    def _build_request_payload(self, prompt: str) -> Dict[str, Any]:
        """
        Build request payload for SiliconFlow API
        
        Args:
            prompt: Complete prompt for analysis
            
        Returns:
            Request payload dictionary
        """
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
    
    def _make_request_with_retry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request with retry logic
        
        Args:
            payload: Request payload
            
        Returns:
            Response data
            
        Raises:
            Exception: If all retries fail
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/chat/completions"
        
        last_exception = None
        retry_delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting
                self._enforce_rate_limit()
                
                # Make request
                self.logger.info(f"Making API request (attempt {attempt + 1}/{self.max_retries + 1})")
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(self.connection_timeout, self.read_timeout)
                )
                
                # Update last request time
                self.last_request_time = time.time()
                
                # Handle response
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    self.logger.warning("Rate limited, retrying...")
                    if attempt < self.max_retries:
                        time.sleep(retry_delay)
                        retry_delay *= self.backoff_multiplier
                        continue
                    else:
                        raise Exception("Rate limit exceeded, max retries reached")
                elif response.status_code == 401:
                    raise Exception("Authentication failed - invalid API key")
                elif response.status_code == 400:
                    error_detail = self._extract_error_message(response)
                    raise Exception(f"Bad request: {error_detail}")
                else:
                    error_detail = self._extract_error_message(response)
                    raise Exception(f"API request failed with status {response.status_code}: {error_detail}")
                    
            except requests.exceptions.Timeout:
                last_exception = Exception(f"Request timeout after {self.timeout} seconds")
                if attempt < self.max_retries:
                    self.logger.warning(f"Request timeout, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= self.backoff_multiplier
                    continue
                    
            except requests.exceptions.ConnectionError:
                last_exception = Exception("Connection error - unable to reach SiliconFlow API")
                if attempt < self.max_retries:
                    self.logger.warning(f"Connection error, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= self.backoff_multiplier
                    continue
                    
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries and "rate limit" in str(e).lower():
                    self.logger.warning(f"Error occurred, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= self.backoff_multiplier
                    continue
                else:
                    break
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise Exception("All retry attempts failed")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def _extract_error_message(self, response: requests.Response) -> str:
        """
        Extract error message from API response
        
        Args:
            response: HTTP response object
            
        Returns:
            Error message string
        """
        try:
            error_data = response.json()
            if 'error' in error_data:
                if isinstance(error_data['error'], dict):
                    return error_data['error'].get('message', 'Unknown error')
                else:
                    return str(error_data['error'])
            else:
                return error_data.get('message', 'Unknown error')
        except (json.JSONDecodeError, KeyError):
            return response.text or 'Unknown error'
    
    def _handle_api_response(self, response_data: Dict[str, Any], start_time: float) -> AnalysisResult:
        """
        Handle and process API response
        
        Args:
            response_data: Response data from API
            start_time: Request start time
            
        Returns:
            AnalysisResult with processed response
        """
        processing_time = time.time() - start_time
        
        try:
            # Extract content from response
            choices = response_data.get('choices', [])
            if not choices:
                return AnalysisResult(
                    success=False,
                    content="",
                    error_message="No response choices returned from API",
                    processing_time=processing_time
                )
            
            message = choices[0].get('message', {})
            content = message.get('content', '').strip()
            
            if not content:
                return AnalysisResult(
                    success=False,
                    content="",
                    error_message="Empty response content from API",
                    processing_time=processing_time
                )
            
            # Extract usage information
            usage = response_data.get('usage', {})
            tokens_used = usage.get('total_tokens')
            
            # Extract model information
            model_used = response_data.get('model', self.model)
            
            # Build metadata
            metadata = {
                'response_id': response_data.get('id'),
                'created': response_data.get('created'),
                'usage': usage,
                'finish_reason': choices[0].get('finish_reason')
            }
            
            return AnalysisResult(
                success=True,
                content=content,
                processing_time=processing_time,
                model_used=model_used,
                tokens_used=tokens_used,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error processing API response: {str(e)}")
            return AnalysisResult(
                success=False,
                content="",
                error_message=f"Error processing API response: {str(e)}",
                processing_time=processing_time
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to SiliconFlow API
        
        Returns:
            Dictionary with test results
        """
        test_result = {
            'success': False,
            'error_message': None,
            'response_time': None,
            'api_accessible': False,
            'authentication_valid': False
        }
        
        start_time = time.time()
        
        try:
            # Simple test request
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            test_result['response_time'] = time.time() - start_time
            test_result['api_accessible'] = True
            
            if response.status_code == 200:
                test_result['success'] = True
                test_result['authentication_valid'] = True
            elif response.status_code == 401:
                test_result['error_message'] = "Authentication failed - invalid API key"
            else:
                test_result['error_message'] = f"API returned status {response.status_code}"
                
        except requests.exceptions.Timeout:
            test_result['error_message'] = "Connection timeout"
            test_result['response_time'] = time.time() - start_time
            
        except requests.exceptions.ConnectionError:
            test_result['error_message'] = "Connection error - unable to reach API"
            test_result['response_time'] = time.time() - start_time
            
        except Exception as e:
            test_result['error_message'] = f"Test failed: {str(e)}"
            test_result['response_time'] = time.time() - start_time
        
        return test_result
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the configured model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'base_url': self.base_url,
            'timeout': self.timeout
        }