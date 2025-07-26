import unittest
import tempfile
import os
import json
import sqlite3
from unittest.mock import patch, mock_open
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_config.json')
        self.db_file = os.path.join(self.temp_dir, 'test.db')
        
        # Create test configuration
        self.test_config = {
            "siliconflow": {
                "api_key": "sk-test123456789012345678901234567890",
                "base_url": "https://api.siliconflow.cn/v1",
                "model": "gpt-3.5-turbo",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "file_processing": {
                "max_file_size": 5242880,
                "supported_formats": ["pdf", "md", "xlsx", "xls", "docx", "doc", "txt"],
                "temp_dir": "temp/uploads"
            },
            "prompts": {
                "default": "请分析以下文档内容，提供详细的分析报告。",
                "custom": None
            }
        }
        
        # Write test config to file
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f, ensure_ascii=False, indent=2)
        
        # Create test database
        self._create_test_database()
        
        self.config_manager = ConfigManager(self.config_file, self.db_file)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Create test database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_config (
                id INTEGER PRIMARY KEY,
                api_key TEXT NOT NULL,
                custom_prompt TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def test_load_config_file_success(self):
        """Test successful config file loading"""
        config = self.config_manager._load_config_file()
        self.assertEqual(config['siliconflow']['api_key'], 'sk-test123456789012345678901234567890')
        self.assertEqual(config['file_processing']['max_file_size'], 5242880)
    
    def test_load_config_file_not_found(self):
        """Test config file not found error"""
        config_manager = ConfigManager('/nonexistent/config.json', self.db_file)
        with self.assertRaises(FileNotFoundError):
            config_manager._load_config_file()
    
    def test_load_config_file_invalid_json(self):
        """Test invalid JSON in config file"""
        invalid_config_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_config_file, 'w') as f:
            f.write('{ invalid json }')
        
        config_manager = ConfigManager(invalid_config_file, self.db_file)
        with self.assertRaises(ValueError):
            config_manager._load_config_file()
    
    def test_get_api_key_success(self):
        """Test successful API key retrieval"""
        api_key = self.config_manager.get_api_key()
        self.assertEqual(api_key, 'sk-test123456789012345678901234567890')
    
    def test_get_api_key_missing(self):
        """Test API key missing error"""
        # Create config without API key
        config_without_key = self.test_config.copy()
        del config_without_key['siliconflow']['api_key']
        
        config_file = os.path.join(self.temp_dir, 'no_key.json')
        with open(config_file, 'w') as f:
            json.dump(config_without_key, f)
        
        config_manager = ConfigManager(config_file, self.db_file)
        with self.assertRaises(ValueError):
            config_manager.get_api_key()
    
    def test_validate_api_key_format(self):
        """Test API key format validation"""
        # Valid key
        self.assertTrue(self.config_manager._validate_api_key_format('sk-test123456789012345678901234567890'))
        
        # Invalid keys
        self.assertFalse(self.config_manager._validate_api_key_format('invalid-key'))
        self.assertFalse(self.config_manager._validate_api_key_format('sk-short'))
        self.assertFalse(self.config_manager._validate_api_key_format(''))
        self.assertFalse(self.config_manager._validate_api_key_format(None))
    
    def test_get_default_prompt(self):
        """Test default prompt retrieval"""
        prompt = self.config_manager.get_default_prompt()
        self.assertEqual(prompt, "请分析以下文档内容，提供详细的分析报告。")
    
    def test_get_custom_prompt_none(self):
        """Test custom prompt retrieval when none exists"""
        prompt = self.config_manager.get_custom_prompt()
        self.assertIsNone(prompt)
    
    def test_set_and_get_custom_prompt(self):
        """Test setting and getting custom prompt"""
        custom_prompt = "这是一个自定义的分析提示词"
        self.config_manager.set_custom_prompt(custom_prompt)
        
        retrieved_prompt = self.config_manager.get_custom_prompt()
        self.assertEqual(retrieved_prompt, custom_prompt)
    
    def test_set_custom_prompt_empty(self):
        """Test setting empty custom prompt"""
        with self.assertRaises(ValueError):
            self.config_manager.set_custom_prompt("")
        
        with self.assertRaises(ValueError):
            self.config_manager.set_custom_prompt("   ")
    
    def test_set_custom_prompt_too_long(self):
        """Test setting too long custom prompt"""
        long_prompt = "x" * 5001
        with self.assertRaises(ValueError):
            self.config_manager.set_custom_prompt(long_prompt)
    
    def test_get_effective_prompt_default(self):
        """Test effective prompt when no custom prompt is set"""
        prompt = self.config_manager.get_effective_prompt()
        self.assertEqual(prompt, "请分析以下文档内容，提供详细的分析报告。")
    
    def test_get_effective_prompt_custom(self):
        """Test effective prompt when custom prompt is set"""
        custom_prompt = "自定义提示词"
        self.config_manager.set_custom_prompt(custom_prompt)
        
        prompt = self.config_manager.get_effective_prompt()
        self.assertEqual(prompt, custom_prompt)
    
    def test_clear_custom_prompt(self):
        """Test clearing custom prompt"""
        # Set a custom prompt first
        self.config_manager.set_custom_prompt("测试提示词")
        self.assertIsNotNone(self.config_manager.get_custom_prompt())
        
        # Clear it
        self.config_manager.clear_custom_prompt()
        self.assertIsNone(self.config_manager.get_custom_prompt())
    
    def test_get_max_file_size(self):
        """Test max file size retrieval"""
        size = self.config_manager.get_max_file_size()
        self.assertEqual(size, 5242880)
    
    def test_get_supported_formats(self):
        """Test supported formats retrieval"""
        formats = self.config_manager.get_supported_formats()
        expected = ["pdf", "md", "xlsx", "xls", "docx", "doc", "txt"]
        self.assertEqual(formats, expected)
    
    def test_get_siliconflow_config(self):
        """Test SiliconFlow config retrieval"""
        config = self.config_manager.get_siliconflow_config()
        self.assertEqual(config['api_key'], 'sk-test123456789012345678901234567890')
        self.assertEqual(config['base_url'], 'https://api.siliconflow.cn/v1')
    
    def test_get_file_processing_config(self):
        """Test file processing config retrieval"""
        config = self.config_manager.get_file_processing_config()
        self.assertEqual(config['max_file_size'], 5242880)
        self.assertEqual(len(config['supported_formats']), 7)
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation"""
        result = self.config_manager.validate_configuration()
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_configuration_invalid_api_key(self):
        """Test configuration validation with invalid API key"""
        # Create config with invalid API key
        invalid_config = self.test_config.copy()
        invalid_config['siliconflow']['api_key'] = 'invalid-key'
        
        config_file = os.path.join(self.temp_dir, 'invalid_key.json')
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f)
        
        config_manager = ConfigManager(config_file, self.db_file)
        result = config_manager.validate_configuration()
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('API key' in error for error in result['errors']))


if __name__ == '__main__':
    unittest.main()