import os
import uuid
import mimetypes
from typing import Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of file validation"""
    is_valid: bool
    error_message: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None


class FileUploadHandler:
    """Handle file uploads with validation and temporary storage"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.supported_formats = self._get_supported_formats()
        self.max_file_size = self._get_max_file_size()
        self.temp_dir = self._get_temp_dir()
        
        # MIME type mappings for better file type detection
        self.mime_type_mapping = {
            'application/pdf': 'pdf',
            'text/markdown': 'md',
            'text/plain': 'txt',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/vnd.ms-excel': 'xls',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/msword': 'doc',
        }
        
        # File extension mappings as fallback
        self.extension_mapping = {
            '.pdf': 'pdf',
            '.md': 'md',
            '.markdown': 'md',
            '.txt': 'txt',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.docx': 'docx',
            '.doc': 'doc',
        }
    
    def _get_supported_formats(self) -> list:
        """Get supported file formats from config"""
        if self.config_manager:
            return self.config_manager.get_supported_formats()
        return ['pdf', 'md', 'xlsx', 'xls', 'docx', 'doc', 'txt']
    
    def _get_max_file_size(self) -> int:
        """Get maximum file size from config"""
        if self.config_manager:
            return self.config_manager.get_max_file_size()
        return 5242880  # 5MB default
    
    def _get_temp_dir(self) -> str:
        """Get temporary directory from config"""
        if self.config_manager:
            return self.config_manager.get_temp_dir()
        
        temp_dir = 'temp/uploads'
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir
    
    def validate_file(self, file: FileStorage) -> ValidationResult:
        """
        Validate uploaded file for format and size
        
        Args:
            file: Werkzeug FileStorage object
            
        Returns:
            ValidationResult with validation status and details
        """
        if not file:
            return ValidationResult(
                is_valid=False,
                error_message="No file provided"
            )
        
        if not file.filename:
            return ValidationResult(
                is_valid=False,
                error_message="No filename provided"
            )
        
        # Get file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        # Validate file size
        if file_size > self.max_file_size:
            size_mb = self.max_file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                error_message=f"File size ({file_size / (1024 * 1024):.1f}MB) exceeds maximum allowed size ({size_mb:.1f}MB)",
                file_size=file_size
            )
        
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_message="File is empty",
                file_size=file_size
            )
        
        # Determine file type
        file_type = self._determine_file_type(file)
        
        if not file_type:
            return ValidationResult(
                is_valid=False,
                error_message="Could not determine file type",
                file_size=file_size
            )
        
        # Validate file format
        if file_type not in self.supported_formats:
            supported_formats_str = ', '.join(self.supported_formats)
            return ValidationResult(
                is_valid=False,
                error_message=f"Unsupported file format '{file_type}'. Supported formats: {supported_formats_str}",
                file_type=file_type,
                file_size=file_size
            )
        
        return ValidationResult(
            is_valid=True,
            file_type=file_type,
            file_size=file_size
        )
    
    def _determine_file_type(self, file: FileStorage) -> Optional[str]:
        """
        Determine file type using multiple methods
        
        Args:
            file: FileStorage object
            
        Returns:
            File type string or None if cannot be determined
        """
        filename = file.filename.lower()
        
        # Try MIME type first
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type in self.mime_type_mapping:
            return self.mime_type_mapping[mime_type]
        
        # Try file extension as fallback
        for ext, file_type in self.extension_mapping.items():
            if filename.endswith(ext):
                return file_type
        
        # Special handling for markdown files
        if filename.endswith('.md') or filename.endswith('.markdown'):
            return 'md'
        
        return None
    
    def save_temp_file(self, file: FileStorage) -> Tuple[str, str]:
        """
        Save file to temporary storage
        
        Args:
            file: Validated FileStorage object
            
        Returns:
            Tuple of (file_id, file_path)
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Create secure filename
        original_filename = secure_filename(file.filename)
        file_extension = os.path.splitext(original_filename)[1]
        temp_filename = f"{file_id}{file_extension}"
        
        # Create full path
        file_path = os.path.join(self.temp_dir, temp_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        return file_id, file_path
    
    def cleanup_temp_file(self, file_path: str) -> bool:
        """
        Clean up temporary file
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError as e:
            print(f"Error cleaning up temporary file {file_path}: {e}")
            return False
    
    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
            
        Returns:
            Number of files cleaned up
        """
        if not os.path.exists(self.temp_dir):
            return 0
        
        cleaned_count = 0
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        if self.cleanup_temp_file(file_path):
                            cleaned_count += 1
        except OSError as e:
            print(f"Error during temp file cleanup: {e}")
        
        return cleaned_count
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_type = self._determine_file_type_by_path(file_path)
        
        return {
            'filename': filename,
            'file_type': file_type,
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime)
        }
    
    def _determine_file_type_by_path(self, file_path: str) -> Optional[str]:
        """Determine file type by file path"""
        filename = os.path.basename(file_path).lower()
        
        for ext, file_type in self.extension_mapping.items():
            if filename.endswith(ext):
                return file_type
        
        return None
    
    def validate_file_path(self, file_path: str) -> bool:
        """
        Validate that file path is within allowed temporary directory
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Get absolute paths
            abs_file_path = os.path.abspath(file_path)
            abs_temp_dir = os.path.abspath(self.temp_dir)
            
            # Check if file is within temp directory
            return abs_file_path.startswith(abs_temp_dir)
        except Exception:
            return False