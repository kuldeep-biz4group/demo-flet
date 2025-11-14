"""
Data Processing Module
Handles CSV/Excel file reading, merging, and validation
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import os


class DataProcessor:
    """Handles all data processing operations for report generation"""
    
    def __init__(self, config: Dict):
        """
        Initialize data processor with configuration
        
        Args:
            config: Report configuration dictionary
        """
        self.config = config
        self.input_mapping = config.get('input_mapping', {})
        self.required_fields = self.input_mapping.get('required_fields', [])
        self.date_format = self.input_mapping.get('date_format', '%Y-%m-%d')
        self.merge_key = self.input_mapping.get('merge_key', 'student_id')
        
    def read_file(self, file_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Read CSV or Excel file into DataFrame
        
        Args:
            file_path: Path to the input file
            
        Returns:
            Tuple of (DataFrame, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return None, f"File not found: {file_path}"
            
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                return None, f"Unsupported file format: {file_ext}. Please use CSV or Excel files."
            
            if df.empty:
                return None, "File is empty or contains no data"
            
            # Clean column names (strip whitespace, lowercase)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            return df, None
            
        except Exception as e:
            return None, f"Error reading file: {str(e)}"
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame has required fields and proper data
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for required fields
        missing_fields = []
        for field in self.required_fields:
            field_normalized = field.lower().replace(' ', '_')
            if field_normalized not in df.columns:
                missing_fields.append(field)
        
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check for empty required fields
        for field in self.required_fields:
            field_normalized = field.lower().replace(' ', '_')
            if field_normalized in df.columns:
                null_count = df[field_normalized].isnull().sum()
                if null_count > 0:
                    errors.append(f"Field '{field}' has {null_count} empty values")
        
        # Validate date fields
        date_fields = ['assessment_date', 'test_date', 'date']
        for date_field in date_fields:
            if date_field in df.columns:
                valid_dates, date_errors = self._validate_dates(df, date_field)
                if date_errors:
                    errors.extend(date_errors)
        
        return len(errors) == 0, errors
    
    def _validate_dates(self, df: pd.DataFrame, date_column: str) -> Tuple[bool, List[str]]:
        """
        Validate date column format
        
        Args:
            df: DataFrame containing dates
            date_column: Name of date column
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Try to parse dates
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            
            # Check for invalid dates
            invalid_count = df[date_column].isnull().sum()
            if invalid_count > 0:
                errors.append(f"Found {invalid_count} invalid dates in '{date_column}' column")
            
        except Exception as e:
            errors.append(f"Error parsing dates in '{date_column}': {str(e)}")
        
        return len(errors) == 0, errors
    
    def merge_data(self, df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Merge two DataFrames on the merge key
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            Tuple of (merged_DataFrame, error_message)
        """
        try:
            # Check if merge key exists in both DataFrames
            merge_key_normalized = self.merge_key.lower().replace(' ', '_')
            
            if merge_key_normalized not in df1.columns:
                return None, f"Merge key '{self.merge_key}' not found in first file"
            
            if merge_key_normalized not in df2.columns:
                return None, f"Merge key '{self.merge_key}' not found in second file"
            
            # Perform outer merge to keep all records
            merged_df = pd.merge(
                df1, 
                df2, 
                on=merge_key_normalized, 
                how='outer',
                suffixes=('_file1', '_file2'),
                indicator=True
            )
            
            # Check for merge issues
            left_only = (merged_df['_merge'] == 'left_only').sum()
            right_only = (merged_df['_merge'] == 'right_only').sum()
            
            warnings = []
            if left_only > 0:
                warnings.append(f"{left_only} records only in first file")
            if right_only > 0:
                warnings.append(f"{right_only} records only in second file")
            
            # Remove merge indicator column
            merged_df = merged_df.drop('_merge', axis=1)
            
            return merged_df, None
            
        except Exception as e:
            return None, f"Error merging data: {str(e)}"
    
    def normalize_data(self, df: pd.DataFrame, variant_config: Dict) -> pd.DataFrame:
        """
        Normalize data according to variant configuration
        
        Args:
            df: DataFrame to normalize
            variant_config: Configuration for specific report variant
            
        Returns:
            Normalized DataFrame
        """
        metrics = variant_config.get('metrics', [])
        
        for metric in metrics:
            field = metric['field']
            metric_type = metric.get('type', 'numeric')
            precision = metric.get('precision', 1)
            
            if field in df.columns:
                # Convert to numeric, coercing errors to NaN
                df[field] = pd.to_numeric(df[field], errors='coerce')
                
                # Round to specified precision
                if metric_type == 'percentage':
                    df[field] = df[field].round(precision)
                elif metric_type == 'numeric':
                    df[field] = df[field].round(precision)
        
        return df
    
    def filter_by_date_range(self, df: pd.DataFrame, date_column: str, 
                            start_date: Optional[str] = None, 
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: DataFrame to filter
            date_column: Name of date column
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Filtered DataFrame
        """
        if date_column not in df.columns:
            return df
        
        # Ensure dates are datetime
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            df = df[df[date_column] >= start_dt]
        
        if end_date:
            end_dt = pd.to_datetime(end_date)
            df = df[df[date_column] <= end_dt]
        
        return df
    
    def sort_by_date(self, df: pd.DataFrame, date_column: str = 'assessment_date', 
                     ascending: bool = True) -> pd.DataFrame:
        """
        Sort DataFrame by date column (flexible - tries multiple column names)
        
        Args:
            df: DataFrame to sort
            date_column: Name of date column
            ascending: Sort order
            
        Returns:
            Sorted DataFrame
        """
        # Try the specified column first
        if date_column in df.columns:
            try:
                df = df.sort_values(by=date_column, ascending=ascending)
                return df
            except Exception as e:
                print(f"Warning: Could not sort by {date_column}: {e}")
        
        # Try alternative date column names
        for col_name in ['assessment_date', 'test_date', 'date', 'Date', 'Assessment Date']:
            if col_name in df.columns:
                try:
                    df = df.sort_values(by=col_name, ascending=ascending)
                    print(f"Sorted by {col_name}")
                    return df
                except Exception as e:
                    continue
        
        print("Warning: No date column found for sorting")
        return df
    
    def get_unique_students(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of unique student IDs
        
        Args:
            df: DataFrame containing student data
            
        Returns:
            List of unique student IDs
        """
        merge_key_normalized = self.merge_key.lower().replace(' ', '_')
        
        # Try the configured merge key first
        if merge_key_normalized in df.columns:
            students = df[merge_key_normalized].dropna().unique().tolist()
            if students:
                return students
        
        # Try common student ID column names
        possible_columns = ['student_id', 'studentid', 'id', 'student', 'student_number']
        for col in possible_columns:
            if col in df.columns:
                students = df[col].dropna().unique().tolist()
                if students:
                    print(f"Found students using column: {col}")
                    return students
        
        # If still no students found, print available columns for debugging
        print(f"WARNING: No student ID column found!")
        print(f"Available columns: {df.columns.tolist()}")
        print(f"Looking for: {merge_key_normalized} or {possible_columns}")
        
        return []
    
    def get_student_data(self, df: pd.DataFrame, student_id: str) -> pd.DataFrame:
        """
        Get all data for a specific student
        
        Args:
            df: DataFrame containing all student data
            student_id: Student ID to filter
            
        Returns:
            DataFrame with student's data
        """
        merge_key_normalized = self.merge_key.lower().replace(' ', '_')
        
        # Try the configured merge key first
        if merge_key_normalized in df.columns:
            return df[df[merge_key_normalized] == student_id].copy()
        
        # Try common student ID column names
        possible_columns = ['student_id', 'studentid', 'id', 'student', 'student_number']
        for col in possible_columns:
            if col in df.columns:
                return df[df[col] == student_id].copy()
        
        return pd.DataFrame()
