import unittest
import json
from datetime import datetime
from unittest.mock import Mock
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.report_generator import ReportGenerator, Report
from services.siliconflow_client import AnalysisResult


class TestReportGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.generator = ReportGenerator()
        
        # Create sample analysis result
        self.success_analysis = AnalysisResult(
            success=True,
            content="这是一个测试分析结果。文档包含重要信息，建议进一步处理。",
            processing_time=2.5,
            model_used="gpt-3.5-turbo",
            tokens_used=150,
            metadata={"response_id": "test-123", "finish_reason": "stop"}
        )
        
        self.failed_analysis = AnalysisResult(
            success=False,
            content="",
            error_message="API调用失败",
            processing_time=1.0
        )
        
        # Create sample file metadata
        self.file_metadata = {
            'filename': 'test_document.pdf',
            'file_type': 'pdf',
            'file_size': 1024000,
            'upload_time': '2024-01-15T10:00:00',
            'prompt_used': '请分析这个文档',
            'extraction_metadata': {'pages': 5, 'has_text': True}
        }
    
    def test_generate_report_success(self):
        """Test generating report from successful analysis"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata, 
            "test-report-123"
        )
        
        self.assertEqual(report.id, "test-report-123")
        self.assertEqual(report.status, "completed")
        self.assertEqual(report.file_info['filename'], 'test_document.pdf')
        self.assertEqual(report.file_info['file_type'], 'pdf')
        self.assertEqual(report.file_info['file_size'], 1024000)
        
        self.assertTrue(report.analysis['success'])
        self.assertEqual(report.analysis['content'], self.success_analysis.content)
        self.assertEqual(report.analysis['processing_time'], 2.5)
        self.assertEqual(report.analysis['model_used'], "gpt-3.5-turbo")
        self.assertEqual(report.analysis['tokens_used'], 150)
        self.assertEqual(report.analysis['prompt_used'], '请分析这个文档')
        
        self.assertIsNotNone(report.metadata)
        self.assertIn('analysis_metadata', report.metadata)
        self.assertIn('file_metadata', report.metadata)
        self.assertIn('generation_info', report.metadata)
    
    def test_generate_report_failure(self):
        """Test generating report from failed analysis"""
        report = self.generator.generate_report(
            self.failed_analysis, 
            self.file_metadata
        )
        
        self.assertEqual(report.status, "failed")
        self.assertFalse(report.analysis['success'])
        self.assertEqual(report.analysis['content'], "")
        self.assertEqual(report.analysis['error_message'], "API调用失败")
        self.assertEqual(report.analysis['processing_time'], 1.0)
    
    def test_generate_report_auto_id(self):
        """Test generating report with auto-generated ID"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        
        self.assertIsNotNone(report.id)
        self.assertTrue(len(report.id) > 0)
    
    def test_format_html_report_success(self):
        """Test HTML formatting for successful analysis"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata, 
            "test-html-123"
        )
        
        html_output = self.generator.format_html_report(report)
        
        # Check that HTML contains expected elements
        self.assertIn('<!DOCTYPE html>', html_output)
        self.assertIn('AI文档分析报告', html_output)
        self.assertIn('test_document.pdf', html_output)
        self.assertIn('PDF', html_output)
        self.assertIn('分析成功', html_output)
        self.assertIn('这是一个测试分析结果', html_output)
        self.assertIn('gpt-3.5-turbo', html_output)
        self.assertIn('test-html-123', html_output)
        
        # Check for proper HTML escaping
        self.assertNotIn('<script>', html_output)  # Should be escaped if present
    
    def test_format_html_report_failure(self):
        """Test HTML formatting for failed analysis"""
        report = self.generator.generate_report(
            self.failed_analysis, 
            self.file_metadata
        )
        
        html_output = self.generator.format_html_report(report)
        
        self.assertIn('分析失败', html_output)
        self.assertIn('API调用失败', html_output)
        self.assertIn('error-message', html_output)
    
    def test_format_json_report(self):
        """Test JSON formatting"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata, 
            "test-json-123"
        )
        
        json_output = self.generator.format_json_report(report)
        
        # Verify structure
        self.assertEqual(json_output['id'], "test-json-123")
        self.assertEqual(json_output['status'], "completed")
        self.assertIn('file_info', json_output)
        self.assertIn('analysis', json_output)
        self.assertIn('metadata', json_output)
        self.assertIn('created_at', json_output)
        self.assertEqual(json_output['report_version'], '1.0')
        
        # Verify file info
        self.assertEqual(json_output['file_info']['filename'], 'test_document.pdf')
        self.assertEqual(json_output['file_info']['file_type'], 'pdf')
        
        # Verify analysis data
        self.assertTrue(json_output['analysis']['success'])
        self.assertEqual(json_output['analysis']['content'], self.success_analysis.content)
    
    def test_format_summary_report(self):
        """Test summary formatting"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata, 
            "test-summary-123"
        )
        
        summary_output = self.generator.format_summary_report(report)
        
        # Verify structure
        self.assertEqual(summary_output['id'], "test-summary-123")
        self.assertEqual(summary_output['filename'], 'test_document.pdf')
        self.assertEqual(summary_output['file_type'], 'pdf')
        self.assertEqual(summary_output['status'], "completed")
        self.assertTrue(summary_output['success'])
        self.assertEqual(summary_output['processing_time'], 2.5)
        self.assertEqual(summary_output['tokens_used'], 150)
        
        # Verify summary content
        self.assertIn('summary', summary_output)
        self.assertTrue(len(summary_output['summary']) > 0)
    
    def test_extract_summary_short_content(self):
        """Test summary extraction from short content"""
        short_content = "这是一个简短的分析结果。"
        summary = self.generator._extract_summary(short_content, 200)
        
        self.assertEqual(summary, short_content)
    
    def test_extract_summary_long_content(self):
        """Test summary extraction from long content"""
        long_content = "这是一个非常长的分析结果。" * 20  # Very long content
        summary = self.generator._extract_summary(long_content, 50)
        
        self.assertTrue(len(summary) <= 53)  # 50 + "..."
        self.assertTrue(summary.endswith('...'))
    
    def test_extract_summary_empty_content(self):
        """Test summary extraction from empty content"""
        summary = self.generator._extract_summary("", 200)
        self.assertEqual(summary, "无内容")
        
        summary = self.generator._extract_summary(None, 200)
        self.assertEqual(summary, "无内容")
    
    def test_export_report_json(self):
        """Test exporting report as JSON"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        
        exported = self.generator.export_report(report, 'json')
        
        # Should be valid JSON
        parsed = json.loads(exported)
        self.assertIn('id', parsed)
        self.assertIn('file_info', parsed)
        self.assertIn('analysis', parsed)
    
    def test_export_report_html(self):
        """Test exporting report as HTML"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        
        exported = self.generator.export_report(report, 'html')
        
        self.assertIn('<!DOCTYPE html>', exported)
        self.assertIn('AI文档分析报告', exported)
    
    def test_export_report_summary(self):
        """Test exporting report as summary"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        
        exported = self.generator.export_report(report, 'summary')
        
        # Should be valid JSON
        parsed = json.loads(exported)
        self.assertIn('summary', parsed)
        self.assertIn('filename', parsed)
    
    def test_export_report_invalid_format(self):
        """Test exporting report with invalid format"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        
        with self.assertRaises(ValueError):
            self.generator.export_report(report, 'invalid_format')
    
    def test_validate_report_valid(self):
        """Test validating a valid report"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata, 
            "valid-report-123"
        )
        
        validation = self.generator.validate_report(report)
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
    
    def test_validate_report_missing_id(self):
        """Test validating report with missing ID"""
        report = self.generator.generate_report(
            self.success_analysis, 
            self.file_metadata
        )
        report.id = ""  # Clear ID
        
        validation = self.generator.validate_report(report)
        
        self.assertFalse(validation['valid'])
        self.assertIn("Report ID is missing", validation['errors'])
    
    def test_validate_report_missing_filename(self):
        """Test validating report with missing filename"""
        metadata_no_filename = self.file_metadata.copy()
        del metadata_no_filename['filename']
        
        report = self.generator.generate_report(
            self.success_analysis, 
            metadata_no_filename
        )
        
        validation = self.generator.validate_report(report)
        
        self.assertFalse(validation['valid'])
        self.assertIn("Filename is missing", validation['errors'])
    
    def test_validate_report_failed_analysis_no_error(self):
        """Test validating failed analysis without error message"""
        failed_analysis_no_error = AnalysisResult(
            success=False,
            content="",
            error_message="",  # Empty error message
            processing_time=1.0
        )
        
        report = self.generator.generate_report(
            failed_analysis_no_error, 
            self.file_metadata
        )
        
        validation = self.generator.validate_report(report)
        
        # Should still be valid but have warnings
        self.assertTrue(validation['valid'])
        self.assertIn("no error message provided", validation['warnings'][0])
    
    def test_validate_report_negative_processing_time(self):
        """Test validating report with negative processing time"""
        negative_time_analysis = AnalysisResult(
            success=True,
            content="Test content",
            processing_time=-1.0  # Negative time
        )
        
        report = self.generator.generate_report(
            negative_time_analysis, 
            self.file_metadata
        )
        
        validation = self.generator.validate_report(report)
        
        # Should still be valid but have warnings
        self.assertTrue(validation['valid'])
        self.assertIn("Processing time is negative", validation['warnings'][0])
    
    def test_html_escaping_security(self):
        """Test that HTML output properly escapes potentially dangerous content"""
        malicious_analysis = AnalysisResult(
            success=True,
            content="<script>alert('xss')</script>这是恶意内容",
            processing_time=1.0
        )
        
        malicious_metadata = self.file_metadata.copy()
        malicious_metadata['filename'] = '<img src=x onerror=alert(1)>.pdf'
        malicious_metadata['prompt_used'] = '<script>alert("prompt")</script>'
        
        report = self.generator.generate_report(
            malicious_analysis, 
            malicious_metadata
        )
        
        html_output = self.generator.format_html_report(report)
        
        # Check that dangerous content is escaped
        self.assertNotIn('<script>alert(', html_output)
        self.assertNotIn('<img src=x onerror=', html_output)
        self.assertIn('&lt;script&gt;', html_output)  # Should be escaped


if __name__ == '__main__':
    unittest.main()