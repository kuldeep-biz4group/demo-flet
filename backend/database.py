"""
SQLite Database Manager for Report Generation System
Stores CSV data, report metadata, and generation history
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import os


class DatabaseManager:
    """Manages SQLite database for report generation data"""
    
    def __init__(self, db_path: str = "reports.db"):
        """Initialize database manager"""
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            # Table 1: Report Generations (tracking each generation session)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS report_generations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    file1_name TEXT NOT NULL,
                    file2_name TEXT,
                    total_students INTEGER DEFAULT 0,
                    total_reports INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'processing',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # Table 2: Student Assessments (summary for each student)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_generation_id INTEGER NOT NULL,
                    student_id TEXT NOT NULL,
                    student_name TEXT,
                    grade TEXT,
                    teacher TEXT,
                    school TEXT,
                    assessment_date TEXT,
                    assessment_type TEXT,
                    variant TEXT,
                    composite_score REAL,
                    risk_level TEXT,
                    pdf_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_generation_id) REFERENCES report_generations(id)
                )
            """)
            
            # Table 3: Assessment Data (detailed metrics from CSV)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_generation_id INTEGER NOT NULL,
                    student_assessment_id INTEGER,
                    student_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_text TEXT,
                    assessment_date TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_generation_id) REFERENCES report_generations(id),
                    FOREIGN KEY (student_assessment_id) REFERENCES student_assessments(id)
                )
            """)
            
            # Table 4: Generated Reports (PDF file tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_generation_id INTEGER NOT NULL,
                    student_id TEXT,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_generation_id) REFERENCES report_generations(id)
                )
            """)
            
            # Table 5: System Logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_student_assessments_student_id 
                    ON student_assessments(student_id)
                """)
            except sqlite3.OperationalError:
                pass  # Index or column doesn't exist, skip
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_student_assessments_date 
                    ON student_assessments(assessment_date)
                """)
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_assessment_data_student_id 
                    ON assessment_data(student_id)
                """)
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_report_generations_created 
                    ON report_generations(created_at)
                """)
            except sqlite3.OperationalError:
                pass
    
    def start_report_generation(self, data: Dict) -> int:
        """Start a new report generation session"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO report_generations 
                (report_type, variant, start_date, end_date, file1_name, file2_name, status)
                VALUES (?, ?, ?, ?, ?, ?, 'processing')
            """, (
                data.get('report_type'),
                data.get('variant'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('file1_name'),
                data.get('file2_name')
            ))
            return cursor.lastrowid
    
    def complete_report_generation(self, generation_id: int, total_students: int, total_reports: int):
        """Mark report generation as complete"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE report_generations 
                SET status = 'completed',
                    total_students = ?,
                    total_reports = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (total_students, total_reports, generation_id))
    
    def save_student_assessment(self, data: Dict) -> int:
        """Save student assessment summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO student_assessments 
                (report_generation_id, student_id, student_name, grade, teacher, school,
                 assessment_date, assessment_type, variant, composite_score, risk_level, pdf_filename)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('report_generation_id'),
                data.get('student_id'),
                data.get('student_name'),
                data.get('grade'),
                data.get('teacher'),
                data.get('school'),
                data.get('assessment_date'),
                data.get('assessment_type'),
                data.get('variant'),
                data.get('composite_score'),
                data.get('risk_level'),
                data.get('pdf_filename')
            ))
            return cursor.lastrowid
    
    def save_assessment_data(self, data: Dict):
        """Save detailed assessment metrics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO assessment_data 
                (report_generation_id, student_assessment_id, student_id, 
                 metric_name, metric_value, metric_text, assessment_date, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('report_generation_id'),
                data.get('student_assessment_id'),
                data.get('student_id'),
                data.get('metric_name'),
                data.get('metric_value'),
                data.get('metric_text'),
                data.get('assessment_date'),
                data.get('source_file')
            ))
    
    def save_generated_report(self, data: Dict):
        """Save generated PDF file info"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generated_reports 
                (report_generation_id, student_id, filename, file_path, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data.get('report_generation_id'),
                data.get('student_id'),
                data.get('filename'),
                data.get('file_path'),
                data.get('file_size')
            ))
    
    def log(self, level: str, message: str, details: str = None):
        """Add system log entry"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (level, message, details)
                VALUES (?, ?, ?)
            """, (level, message, details))
    
    def get_recent_generations(self, limit: int = 10) -> List[Dict]:
        """Get recent report generations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM report_generations 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_generation_details(self, generation_id: int) -> Dict:
        """Get details of a specific generation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get generation info
            cursor.execute("""
                SELECT * FROM report_generations WHERE id = ?
            """, (generation_id,))
            generation = dict(cursor.fetchone())
            
            # Get student assessments
            cursor.execute("""
                SELECT * FROM student_assessments 
                WHERE report_generation_id = ?
            """, (generation_id,))
            generation['students'] = [dict(row) for row in cursor.fetchall()]
            
            # Get generated reports
            cursor.execute("""
                SELECT * FROM generated_reports 
                WHERE report_generation_id = ?
            """, (generation_id,))
            generation['reports'] = [dict(row) for row in cursor.fetchall()]
            
            return generation
    
    def get_student_history(self, student_id: str) -> List[Dict]:
        """Get assessment history for a student"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sa.*, rg.report_type, rg.variant, rg.created_at as generation_date
                FROM student_assessments sa
                JOIN report_generations rg ON sa.report_generation_id = rg.id
                WHERE sa.student_id = ?
                ORDER BY sa.assessment_date DESC
            """, (student_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total generations
            cursor.execute("SELECT COUNT(*) as count FROM report_generations")
            stats['total_generations'] = cursor.fetchone()['count']
            
            # Total students
            cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM student_assessments")
            stats['total_students'] = cursor.fetchone()['count']
            
            # Total reports
            cursor.execute("SELECT COUNT(*) as count FROM generated_reports")
            stats['total_reports'] = cursor.fetchone()['count']
            
            # Total assessments
            cursor.execute("SELECT COUNT(*) as count FROM student_assessments")
            stats['total_assessments'] = cursor.fetchone()['count']
            
            return stats


# Global database instance
db = DatabaseManager()
