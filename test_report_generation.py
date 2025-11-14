"""
Quick Test Script - Generate Report via API
Tests if backend can generate reports
"""

import requests
import os

# Configuration
API_URL = "http://127.0.0.1:8000"
SAMPLE_FILE = "backend/sample_data/progress_monitoring_sample.csv"

print("="*60)
print("TESTING REPORT GENERATION")
print("="*60)

# Step 1: Check backend health
print("\n1. Checking backend health...")
try:
    response = requests.get(f"{API_URL}/health", timeout=2)
    if response.status_code == 200:
        print("   ✅ Backend is running")
    else:
        print(f"   ❌ Backend returned: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Backend not running: {e}")
    print("   Please start backend: uvicorn backend.main:app --reload")
    exit(1)

# Step 2: Get report types
print("\n2. Getting report types...")
try:
    response = requests.get(f"{API_URL}/api/report-types", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Found {len(data.get('report_types', {}))} report types")
    else:
        print(f"   ❌ Failed to get report types: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 3: Generate report
print("\n3. Generating report...")
print(f"   File: {SAMPLE_FILE}")
print(f"   Type: progress_monitoring")
print(f"   Variant: early_reading")

if not os.path.exists(SAMPLE_FILE):
    print(f"   ❌ Sample file not found: {SAMPLE_FILE}")
    exit(1)

try:
    with open(SAMPLE_FILE, 'rb') as f:
        files = {
            'file1': (os.path.basename(SAMPLE_FILE), f, 'text/csv')
        }
        data = {
            'report_type': 'progress_monitoring',
            'variant': 'early_reading',
            'output_format': 'pdf'
        }
        
        print("   📤 Sending request...")
        response = requests.post(
            f"{API_URL}/api/generate-report",
            files=files,
            data=data,
            timeout=60
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            if 'application/pdf' in content_type:
                # Single PDF
                output_file = "test_report.pdf"
                with open(output_file, 'wb') as out:
                    out.write(response.content)
                print(f"   ✅ PDF generated: {output_file}")
                print(f"   Size: {len(response.content)} bytes")
            else:
                # Multiple PDFs
                result = response.json()
                print(f"   ✅ {result.get('message')}")
                print(f"   Files: {result.get('files')}")
                print(f"   Directory: {result.get('output_directory')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('message')}")
                print(f"   Details: {error_data.get('details')}")
            except:
                print(f"   Response: {response.text[:200]}")
                
except Exception as e:
    print(f"   ❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
