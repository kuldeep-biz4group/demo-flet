from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import os
import tempfile
import shutil
from datetime import datetime
import pandas as pd

from backend.core.config_loader import ConfigLoader
from backend.core.data_processor import DataProcessor
from backend.core.delta_calculator import DeltaCalculator
from backend.core.risk_analyzer import RiskAnalyzer
from backend.core.pdf_engine import PDFEngine
from backend.core.error_handler import ErrorHandler, ErrorType
# from backend.database import db  # Disabled for now - focus on PDF generation

app = FastAPI(
    title="Offline Report Generation System",
    description="Converts Excel/CSV data exports into professionally formatted PDF reports",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration loader
config_loader = ConfigLoader()


@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Offline Report Generation System API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "report_types": "/api/report-types",
            "generate_report": "/api/generate-report"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_loaded": len(config_loader.list_report_types()) > 0
    }


@app.get("/api/report-types")
def get_report_types():
    """Get available report types and variants"""
    try:
        report_types = {}
        
        for report_type in config_loader.list_report_types():
            config = config_loader.get_config(report_type)
            variants = config_loader.list_variants(report_type)
            
            report_types[report_type] = {
                "name": config.get('report_name', report_type),
                "description": config.get('description', ''),
                "variants": [
                    {
                        "id": variant,
                        "name": config_loader.get_variant_display_name(report_type, variant),
                        "grade_range": config_loader.get_variant_config(report_type, variant).get('grade_range', ''),
                        "subject": config_loader.get_variant_config(report_type, variant).get('subject', '')
                    }
                    for variant in variants
                ]
            }
        
        return {
            "success": True,
            "report_types": report_types
        }
    
    except Exception as e:
        error = ErrorHandler.format_error(ErrorType.CONFIGURATION_ERROR, str(e))
        return JSONResponse(status_code=500, content=error)


@app.post("/api/generate-report")
async def generate_report(
    file1: UploadFile = File(..., description="First data file (CSV or Excel)"),
    file2: Optional[UploadFile] = File(None, description="Second data file (optional)"),
    report_type: str = Form(..., description="Report type (progress_monitoring or screening)"),
    variant: str = Form(..., description="Report variant (e.g., early_reading, cbmr_english)"),
    start_date: Optional[str] = Form(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[str] = Form(None, description="End date for filtering (YYYY-MM-DD)"),
    output_format: str = Form("pdf", description="Output format (currently only PDF supported)")
):
    """Generate report from uploaded data files"""
    
    temp_files = []
    
    try:
        # Validate report configuration
        available_types = config_loader.list_report_types()
        available_variants = config_loader.list_variants(report_type) if report_type in available_types else []
        
        is_valid, error_msg = ErrorHandler.validate_report_config(
            report_type, variant, available_types, available_variants
        )
        
        if not is_valid:
            error = ErrorHandler.format_error(ErrorType.CONFIGURATION_ERROR, error_msg)
            return JSONResponse(status_code=400, content=error)
        
        # Load configuration
        config = config_loader.get_config(report_type)
        variant_config = config_loader.get_variant_config(report_type, variant)
        
        if not config or not variant_config:
            error = ErrorHandler.format_error(
                ErrorType.CONFIGURATION_ERROR,
                f"Configuration not found for {report_type}/{variant}"
            )
            return JSONResponse(status_code=500, content=error)
        
        # Save uploaded files temporarily
        temp_dir = tempfile.mkdtemp()
        
        file1_path = os.path.join(temp_dir, file1.filename)
        with open(file1_path, 'wb') as f:
            shutil.copyfileobj(file1.file, f)
        temp_files.append(file1_path)
        
        file2_path = None
        if file2:
            file2_path = os.path.join(temp_dir, file2.filename)
            with open(file2_path, 'wb') as f:
                shutil.copyfileobj(file2.file, f)
            temp_files.append(file2_path)
        
        # Initialize processors
        data_processor = DataProcessor(config)
        delta_calculator = DeltaCalculator(config)
        risk_analyzer = RiskAnalyzer(config)
        pdf_engine = PDFEngine(config)
        
        # Read and validate first file
        df1, error = data_processor.read_file(file1_path)
        if error:
            error_dict = ErrorHandler.format_error(ErrorType.FILE_READ_ERROR, error)
            return JSONResponse(status_code=400, content=error_dict)
        
        is_valid, errors = data_processor.validate_data(df1)
        if not is_valid:
            error_details = ErrorHandler.format_validation_errors(errors)
            error_dict = ErrorHandler.format_error(ErrorType.VALIDATION_ERROR, error_details)
            return JSONResponse(status_code=400, content=error_dict)
        
        # Merge with second file if provided
        if file2_path:
            df2, error = data_processor.read_file(file2_path)
            if error:
                error_dict = ErrorHandler.format_error(ErrorType.FILE_READ_ERROR, error)
                return JSONResponse(status_code=400, content=error_dict)
            
            is_valid, errors = data_processor.validate_data(df2)
            if not is_valid:
                error_details = ErrorHandler.format_validation_errors(errors)
                error_dict = ErrorHandler.format_error(ErrorType.VALIDATION_ERROR, error_details)
                return JSONResponse(status_code=400, content=error_dict)
            
            df_merged, error = data_processor.merge_data(df1, df2)
            if error:
                error_dict = ErrorHandler.format_error(ErrorType.MERGE_ERROR, error)
                return JSONResponse(status_code=400, content=error_dict)
            
            df = df_merged
        else:
            df = df1
        
        # Normalize data
        df = data_processor.normalize_data(df, variant_config)
        
        # Sort by date
        df = data_processor.sort_by_date(df)
        
        # Apply date range filter if provided
        if start_date or end_date:
            # Find date column (try multiple names)
            date_col = None
            for col_name in ['assessment_date', 'test_date', 'date', 'Date', 'Assessment Date']:
                if col_name in df.columns:
                    date_col = col_name
                    break
            
            if date_col:
                try:
                    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                    
                    if start_date:
                        filter_start = pd.to_datetime(start_date)
                        df = df[df[date_col] >= filter_start]
                    
                    if end_date:
                        filter_end = pd.to_datetime(end_date)
                        df = df[df[date_col] <= filter_end]
                    
                    print(f"Applied date filter using column: {date_col}")
                except Exception as e:
                    print(f"Warning: Could not apply date filter: {e}")
            else:
                print("Warning: No date column found for filtering")
        
        # Get unique students
        students = data_processor.get_unique_students(df)
        
        # Database tracking disabled for now - focus on PDF generation
        print(f"Starting report generation: {report_type}/{variant}")
        print(f"Students found: {len(students)}")
        
        if not students:
            error = ErrorHandler.format_error(
                ErrorType.INVALID_DATA,
                "No student records found in the data"
            )
            return JSONResponse(status_code=400, content=error)
        
        # Generate reports for each student
        generated_files = []
        metrics = variant_config.get('metrics', [])
        
        for student_id in students:
            try:
                student_df = data_processor.get_student_data(df, student_id)
                
                if student_df.empty:
                    print(f"Warning: No data found for student {student_id}, skipping")
                    continue
                
                # Extract student information (safely handle missing fields)
                latest_record = student_df.iloc[-1]
                
                # Helper function to safely get field value
                def safe_get(record, field_name, default='N/A'):
                    try:
                        value = record.get(field_name, default)
                        if pd.isna(value) or value == '' or value is None:
                            return default
                        return value
                    except:
                        return default
                
                student_data = {
                    'student_id': student_id,
                    'student_name': safe_get(latest_record, 'student_name', 'Unknown'),
                    'grade': safe_get(latest_record, 'grade'),
                    'teacher_name': safe_get(latest_record, 'teacher_name'),
                    'school_name': safe_get(latest_record, 'school_name'),
                    'district_name': safe_get(latest_record, 'district_name'),
                    'screening_period': safe_get(latest_record, 'screening_period')
                }
                
                # Perform risk analysis (safely)
                try:
                    risk_analysis = risk_analyzer.analyze_student_performance(student_df, variant_config)
                except Exception as e:
                    print(f"Warning: Risk analysis failed for {student_id}: {e}")
                    risk_analysis = {'overall_risk': 'N/A'}
                
                # Generate appropriate report type
                if report_type == 'progress_monitoring':
                    # Calculate deltas (safely)
                    try:
                        delta_results = delta_calculator.calculate_latest_vs_prior(
                            student_df, metrics
                        )
                    except Exception as e:
                        print(f"Warning: Delta calculation failed for {student_id}: {e}")
                        delta_results = {}
                    
                    # Generate PDF
                    pdf_path = pdf_engine.generate_progress_monitoring_report(
                        student_data, variant_config, delta_results, risk_analysis
                    )
                    
                elif report_type == 'screening':
                    # Prepare screening results (safely)
                    screening_results = {
                        'composite_score': safe_get(latest_record, 'composite_score', 0),
                        'metrics': {}
                    }
                    
                    for metric in metrics:
                        field = metric['field']
                        try:
                            if field in latest_record.index:
                                value = latest_record[field]
                                if not pd.isna(value):
                                    screening_results['metrics'][field] = value
                        except:
                            continue
                    
                    # Generate PDF
                    pdf_path = pdf_engine.generate_screening_report(
                        student_data, variant_config, screening_results, risk_analysis
                    )
                
                generated_files.append(pdf_path)
                print(f"✅ Generated PDF for {student_data['student_name']}: {os.path.basename(pdf_path)}")
                
            except Exception as e:
                print(f"❌ Error generating report for student {student_id}: {e}")
                print(f"   Continuing with next student...")
                continue
        
        # Report generation complete
        print(f"\n✅ Successfully generated {len(generated_files)} reports for {len(students)} students")
        
        # Check if at least one PDF was generated
        if not generated_files:
            error = ErrorHandler.format_error(
                ErrorType.PDF_GENERATION_ERROR,
                "No reports could be generated. Check backend console for details."
            )
            return JSONResponse(status_code=500, content=error)
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        # Return first generated file (or create a zip if multiple)
        if len(generated_files) == 1:
            return FileResponse(
                generated_files[0],
                media_type="application/pdf",
                filename=os.path.basename(generated_files[0])
            )
        else:
            # For multiple files, return success message with file list
            return {
                "success": True,
                "message": f"Generated {len(generated_files)} reports",
                "files": [os.path.basename(f) for f in generated_files],
                "output_directory": os.path.dirname(generated_files[0]) if generated_files else None
            }
    
    except Exception as e:
        # Log detailed error
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*60}")
        print(f"ERROR IN REPORT GENERATION:")
        print(f"{'='*60}")
        print(f"Error: {str(e)}")
        print(f"\nFull traceback:")
        print(error_details)
        print(f"{'='*60}\n")
        
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
        
        error = ErrorHandler.format_error(ErrorType.PDF_GENERATION_ERROR, str(e))
        return JSONResponse(status_code=500, content=error)


@app.get("/api/validate-config")
def validate_config(report_type: str):
    """Validate report configuration"""
    try:
        is_valid, errors = config_loader.validate_config(report_type)
        
        return {
            "success": is_valid,
            "report_type": report_type,
            "errors": errors if not is_valid else []
        }
    
    except Exception as e:
        error = ErrorHandler.format_error(ErrorType.CONFIGURATION_ERROR, str(e))
        return JSONResponse(status_code=500, content=error)
