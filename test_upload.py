#!/usr/bin/env python3
"""
Test file upload and analysis functionality
"""

import requests
import json
import time

def test_file_upload_analysis():
    """Test file upload and AI analysis"""
    
    print("🔧 Testing File Upload and Analysis...")
    print("=" * 50)
    
    try:
        # Test file path
        test_file_path = "test_document.txt"
        
        # 1. Test file upload and analysis
        print("1. Testing file upload and analysis...")
        
        with open(test_file_path, 'rb') as file:
            files = {'file': (test_file_path, file, 'text/plain')}
            data = {'custom_prompt': '请分析这个文档的主要内容，并提供简洁的总结。'}
            
            print(f"   ✓ Uploading file: {test_file_path}")
            print("   ✓ Starting analysis...")
            
            response = requests.post(
                'http://localhost:5000/api/ai-analysis/upload',
                files=files,
                data=data,
                timeout=180  # 3 minutes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Upload and analysis PASSED")
                print(f"   ✓ File ID: {result.get('file_id', 'N/A')}")
                print(f"   ✓ Analysis ID: {result.get('analysis_id', 'N/A')}")
                print(f"   ✓ Status: {result.get('status', 'N/A')}")
                
                # Display analysis result
                report = result.get('report', {})
                if report:
                    analysis_text = report.get('analysis', '')
                    if isinstance(analysis_text, str) and len(analysis_text) > 0:
                        preview = analysis_text[:200] if len(analysis_text) > 200 else analysis_text
                        print(f"   ✓ Analysis preview: {preview}...")
                    else:
                        print("   ✓ Analysis completed (no preview available)")
                    
                return True
            else:
                print(f"   ❌ Upload failed with status {response.status_code}")
                print(f"   ✗ Error: {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout - analysis took too long")
        return False
    except Exception as e:
        print(f"   ❌ Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_file_upload_analysis()
    if success:
        print("\n" + "=" * 50)
        print("🎉 File upload and analysis test PASSED!")
    else:
        print("\n" + "=" * 50)
        print("❌ File upload and analysis test FAILED!")