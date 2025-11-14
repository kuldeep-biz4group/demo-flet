"""
Error Handling Module
Provides user-friendly error messages and validation
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ErrorType(Enum):
    """Types of errors that can occur"""
    FILE_NOT_FOUND = "file_not_found"
    FILE_READ_ERROR = "file_read_error"
    INVALID_FORMAT = "invalid_format"
    MISSING_FIELDS = "missing_fields"
    INVALID_DATA = "invalid_data"
    MERGE_ERROR = "merge_error"
    CALCULATION_ERROR = "calculation_error"
    PDF_GENERATION_ERROR = "pdf_generation_error"
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"


class ErrorHandler:
    """Handles error messages and validation"""
    
    @staticmethod
    def format_error(error_type: ErrorType, details: str = "") -> Dict:
        """
        Format error message for display
        
        Args:
            error_type: Type of error
            details: Additional error details
            
        Returns:
            Error dictionary with message and suggestions
        """
        error_messages = {
            ErrorType.FILE_NOT_FOUND: {
                "title": "File Not Found",
                "message": "The specified file could not be found.",
                "suggestions": [
                    "Check that the file path is correct",
                    "Ensure the file exists in the specified location",
                    "Verify you have permission to access the file"
                ]
            },
            ErrorType.FILE_READ_ERROR: {
                "title": "File Read Error",
                "message": "Unable to read the file.",
                "suggestions": [
                    "Ensure the file is not open in another program",
                    "Check that the file is a valid CSV or Excel file",
                    "Verify the file is not corrupted"
                ]
            },
            ErrorType.INVALID_FORMAT: {
                "title": "Invalid File Format",
                "message": "The file format is not supported.",
                "suggestions": [
                    "Use CSV (.csv) or Excel (.xlsx, .xls) files only",
                    "Check that the file extension matches the file type",
                    "Try exporting the data in a supported format"
                ]
            },
            ErrorType.MISSING_FIELDS: {
                "title": "Missing Required Fields",
                "message": "The file is missing required data columns.",
                "suggestions": [
                    "Ensure all required fields are present in the file",
                    "Check that column names match the expected format",
                    "Verify the file contains the correct data export"
                ]
            },
            ErrorType.INVALID_DATA: {
                "title": "Invalid Data",
                "message": "The file contains invalid or improperly formatted data.",
                "suggestions": [
                    "Check for empty or missing values in required fields",
                    "Verify date formats are consistent (YYYY-MM-DD recommended)",
                    "Ensure numeric fields contain valid numbers"
                ]
            },
            ErrorType.MERGE_ERROR: {
                "title": "Data Merge Error",
                "message": "Unable to merge the two data files.",
                "suggestions": [
                    "Ensure both files contain the merge key field (e.g., Student ID)",
                    "Check that the merge key values match between files",
                    "Verify both files are from the same data source"
                ]
            },
            ErrorType.CALCULATION_ERROR: {
                "title": "Calculation Error",
                "message": "An error occurred during data calculations.",
                "suggestions": [
                    "Ensure all required metric fields contain valid numbers",
                    "Check that dates are in the correct format",
                    "Verify there are at least two assessments for delta calculations"
                ]
            },
            ErrorType.PDF_GENERATION_ERROR: {
                "title": "PDF Generation Error",
                "message": "Unable to generate the PDF report.",
                "suggestions": [
                    "Check that you have write permissions in the output directory",
                    "Ensure there is enough disk space",
                    "Try closing any open PDF files and regenerating"
                ]
            },
            ErrorType.CONFIGURATION_ERROR: {
                "title": "Configuration Error",
                "message": "Report configuration is missing or invalid.",
                "suggestions": [
                    "Verify configuration files exist in the config directory",
                    "Check that configuration files are valid JSON format",
                    "Ensure all required configuration fields are present"
                ]
            },
            ErrorType.VALIDATION_ERROR: {
                "title": "Validation Error",
                "message": "Data validation failed.",
                "suggestions": [
                    "Review the validation errors listed below",
                    "Correct the data issues in the source files",
                    "Ensure data meets the required format specifications"
                ]
            }
        }
        
        error_info = error_messages.get(error_type, {
            "title": "Unknown Error",
            "message": "An unexpected error occurred.",
            "suggestions": ["Please contact support for assistance"]
        })
        
        return {
            "error_type": error_type.value,
            "title": error_info["title"],
            "message": error_info["message"],
            "details": details,
            "suggestions": error_info["suggestions"]
        }
    
    @staticmethod
    def format_validation_errors(errors: List[str]) -> str:
        """
        Format validation errors for display
        
        Args:
            errors: List of error messages
            
        Returns:
            Formatted error string
        """
        if not errors:
            return "No errors"
        
        formatted = "Validation Errors:\n"
        for i, error in enumerate(errors, 1):
            formatted += f"{i}. {error}\n"
        
        return formatted
    
    @staticmethod
    def create_status_message(success: bool, message: str, 
                            details: Optional[str] = None) -> Dict:
        """
        Create status message for GUI display
        
        Args:
            success: Whether operation was successful
            message: Status message
            details: Optional additional details
            
        Returns:
            Status dictionary
        """
        return {
            "success": success,
            "message": message,
            "details": details,
            "timestamp": None  # Will be set by GUI
        }
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file path
        
        Args:
            file_path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import os
        
        if not file_path:
            return False, "File path is empty"
        
        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"
        
        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            return False, f"Unsupported file format: {ext}"
        
        return True, None
    
    @staticmethod
    def validate_report_config(report_type: str, variant: str,
                              available_types: List[str],
                              available_variants: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate report configuration selection
        
        Args:
            report_type: Selected report type
            variant: Selected variant
            available_types: List of available report types
            available_variants: List of available variants
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not report_type:
            return False, "Report type not selected"
        
        if report_type not in available_types:
            return False, f"Invalid report type: {report_type}"
        
        if not variant:
            return False, "Report variant not selected"
        
        if variant not in available_variants:
            return False, f"Invalid variant: {variant}"
        
        return True, None
    
    @staticmethod
    def safe_execute(func, *args, error_type: ErrorType = ErrorType.CALCULATION_ERROR, **kwargs):
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            error_type: Type of error if function fails
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, error_dict or None)
        """
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            error = ErrorHandler.format_error(error_type, str(e))
            return None, error
