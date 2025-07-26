import json
import os
import sqlite3
from typing import Optional
from datetime import datetime

class ConfigManager:
    """Configuration manager for AI analysis module"""
    
    def __init__(self, config_file_path: str = None, database_path: str = None):
        self.config_file_path = config_file_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'config', 'ai_config.json'
        )
        self.database_path = database_path or os.path.join(
            os.path.dirname(__file__), '..', '..', 'database', 'efficiency.db'
        )
        self._config_cache = None
    
    def _load_config_file(self) -> dict:
        """Load configuration from JSON file"""
        if self._config_cache is None:
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file: {e}")
        return self._config_cache
    
    def get_api_key(self) -> str:
        """Get SiliconFlow API key from configuration"""
        config = self._load_config_file()
        api_key = config.get('siliconflow', {}).get('api_key')
        
        if not api_key:
            raise ValueError("SiliconFlow API key not found in configuration")
        
        if not self._validate_api_key_format(api_key):
            raise ValueError("Invalid API key format")
        
        return api_key
    
    def get_siliconflow_config(self) -> dict:
        """Get complete SiliconFlow configuration"""
        config = self._load_config_file()
        return config.get('siliconflow', {})
    
    def get_file_processing_config(self) -> dict:
        """Get file processing configuration"""
        config = self._load_config_file()
        return config.get('file_processing', {})
    
    def get_custom_prompt(self) -> Optional[str]:
        """Get custom prompt from database, fallback to config file"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT custom_prompt FROM ai_config ORDER BY updated_at DESC LIMIT 1'
            )
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
        except sqlite3.Error:
            # If database query fails, fallback to config file
            pass
        
        # Fallback to config file
        config = self._load_config_file()
        return config.get('prompts', {}).get('custom')
    
    def get_default_prompt(self) -> str:
        """Get default prompt from configuration"""
        config = self._load_config_file()
        default_prompt = config.get('prompts', {}).get('default')
        
        if not default_prompt:
            return "请分析以下文档内容，提供详细的分析报告，包括主要内容总结、关键信息提取和建议。"
        
        return default_prompt
    
    def get_effective_prompt(self) -> str:
        """Get the prompt to use (custom if available, otherwise default)"""
        custom_prompt = self.get_custom_prompt()
        if custom_prompt:
            return custom_prompt
        return self.get_default_prompt()
    
    def set_custom_prompt(self, prompt: str) -> None:
        """Set custom prompt in database"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if len(prompt) > 5000:  # Reasonable limit
            raise ValueError("Prompt is too long (maximum 5000 characters)")
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check if config exists
            cursor.execute('SELECT COUNT(*) FROM ai_config')
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insert new config
                cursor.execute('''
                    INSERT INTO ai_config (api_key, custom_prompt, updated_at)
                    VALUES (?, ?, ?)
                ''', (self.get_api_key(), prompt.strip(), datetime.now()))
            else:
                # Update existing config
                cursor.execute('''
                    UPDATE ai_config 
                    SET custom_prompt = ?, updated_at = ?
                    WHERE id = (SELECT id FROM ai_config ORDER BY updated_at DESC LIMIT 1)
                ''', (prompt.strip(), datetime.now()))
            
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to save custom prompt: {e}")
    
    def clear_custom_prompt(self) -> None:
        """Clear custom prompt (will use default)"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE ai_config 
                SET custom_prompt = NULL, updated_at = ?
                WHERE id = (SELECT id FROM ai_config ORDER BY updated_at DESC LIMIT 1)
            ''', (datetime.now(),))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to clear custom prompt: {e}")
    
    def get_max_file_size(self) -> int:
        """Get maximum file size in bytes"""
        config = self._load_config_file()
        return config.get('file_processing', {}).get('max_file_size', 5242880)  # 5MB default
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        config = self._load_config_file()
        return config.get('file_processing', {}).get('supported_formats', 
                         ['pdf', 'md', 'xlsx', 'xls', 'docx', 'doc', 'txt'])
    
    def get_temp_dir(self) -> str:
        """Get temporary directory for file uploads"""
        config = self._load_config_file()
        temp_dir = config.get('file_processing', {}).get('temp_dir', 'temp/uploads')
        
        # Ensure directory exists
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def _validate_api_key_format(self, api_key: str) -> bool:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # SiliconFlow API keys typically start with 'sk-'
        if not api_key.startswith('sk-'):
            return False
        
        # Should be at least 20 characters long
        if len(api_key) < 20:
            return False
        
        return True
    
    def validate_configuration(self) -> dict:
        """Validate entire configuration and return status"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test config file loading
            config = self._load_config_file()
            
            # Validate API key
            try:
                api_key = self.get_api_key()
                if not self._validate_api_key_format(api_key):
                    validation_result['errors'].append("Invalid API key format")
                    validation_result['valid'] = False
            except Exception as e:
                validation_result['errors'].append(f"API key error: {str(e)}")
                validation_result['valid'] = False
            
            # Validate file processing config
            max_size = self.get_max_file_size()
            if max_size <= 0 or max_size > 10485760:  # 10MB max
                validation_result['warnings'].append("File size limit seems unusual")
            
            # Validate supported formats
            formats = self.get_supported_formats()
            if not formats:
                validation_result['errors'].append("No supported file formats configured")
                validation_result['valid'] = False
            
            # Test database connection
            try:
                conn = sqlite3.connect(self.database_path)
                conn.close()
            except Exception as e:
                validation_result['errors'].append(f"Database connection error: {str(e)}")
                validation_result['valid'] = False
                
        except Exception as e:
            validation_result['errors'].append(f"Configuration error: {str(e)}")
            validation_result['valid'] = False
        
        return validation_result