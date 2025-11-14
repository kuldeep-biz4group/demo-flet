#!/usr/bin/env python
"""
Quick Report Generation CLI Tool
Generate reports directly without starting the web server
"""
import argparse
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.config_loader import ConfigLoader
from backend.core.data_processor import DataProcessor
from backend.core.delta_calculator import DeltaCalculator
from backend.core.risk_analyzer import RiskAnalyzer
from backend.core.pdf_engine import PDFEngine
from backend.core.error_handler import ErrorHandler, ErrorType


def print_banner():
    """Print application banner"""
    print("=" * 70)
    print("  Offline Report Generation System - CLI Tool")
    print("=" * 70)
    print()


def list_report_types(config_loader):
    """List available report types and variants"""
    print("Available Report Types:")
    print("-" * 70)
    
    for report_type in config_loader.list_report_types():
        config = config_loader.get_config(report_type)
        print(f"\n{config.get('report_name', report_type)}")
        print(f"  Type: {report_type}")
        print(f"  Description: {config.get('description', 'N/A')}")
        print(f"\n  Variants:")
        
        for variant in config_loader.list_variants(report_type):
            variant_config = config_loader.get_variant_config(report_type, variant)
            print(f"    - {variant}")
            print(f"      Name: {variant_config.get('name', 'N/A')}")
            print(f"      Grade Range: {variant_config.get('grade_range', 'N/A')}")
            print(f"      Subject: {variant_config.get('subject', 'N/A')}")


def generate_reports(file1_path, file2_path, report_type, variant, output_dir):
    """Generate reports from data files"""
    
    # Initialize config loader
    config_loader = ConfigLoader()
    
    # Validate report type and variant
    available_types = config_loader.list_report_types()
    if report_type not in available_types:
        print(f"❌ Error: Invalid report type '{report_type}'")
        print(f"   Available types: {', '.join(available_types)}")
        return False
    
    available_variants = config_loader.list_variants(report_type)
    if variant not in available_variants:
        print(f"❌ Error: Invalid variant '{variant}'")
        print(f"   Available variants: {', '.join(available_variants)}")
        return False
    
    # Load configuration
    config = config_loader.get_config(report_type)
    variant_config = config_loader.get_variant_config(report_type, variant)
    
    print(f"📋 Report Type: {config.get('report_name', report_type)}")
    print(f"📊 Variant: {variant_config.get('name', variant)}")
    print(f"📁 Input File 1: {file1_path}")
    if file2_path:
        print(f"📁 Input File 2: {file2_path}")
    print(f"📂 Output Directory: {output_dir}")
    print()
    
    # Initialize processors
    data_processor = DataProcessor(config)
    delta_calculator = DeltaCalculator(config)
    risk_analyzer = RiskAnalyzer(config)
    pdf_engine = PDFEngine(config, output_dir=output_dir)
    
    # Read and validate first file
    print("📖 Reading first file...")
    df1, error = data_processor.read_file(file1_path)
    if error:
        print(f"❌ Error reading file: {error}")
        return False
    
    print(f"✓ Read {len(df1)} records from first file")
    
    # Validate first file
    print("🔍 Validating data...")
    is_valid, errors = data_processor.validate_data(df1)
    if not is_valid:
        print("❌ Validation errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✓ Data validation passed")
    
    # Merge with second file if provided
    if file2_path:
        print("📖 Reading second file...")
        df2, error = data_processor.read_file(file2_path)
        if error:
            print(f"❌ Error reading file: {error}")
            return False
        
        print(f"✓ Read {len(df2)} records from second file")
        
        # Validate second file
        is_valid, errors = data_processor.validate_data(df2)
        if not is_valid:
            print("❌ Validation errors in second file:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        # Merge files
        print("🔗 Merging files...")
        df_merged, error = data_processor.merge_data(df1, df2)
        if error:
            print(f"❌ Error merging files: {error}")
            return False
        
        df = df_merged
        print(f"✓ Merged into {len(df)} records")
    else:
        df = df1
    
    # Normalize and sort data
    print("⚙️  Processing data...")
    df = data_processor.normalize_data(df, variant_config)
    df = data_processor.sort_by_date(df)
    
    # Get unique students
    students = data_processor.get_unique_students(df)
    
    if not students:
        print("❌ Error: No student records found in the data")
        return False
    
    print(f"✓ Found {len(students)} students")
    
    # Generate reports
    print(f"\n📝 Generating reports...")
    print("-" * 70)
    
    metrics = variant_config.get('metrics', [])
    generated_count = 0
    
    for i, student_id in enumerate(students, 1):
        student_df = data_processor.get_student_data(df, student_id)
        
        if student_df.empty:
            continue
        
        # Extract student information
        latest_record = student_df.iloc[-1]
        student_name = latest_record.get('student_name', 'Unknown')
        
        print(f"  [{i}/{len(students)}] Generating report for {student_name}...", end=" ")
        
        student_data = {
            'student_id': student_id,
            'student_name': student_name,
            'grade': latest_record.get('grade', 'N/A'),
            'teacher_name': latest_record.get('teacher_name', 'N/A'),
            'school_name': latest_record.get('school_name', 'N/A'),
            'district_name': latest_record.get('district_name', 'N/A'),
            'screening_period': latest_record.get('screening_period', 'N/A')
        }
        
        try:
            # Perform risk analysis
            risk_analysis = risk_analyzer.analyze_student_performance(
                student_df, variant_config
            )
            
            # Generate appropriate report type
            if report_type == 'progress_monitoring':
                delta_results = delta_calculator.calculate_latest_vs_prior(
                    student_df, metrics
                )
                
                pdf_path = pdf_engine.generate_progress_monitoring_report(
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
                
                pdf_path = pdf_engine.generate_screening_report(
                    student_data, variant_config, screening_results, risk_analysis
                )
            
            print(f"✓")
            generated_count += 1
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("-" * 70)
    print(f"\n✅ Successfully generated {generated_count} reports")
    print(f"📂 Reports saved to: {output_dir}")
    
    return True


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate PDF reports from CSV/Excel data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available report types
  python generate_report.py --list

  # Generate progress monitoring report
  python generate_report.py data.csv progress_monitoring early_reading

  # Generate with two files
  python generate_report.py file1.csv progress_monitoring early_reading --file2 file2.csv

  # Specify output directory
  python generate_report.py data.csv screening early_reading --output my_reports
        """
    )
    
    parser.add_argument(
        'file1',
        nargs='?',
        help='First data file (CSV or Excel)'
    )
    
    parser.add_argument(
        'report_type',
        nargs='?',
        help='Report type (progress_monitoring or screening)'
    )
    
    parser.add_argument(
        'variant',
        nargs='?',
        help='Report variant (e.g., early_reading, cbmr_english)'
    )
    
    parser.add_argument(
        '--file2',
        help='Second data file to merge (optional)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='generated_reports',
        help='Output directory for generated reports (default: generated_reports)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available report types and variants'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # List mode
    if args.list:
        config_loader = ConfigLoader()
        list_report_types(config_loader)
        return
    
    # Validate required arguments
    if not args.file1 or not args.report_type or not args.variant:
        parser.print_help()
        print("\n❌ Error: file1, report_type, and variant are required")
        print("   Use --list to see available report types and variants")
        sys.exit(1)
    
    # Check if file exists
    if not os.path.exists(args.file1):
        print(f"❌ Error: File not found: {args.file1}")
        sys.exit(1)
    
    if args.file2 and not os.path.exists(args.file2):
        print(f"❌ Error: File not found: {args.file2}")
        sys.exit(1)
    
    # Generate reports
    success = generate_reports(
        args.file1,
        args.file2,
        args.report_type,
        args.variant,
        args.output
    )
    
    if success:
        print("\n🎉 Report generation complete!")
        sys.exit(0)
    else:
        print("\n❌ Report generation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
