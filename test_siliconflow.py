#!/usr/bin/env python3
"""
Test script for SiliconFlow API connection
"""

import sys
import os
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.config_manager import ConfigManager
from services.siliconflow_client import SiliconFlowClient

def test_siliconflow_connection():
    """Test SiliconFlow API connection and basic functionality"""
    
    print("🔧 Testing SiliconFlow Connection...")
    print("=" * 50)
    
    try:
        # 1. Load configuration
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        siliconflow_config = config_manager.get_siliconflow_config()
        
        print(f"   ✓ API Base URL: {siliconflow_config['base_url']}")
        print(f"   ✓ Model: {siliconflow_config['model']}")
        print(f"   ✓ API Key: {siliconflow_config['api_key'][:10]}...{siliconflow_config['api_key'][-4:]}")
        
        # 2. Initialize client
        print("\n2. Initializing SiliconFlow client...")
        client = SiliconFlowClient(
            api_key=siliconflow_config['api_key'],
            base_url=siliconflow_config['base_url'],
            model=siliconflow_config['model'],
            max_tokens=siliconflow_config.get('max_tokens', 2000),
            temperature=siliconflow_config.get('temperature', 0.7),
            timeout=siliconflow_config.get('timeout', 120)
        )
        print("   ✓ Client initialized successfully")
        
        # 3. Test connection
        print("\n3. Testing API connection...")
        test_result = client.test_connection()
        
        if test_result['success']:
            print("   ✅ Connection test PASSED")
            print(f"   ✓ Response time: {test_result['response_time']:.2f}s")
            print(f"   ✓ API accessible: {test_result['api_accessible']}")
            print(f"   ✓ Authentication valid: {test_result['authentication_valid']}")
        else:
            print("   ❌ Connection test FAILED")
            print(f"   ✗ Error: {test_result['error_message']}")
            print(f"   ✗ Response time: {test_result.get('response_time', 'N/A')}")
            return False
        
        # 4. Test basic analysis
        print("\n4. Testing basic analysis...")
        test_content = "这是一个测试文档。请分析这个简单的文本内容。"
        
        analysis_result = client.analyze_content(test_content)
        
        if analysis_result.success:
            print("   ✅ Analysis test PASSED")
            print(f"   ✓ Processing time: {analysis_result.processing_time:.2f}s")
            print(f"   ✓ Model used: {analysis_result.model_used}")
            print(f"   ✓ Tokens used: {analysis_result.tokens_used}")
            print(f"   ✓ Analysis content length: {len(analysis_result.content)} characters")
            print(f"   ✓ Analysis preview: {analysis_result.content[:100]}...")
        else:
            print("   ❌ Analysis test FAILED")
            print(f"   ✗ Error: {analysis_result.error_message}")
            return False
        
        # 5. Test with custom prompt
        print("\n5. Testing with custom prompt...")
        custom_prompt = "请用简洁的方式总结以下内容的主要观点："
        
        custom_analysis_result = client.analyze_content(test_content, custom_prompt)
        
        if custom_analysis_result.success:
            print("   ✅ Custom prompt test PASSED")
            print(f"   ✓ Processing time: {custom_analysis_result.processing_time:.2f}s")
            print(f"   ✓ Analysis preview: {custom_analysis_result.content[:100]}...")
        else:
            print("   ❌ Custom prompt test FAILED")
            print(f"   ✗ Error: {custom_analysis_result.error_message}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests PASSED! SiliconFlow is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_siliconflow_connection()
    sys.exit(0 if success else 1)