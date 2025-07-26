import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, Mock
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.content_extractor import ContentExtractor, ExtractionResult


class TestContentExtractor(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = ContentExtractor()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_file(self, filename: str, content: str) -> str:
        """Create a test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def _create_binary_test_file(self, filename: str, content: bytes) -> str:
        """Create a binary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    def test_extract_text_success(self):
        """Test successful text file extraction"""
        content = "This is a test text file.\nWith multiple lines.\nAnd some content."
        file_path = self._create_test_file("test.txt", content)
        
        result = self.extractor.extract_text(file_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.content, content)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.metadata['lines'], 3)
        self.assertEqual(result.metadata['encoding'], 'utf-8')
    
    def test_extract_text_empty_file(self):
        """Test text extraction from empty file"""
        file_path = self._create_test_file("empty.txt", "")
        
        result = self.extractor.extract_text(file_path)
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("empty", result.error_message.lower())
    
    def test_extract_text_whitespace_only(self):
        """Test text extraction from file with only whitespace"""
        file_path = self._create_test_file("whitespace.txt", "   \n\t  \n  ")
        
        result = self.extractor.extract_text(file_path)
        
        self.assertFalse(result.success)
        self.assertIn("empty", result.error_message.lower())
    
    def test_extract_markdown_success(self):
        """Test successful markdown file extraction"""
        content = "# Test Markdown\n\nThis is a **test** markdown file.\n\n- Item 1\n- Item 2"
        file_path = self._create_test_file("test.md", content)
        
        result = self.extractor.extract_markdown(file_path)
        
        self.assertTrue(result.success)
        self.assertEqual(result.content, content)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.metadata['lines'], 6)
    
    def test_extract_content_file_not_found(self):
        """Test extraction from non-existent file"""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent.txt")
        
        result = self.extractor.extract_content(non_existent_path, "txt")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("File not found", result.error_message)
    
    def test_extract_content_unsupported_type(self):
        """Test extraction with unsupported file type"""
        file_path = self._create_test_file("test.unknown", "content")
        
        result = self.extractor.extract_content(file_path, "unknown")
        
        self.assertFalse(result.success)
        self.assertEqual(result.content, "")
        self.assertIn("Unsupported file type", result.error_message)
    
    def test_extract_content_routes_correctly(self):
        """Test that extract_content routes to correct extraction method"""
        content = "Test content"
        
        # Test different file types
        test_cases = [
            ("test.txt", "txt"),
            ("test.md", "md"),
        ]
        
        for filename, file_type in test_cases:
            file_path = self._create_test_file(filename, content)
            result = self.extractor.extract_content(file_path, file_type)
            
            self.assertTrue(result.success, f"Failed for {file_type}")
            self.assertEqual(result.content, content, f"Content mismatch for {file_type}")
    
    @patch('services.content_extractor.PyPDF2')
    def test_extract_pdf_library_not_available(self, mock_pypdf2):
        """Test PDF extraction when PyPDF2 is not available"""
        mock_pypdf2 = None
        
        # Temporarily set PyPDF2 to None
        import services.content_extractor
        original_pypdf2 = services.content_extractor.PyPDF2
        services.content_extractor.PyPDF2 = None
        
        try:
            extractor = ContentExtractor()
            file_path = self._create_test_file("test.pdf", "fake pdf content")
            
            result = extractor.extract_pdf(file_path)
            
            self.assertFalse(result.success)
            self.assertIn("PyPDF2 library not available", result.error_message)
        finally:
            # Restore original PyPDF2
            services.content_extractor.PyPDF2 = original_pypdf2
    
    @patch('services.content_extractor.Document')
    def test_extract_word_library_not_available(self, mock_document):
        """Test Word extraction when python-docx is not available"""
        # Temporarily set Document to None
        import services.content_extractor
        original_document = services.content_extractor.Document
        services.content_extractor.Document = None
        
        try:
            extractor = ContentExtractor()
            file_path = self._create_test_file("test.docx", "fake docx content")
            
            result = extractor.extract_word(file_path)
            
            self.assertFalse(result.success)
            self.assertIn("python-docx library not available", result.error_message)
        finally:
            # Restore original Document
            services.content_extractor.Document = original_document
    
    @patch('services.content_extractor.openpyxl')
    def test_extract_excel_library_not_available(self, mock_openpyxl):
        """Test Excel extraction when openpyxl is not available"""
        # Temporarily set openpyxl to None
        import services.content_extractor
        original_openpyxl = services.content_extractor.openpyxl
        services.content_extractor.openpyxl = None
        
        try:
            extractor = ContentExtractor()
            file_path = self._create_test_file("test.xlsx", "fake xlsx content")
            
            result = extractor.extract_excel(file_path)
            
            self.assertFalse(result.success)
            self.assertIn("openpyxl library not available", result.error_message)
        finally:
            # Restore original openpyxl
            services.content_extractor.openpyxl = original_openpyxl
    
    def test_get_supported_formats(self):
        """Test getting supported formats"""
        formats = self.extractor.get_supported_formats()
        
        # These should always be supported
        self.assertTrue(formats['txt'])
        self.assertTrue(formats['md'])
        
        # These depend on library availability
        self.assertIn('pdf', formats)
        self.assertIn('docx', formats)
        self.assertIn('xlsx', formats)
    
    def test_validate_extraction_capability(self):
        """Test validation of extraction capability"""
        # Always supported formats
        self.assertTrue(self.extractor.validate_extraction_capability('txt'))
        self.assertTrue(self.extractor.validate_extraction_capability('md'))
        
        # Unsupported format
        self.assertFalse(self.extractor.validate_extraction_capability('unknown'))
    
    def test_extract_text_encoding_fallback(self):
        """Test text extraction with encoding fallback"""
        # Create a file with latin-1 encoding
        content = "Café résumé naïve"
        file_path = os.path.join(self.temp_dir, "latin1.txt")
        
        with open(file_path, 'w', encoding='latin-1') as f:
            f.write(content)
        
        # Create a file that will fail UTF-8 decoding
        binary_content = b'\xff\xfe\x41\x00\x42\x00'  # UTF-16 BOM + "AB"
        binary_file_path = self._create_binary_test_file("binary.txt", binary_content)
        
        result = self.extractor.extract_text(binary_file_path)
        
        # Should succeed with fallback encoding
        self.assertTrue(result.success)
        self.assertIn('encoding', result.metadata)
    
    def test_extract_markdown_encoding_fallback(self):
        """Test markdown extraction with encoding fallback"""
        # Create a file that will fail UTF-8 decoding
        binary_content = b'\xff\xfe# Title\x00'  # UTF-16 BOM + "# Title"
        binary_file_path = self._create_binary_test_file("binary.md", binary_content)
        
        result = self.extractor.extract_markdown(binary_file_path)
        
        # Should succeed with fallback encoding
        self.assertTrue(result.success)
        self.assertIn('encoding', result.metadata)


if __name__ == '__main__':
    unittest.main()