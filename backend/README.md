# Offline Report Generation System - Backend

## Overview

This backend system provides a modular, configuration-driven architecture for converting Excel/CSV data exports into professionally formatted PDF reports. It operates entirely offline with no external dependencies or cloud services.

## Architecture

### Core Modules

1. **ConfigLoader** (`core/config_loader.py`)
   - Loads and manages JSON configuration files
   - Supports multiple report types and variants
   - Validates configuration completeness

2. **DataProcessor** (`core/data_processor.py`)
   - Reads CSV and Excel files
   - Validates data structure and content
   - Merges multiple data sources
   - Normalizes data according to configuration

3. **DeltaCalculator** (`core/delta_calculator.py`)
   - Calculates growth metrics for progress monitoring
   - Compares latest vs. prior assessments
   - Determines trend directions
   - Validates bi-weekly assessment schedules

4. **RiskAnalyzer** (`core/risk_analyzer.py`)
   - Determines risk levels based on thresholds
   - Assigns readiness indicators for screening reports
   - Generates intervention recommendations
   - Calculates composite scores and percentile ranks

5. **PDFEngine** (`core/pdf_engine.py`)
   - Generates professionally formatted PDF reports
   - Supports both progress monitoring and screening formats
   - Applies color-coded risk indicators
   - Includes "Understanding This Report" page

6. **ErrorHandler** (`core/error_handler.py`)
   - Provides user-friendly error messages
   - Validates inputs and configurations
   - Handles exceptions gracefully

## Configuration Files

Configuration files are stored in `backend/config/` and define:

- Report types (Progress Monitoring, Screening)
- Variants (Early Reading, CBMR English, Early Math, CBM Math, etc.)
- Metrics and their properties
- Risk thresholds
- PDF layout and styling
- Understanding page content

### Configuration Structure

```json
{
  "report_type": "progress_monitoring",
  "report_name": "Progress Monitoring Report",
  "variants": {
    "early_reading": {
      "name": "Early Reading Progress Monitoring",
      "grade_range": "K-1",
      "subject": "Reading",
      "metrics": [...],
      "risk_thresholds": {...}
    }
  },
  "input_mapping": {...},
  "calculation_rules": {...},
  "pdf_layout": {...},
  "understanding_page": {...}
}
```

## API Endpoints

### GET `/`
Root endpoint with API information

### GET `/health`
Health check endpoint

### GET `/api/report-types`
Returns available report types and variants

**Response:**
```json
{
  "success": true,
  "report_types": {
    "progress_monitoring": {
      "name": "Progress Monitoring Report",
      "description": "...",
      "variants": [...]
    },
    "screening": {...}
  }
}
```

### POST `/api/generate-report`
Generate PDF report from uploaded data files

**Parameters:**
- `file1` (file): First data file (CSV or Excel) - Required
- `file2` (file): Second data file (optional)
- `report_type` (string): Report type - Required
- `variant` (string): Report variant - Required
- `output_format` (string): Output format (default: "pdf")

**Response:**
- Single report: Returns PDF file
- Multiple reports: Returns JSON with file list

### GET `/api/validate-config`
Validate report configuration

**Parameters:**
- `report_type` (string): Report type to validate

## Data File Requirements

### Required Fields

All data files must include:
- `student_id`: Unique student identifier
- `student_name`: Student's full name
- `grade`: Grade level
- `assessment_date`: Date of assessment (YYYY-MM-DD format)
- `teacher_name`: Teacher's name
- `school_name`: School name

### Progress Monitoring Additional Fields

Metric fields vary by variant but typically include:
- `words_read_correct`: WRC/min score
- `accuracy`: Accuracy percentage
- Additional subject-specific metrics

### Screening Additional Fields

- `screening_period`: BOY, MOY, or EOY
- `district_name`: District name
- `composite_score`: Overall composite score
- Subject-specific metric scores

### Date Format

Dates should be in `YYYY-MM-DD` format (e.g., 2024-03-15)

## Error Handling

The system provides user-friendly error messages for:
- File not found
- Invalid file format
- Missing required fields
- Invalid data
- Merge errors
- Calculation errors
- PDF generation errors
- Configuration errors

Each error includes:
- Error type
- Title
- Message
- Details
- Suggestions for resolution

## Adding New Report Types

To add a new report type:

1. Create a new configuration file in `backend/config/`
2. Define report structure, metrics, and thresholds
3. Add variant configurations
4. Specify PDF layout preferences
5. Include understanding page content

No code changes required - the system automatically loads new configurations.

## Modifying Existing Reports

To modify report text, labels, or formatting:

1. Edit the appropriate configuration file in `backend/config/`
2. Update metric labels, thresholds, or layout settings
3. Modify understanding page content
4. Save changes - no restart required

## Running the Backend

### Development Mode

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Testing

### Test Configuration Validation

```bash
curl http://localhost:8000/api/validate-config?report_type=progress_monitoring
```

### Test Report Generation

```bash
curl -X POST http://localhost:8000/api/generate-report \
  -F "file1=@sample_data.csv" \
  -F "report_type=progress_monitoring" \
  -F "variant=early_reading" \
  -o report.pdf
```

## Output

Generated PDF reports are saved to `generated_reports/` directory with timestamped filenames:
- Progress Monitoring: `ProgressMonitoring_StudentName_YYYYMMDD_HHMMSS.pdf`
- Screening: `Screening_PERIOD_StudentName_YYYYMMDD_HHMMSS.pdf`

## Dependencies

See `requirements.txt` for complete list:
- FastAPI: Web framework
- Pandas: Data processing
- ReportLab: PDF generation
- Uvicorn: ASGI server
- OpenPyXL: Excel file support

## Offline Operation

The system operates completely offline:
- No internet connection required
- No external API calls
- All processing done locally
- All assets stored locally

## Scalability

The modular architecture supports:
- Easy addition of new report types
- Configuration-driven customization
- Batch processing of multiple students
- Future enhancements without code changes

## Security

- No data is transmitted externally
- All files processed locally
- Temporary files cleaned up automatically
- No persistent storage of sensitive data
