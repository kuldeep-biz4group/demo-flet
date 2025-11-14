"""
Batch Processing Utility
Processes multiple files and generates reports in batch
"""
import os
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

from backend.core.config_loader import ConfigLoader
from backend.core.data_processor import DataProcessor
from backend.core.delta_calculator import DeltaCalculator
from backend.core.risk_analyzer import RiskAnalyzer
from backend.core.pdf_engine import PDFEngine
from backend.core.error_handler import ErrorHandler, ErrorType


class BatchProcessor:
    """Process multiple data files and generate reports in batch"""
    
    def __init__(self, output_dir: str = "batch_reports"):
        """
        Initialize batch processor
        
        Args:
            output_dir: Directory for batch output
        """
        self.output_dir = output_dir
        self.config_loader = ConfigLoader()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def process_directory(self, input_dir: str, report_type: str, 
                         variant: str, file_pattern: str = "*.csv") -> Dict:
        """
        Process all files in a directory
        
        Args:
            input_dir: Directory containing input files
            report_type: Type of report to generate
            variant: Report variant
            file_pattern: File pattern to match (default: *.csv)
            
        Returns:
            Processing results dictionary
        """
        import glob
        
        results = {
            'total_files': 0,
            'processed': 0,
            'failed': 0,
            'reports_generated': 0,
            'errors': []
        }
        
        # Find all matching files
        pattern = os.path.join(input_dir, file_pattern)
        files = glob.glob(pattern)
        results['total_files'] = len(files)
        
        if not files:
            results['errors'].append(f"No files found matching pattern: {file_pattern}")
            return results
        
        # Load configuration
        config = self.config_loader.get_config(report_type)
        variant_config = self.config_loader.get_variant_config(report_type, variant)
        
        if not config or not variant_config:
            results['errors'].append(f"Configuration not found for {report_type}/{variant}")
            return results
        
        # Process each file
        for file_path in files:
            try:
                file_results = self.process_single_file(
                    file_path, report_type, variant, config, variant_config
                )
                
                if file_results['success']:
                    results['processed'] += 1
                    results['reports_generated'] += file_results['reports_count']
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'file': os.path.basename(file_path),
                        'error': file_results['error']
                    })
            
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'file': os.path.basename(file_path),
                    'error': str(e)
                })
        
        return results
    
    def process_single_file(self, file_path: str, report_type: str, 
                           variant: str, config: Dict, 
                           variant_config: Dict) -> Dict:
        """
        Process a single file
        
        Args:
            file_path: Path to input file
            report_type: Type of report
            variant: Report variant
            config: Report configuration
            variant_config: Variant configuration
            
        Returns:
            Processing results
        """
        result = {
            'success': False,
            'reports_count': 0,
            'error': None
        }
        
        try:
            # Initialize processors
            data_processor = DataProcessor(config)
            delta_calculator = DeltaCalculator(config)
            risk_analyzer = RiskAnalyzer(config)
            pdf_engine = PDFEngine(config, output_dir=self.output_dir)
            
            # Read and validate file
            df, error = data_processor.read_file(file_path)
            if error:
                result['error'] = error
                return result
            
            is_valid, errors = data_processor.validate_data(df)
            if not is_valid:
                result['error'] = ErrorHandler.format_validation_errors(errors)
                return result
            
            # Normalize and sort data
            df = data_processor.normalize_data(df, variant_config)
            df = data_processor.sort_by_date(df)
            
            # Get unique students
            students = data_processor.get_unique_students(df)
            
            if not students:
                result['error'] = "No student records found"
                return result
            
            # Generate reports for each student
            metrics = variant_config.get('metrics', [])
            
            for student_id in students:
                student_df = data_processor.get_student_data(df, student_id)
                
                if student_df.empty:
                    continue
                
                # Extract student information
                latest_record = student_df.iloc[-1]
                student_data = {
                    'student_id': student_id,
                    'student_name': latest_record.get('student_name', 'Unknown'),
                    'grade': latest_record.get('grade', 'N/A'),
                    'teacher_name': latest_record.get('teacher_name', 'N/A'),
                    'school_name': latest_record.get('school_name', 'N/A'),
                    'district_name': latest_record.get('district_name', 'N/A'),
                    'screening_period': latest_record.get('screening_period', 'N/A')
                }
                
                # Perform risk analysis
                risk_analysis = risk_analyzer.analyze_student_performance(
                    student_df, variant_config
                )
                
                # Generate appropriate report type
                if report_type == 'progress_monitoring':
                    delta_results = delta_calculator.calculate_latest_vs_prior(
                        student_df, metrics
                    )
                    
                    pdf_engine.generate_progress_monitoring_report(
                        student_data, variant_config, delta_results, risk_analysis
                    )
                
                elif report_type == 'screening':
                    screening_results = {
                        'composite_score': latest_record.get('composite_score'),
                        'metrics': {}
                    }
                    
                    for metric in metrics:
                        field = metric['field']
                        if field in latest_record.index:
                            screening_results['metrics'][field] = latest_record[field]
                    
                    pdf_engine.generate_screening_report(
                        student_data, variant_config, screening_results, risk_analysis
                    )
                
                result['reports_count'] += 1
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def generate_summary_report(self, results: Dict, output_file: str = None):
        """
        Generate a summary report of batch processing
        
        Args:
            results: Processing results dictionary
            output_file: Optional output file path
        """
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f'batch_summary_{timestamp}.txt')
        
        with open(output_file, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("BATCH PROCESSING SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total Files: {results['total_files']}\n")
            f.write(f"Successfully Processed: {results['processed']}\n")
            f.write(f"Failed: {results['failed']}\n")
            f.write(f"Reports Generated: {results['reports_generated']}\n\n")
            
            if results['errors']:
                f.write("ERRORS:\n")
                f.write("-" * 60 + "\n")
                for error in results['errors']:
                    if isinstance(error, dict):
                        f.write(f"File: {error['file']}\n")
                        f.write(f"Error: {error['error']}\n\n")
                    else:
                        f.write(f"{error}\n\n")
            
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return output_file


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch process data files and generate reports")
    parser.add_argument("input_dir", help="Directory containing input files")
    parser.add_argument("report_type", help="Report type (progress_monitoring or screening)")
    parser.add_argument("variant", help="Report variant (e.g., early_reading)")
    parser.add_argument("--pattern", default="*.csv", help="File pattern to match")
    parser.add_argument("--output", default="batch_reports", help="Output directory")
    
    args = parser.parse_args()
    
    processor = BatchProcessor(output_dir=args.output)
    
    print(f"Processing files in: {args.input_dir}")
    print(f"Report Type: {args.report_type}")
    print(f"Variant: {args.variant}")
    print(f"Pattern: {args.pattern}")
    print("-" * 60)
    
    results = processor.process_directory(
        args.input_dir,
        args.report_type,
        args.variant,
        args.pattern
    )
    
    print(f"\nTotal Files: {results['total_files']}")
    print(f"Processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
    print(f"Reports Generated: {results['reports_generated']}")
    
    if results['errors']:
        print(f"\nErrors: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            if isinstance(error, dict):
                print(f"  - {error['file']}: {error['error']}")
            else:
                print(f"  - {error}")
    
    # Generate summary report
    summary_file = processor.generate_summary_report(results)
    print(f"\nSummary report saved to: {summary_file}")
