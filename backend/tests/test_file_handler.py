import unittest
import tempfile
import os
import shutil
from io import BytesIO
from unittest.mock import Mock, patch
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.file_handler import FileUploadHandler, ValidationResult
from werkzeug.datastructures import FileStorage


class TestFileUploadHandler(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock config manager
        self.mock_config = Mock()
        self.mock_config.get_supported_formats.return_value = ['pdf', 'md', 'xlsx', 'xls', 'docx', 'doc', 'txt']
        self.mock_config.get_max_file_size.return_value = 5242880  # 5MB
        self.mock_config.get_temp_dir.return_value = self.temp_dir
        
        self.handler = FileUploadHandler(self.mock_config)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_file(self, filename: str, content: bytes = b"test content", size: int = None) -> FileStorage:
        """Create a test FileStorage object"""
        if size is not None:
            content = b"x" * size
        
        file_obj = BytesIO(content)
        return FileStorage(
            stream=file_obj,
            filename=filename,
            content_type='application/octet-stream'
        )
    
    def test_validate_file_success_pdf(self):
        """Test successful PDF file validation"""
        file = self._create_test_file("test.pdf", b"PDF content")
        result = self.handler.validate_file(file)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, 'pdf')
        self.assertIsNone(result.error_message)
    
    def test_validate_file_success_markdown(self):
        """Test successful Markdown file validation"""
        file = self._create_test_file("test.md", b"# Markdown content")
        result = self.handler.validate_file(file)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, 'md')
    
    def test_validate_file_success_txt(self):
        """Test successful TXT file validation"""
        file = self._create_test_file("test.txt", b"Text content")
        result = self.handler.validate_file(file)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, 'txt')
    
    def test_validate_file_success_excel(self):
        """Test successful Excel file validation"""
        file = self._create_test_file("test.xlsx", b"Excel content")
        result = self.handler.validate_file(file)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, 'xlsx')
    
    def test_validate_file_success_word(self):
        """Test successful Word file validation"""
        file = self._create_test_file("test.docx", b"Word content")
        result = self.handler.validate_file(file)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(result.file_type, 'docx')
    
    def test_validate_file_no_file(self):
        """Test validation with no file"""
        result = self.handler.validate_file(None)
        
        self.assertFalse(result.is_valid)
        self.assertIn("No file provided", result.error_message)
    
    def test_validate_file_no_filename(self):
        """Test validation with no filename"""
        file_obj = BytesIO(b"content")
        file = FileStorage(stream=file_obj, filename="")
        
        result = self.handler.validate_file(file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("No filename provided", result.error_message)
    
    def test_validate_file_too_large(self):
        """Test validation with file too large"""
        # Create file larger than 5MB
        large_size = 6 * 1024 * 1024  # 6MB
        file = self._create_test_file("large.pdf", size=large_size)
        
        result = self.handler.validate_file(file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("exceeds maximum allowed size", result.error_message)
        self.assertEqual(result.file_size, large_size)
    
    def test_validate_file_empty(self):
        """Test validation with empty file"""
        file = self._create_test_file("empty.pdf", b"")
        
        result = self.handler.validate_file(file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("File is empty", result.error_message)
        self.assertEqual(result.file_size, 0)
    
    def test_validate_file_unsupported_format(self):
        """Test validation with unsupported file format"""
        file = self._create_test_file("test.exe", b"executable content")
        
        result = self.handler.validate_file(file)
        
        self.assertFalse(result.is_valid)
        self.assertIn("Unsupported file format", result.error_message)
    
    def test_determine_file_type_by_extension(self):
        """Test file type determination by extension"""
        test_cases = [
            ("test.pdf", "pdf"),
            ("document.docx", "docx"),
            ("spreadsheet.xlsx", "xlsx"),
            ("readme.md", "md"),
            ("data.txt", "txt"),
            ("old_doc.doc", "doc"),
            ("old_excel.xls", "xls"),
        ]
        
        for filename, expected_type in test_cases:
            file = self._create_test_file(filename)
            detected_type = self.handler._determine_file_type(file)
            self.assertEqual(detected_type, expected_type, f"Failed for {filename}")
    
    def test_determine_file_type_markdown_variations(self):
        """Test markdown file type detection with different extensions"""
        test_cases = ["readme.md", "document.markdown"]
        
        for filename in test_cases:
            file = self._create_test_file(filename)
            detected_type = self.handler._determine_file_type(file)
            self.assertEqual(detected_type, "md", f"Failed for {filename}")
    
    def test_save_temp_file(self):
        """Test saving file to temporary storage"""
        file = self._create_test_file("test.pdf", b"PDF content")
        
        file_id, file_path = self.handler.save_temp_file(file)
        
        # Check that file was saved
        self.assertTrue(os.path.exists(file_path))
        self.assertTrue(file_path.startswith(self.temp_dir))
        self.assertIsInstance(file_id, str)
        self.assertTrue(len(file_id) > 0)
        
        # Check file content
        with open(file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b"PDF content")
    
    def test_cleanup_temp_file_success(self):
        """Test successful temporary file cleanup"""
        # Create a temporary file
        file = self._create_test_file("test.pdf", b"content")
        file_id, file_path = self.handler.save_temp_file(file)
        
        # Verify file exists
        self.assertTrue(os.path.exists(file_path))
        
        # Clean up file
        result = self.handler.cleanup_temp_file(file_path)
        
        # Verify cleanup
        self.assertTrue(result)
        self.assertFalse(os.path.exists(file_path))
    
    def test_cleanup_temp_file_not_exists(self):
        """Test cleanup of non-existent file"""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent.pdf")
        result = self.handler.cleanup_temp_file(non_existent_path)
        
        self.assertFalse(result)
    
    def test_get_file_info(self):
        """Test getting file information"""
        # Create a test file
        file = self._create_test_file("test.pdf", b"PDF content")
        file_id, file_path = self.handler.save_temp_file(file)
        
        # Get file info
        info = self.handler.get_file_info(file_path)
        
        # Verify info
        self.assertIn('filename', info)
        self.assertIn('file_type', info)
        self.assertIn('file_size', info)
        self.assertIn('created_at', info)
        self.assertIn('modified_at', info)
        
        self.assertEqual(info['file_type'], 'pdf')
        self.assertEqual(info['file_size'], len(b"PDF content"))
    
    def test_get_file_info_not_exists(self):
        """Test getting info for non-existent file"""
        non_existent_path = os.path.join(self.temp_dir, "nonexistent.pdf")
        info = self.handler.get_file_info(non_existent_path)
        
        self.assertEqual(info, {})
    
    def test_validate_file_path_safe(self):
        """Test file path validation for safe paths"""
        safe_path = os.path.join(self.temp_dir, "safe_file.pdf")
        result = self.handler.validate_file_path(safe_path)
        
        self.assertTrue(result)
    
    def test_validate_file_path_unsafe(self):
        """Test file path validation for unsafe paths"""
        unsafe_path = "/etc/passwd"
        result = self.handler.validate_file_path(unsafe_path)
        
        self.assertFalse(result)
    
    def test_cleanup_old_temp_files(self):
        """Test cleanup of old temporary files"""
        # Create some test files
        file1 = self._create_test_file("old1.pdf", b"content1")
        file2 = self._create_test_file("old2.pdf", b"content2")
        
        _, path1 = self.handler.save_temp_file(file1)
        _, path2 = self.handler.save_temp_file(file2)
        
        # Verify files exist
        self.assertTrue(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))
        
        # Mock old modification times
        import time
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(path1, (old_time, old_time))
        os.utime(path2, (old_time, old_time))
        
        # Clean up old files (24 hour threshold)
        cleaned_count = self.handler.cleanup_old_temp_files(24)
        
        # Verify cleanup
        self.assertEqual(cleaned_count, 2)
        self.assertFalse(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))
    
    def test_handler_without_config_manager(self):
        """Test handler initialization without config manager"""
        handler = FileUploadHandler()
        
        # Should use default values
        self.assertEqual(handler.max_file_size, 5242880)
        self.assertIn('pdf', handler.supported_formats)
        self.assertIn('txt', handler.supported_formats)


if __name__ == '__main__':
    unittest.main()