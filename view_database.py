"""
Database Viewer for Report Generation System
View and query the SQLite database
"""

import sqlite3
from datetime import datetime
from typing import List, Dict
import os


class DatabaseViewer:
    """View and query the reports database"""
    
    def __init__(self, db_path: str = "reports.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            print(f"❌ Database not found: {db_path}")
            print(f"   Generate some reports first to create the database.")
            exit(1)
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def show_statistics(self):
        """Show database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        
        # Total generations
        cursor.execute("SELECT COUNT(*) as count FROM report_generations")
        total_gen = cursor.fetchone()['count']
        print(f"Total Report Generations: {total_gen}")
        
        # Total students
        cursor.execute("SELECT COUNT(DISTINCT student_id) as count FROM student_assessments")
        total_students = cursor.fetchone()['count']
        print(f"Unique Students: {total_students}")
        
        # Total assessments
        cursor.execute("SELECT COUNT(*) as count FROM student_assessments")
        total_assessments = cursor.fetchone()['count']
        print(f"Total Assessments: {total_assessments}")
        
        # Total reports
        cursor.execute("SELECT COUNT(*) as count FROM generated_reports")
        total_reports = cursor.fetchone()['count']
        print(f"Total PDF Reports: {total_reports}")
        
        # Total metrics
        cursor.execute("SELECT COUNT(*) as count FROM assessment_data")
        total_metrics = cursor.fetchone()['count']
        print(f"Total Metric Records: {total_metrics}")
        
        # Database size
        db_size = os.path.getsize(self.db_path) / 1024  # KB
        print(f"Database Size: {db_size:.2f} KB")
        
        conn.close()
    
    def show_recent_generations(self, limit: int = 10):
        """Show recent report generations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print(f"📋 RECENT REPORT GENERATIONS (Last {limit})")
        print("="*60)
        
        cursor.execute("""
            SELECT id, report_type, variant, start_date, end_date, 
                   total_students, total_reports, status, created_at
            FROM report_generations
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        if not rows:
            print("No report generations found.")
        else:
            for row in rows:
                print(f"\n🔹 Generation ID: {row['id']}")
                print(f"   Type: {row['report_type']} / {row['variant']}")
                print(f"   Date Range: {row['start_date'] or 'N/A'} to {row['end_date'] or 'N/A'}")
                print(f"   Students: {row['total_students']} | Reports: {row['total_reports']}")
                print(f"   Status: {row['status']}")
                print(f"   Created: {row['created_at']}")
        
        conn.close()
    
    def show_generation_details(self, generation_id: int):
        """Show details of a specific generation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print(f"📄 GENERATION DETAILS - ID: {generation_id}")
        print("="*60)
        
        # Get generation info
        cursor.execute("""
            SELECT * FROM report_generations WHERE id = ?
        """, (generation_id,))
        
        gen = cursor.fetchone()
        if not gen:
            print(f"❌ Generation ID {generation_id} not found.")
            conn.close()
            return
        
        print(f"\n📊 Generation Info:")
        print(f"   Report Type: {gen['report_type']}")
        print(f"   Variant: {gen['variant']}")
        print(f"   Date Range: {gen['start_date'] or 'N/A'} to {gen['end_date'] or 'N/A'}")
        print(f"   Files: {gen['file1_name']}" + (f", {gen['file2_name']}" if gen['file2_name'] else ""))
        print(f"   Status: {gen['status']}")
        print(f"   Created: {gen['created_at']}")
        print(f"   Completed: {gen['completed_at'] or 'N/A'}")
        
        # Get student assessments
        cursor.execute("""
            SELECT * FROM student_assessments 
            WHERE report_generation_id = ?
            ORDER BY student_name
        """, (generation_id,))
        
        students = cursor.fetchall()
        
        print(f"\n👥 Students ({len(students)}):")
        for student in students:
            print(f"\n   🔹 {student['student_name']} (ID: {student['student_id']})")
            print(f"      Grade: {student['grade']} | Teacher: {student['teacher']}")
            print(f"      School: {student['school']}")
            print(f"      Assessment Date: {student['assessment_date']}")
            print(f"      Risk Level: {student['risk_level']}")
            print(f"      PDF: {student['pdf_filename']}")
        
        # Get generated reports
        cursor.execute("""
            SELECT * FROM generated_reports 
            WHERE report_generation_id = ?
        """, (generation_id,))
        
        reports = cursor.fetchall()
        
        print(f"\n📁 Generated PDFs ({len(reports)}):")
        for report in reports:
            size_kb = report['file_size'] / 1024 if report['file_size'] else 0
            print(f"   • {report['filename']} ({size_kb:.2f} KB)")
        
        conn.close()
    
    def show_student_history(self, student_id: str):
        """Show assessment history for a student"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print(f"👤 STUDENT HISTORY - ID: {student_id}")
        print("="*60)
        
        cursor.execute("""
            SELECT sa.*, rg.report_type, rg.variant, rg.created_at as generation_date
            FROM student_assessments sa
            JOIN report_generations rg ON sa.report_generation_id = rg.id
            WHERE sa.student_id = ?
            ORDER BY sa.assessment_date DESC
        """, (student_id,))
        
        assessments = cursor.fetchall()
        
        if not assessments:
            print(f"❌ No assessments found for student ID: {student_id}")
        else:
            first = assessments[0]
            print(f"\nStudent: {first['student_name']}")
            print(f"Total Assessments: {len(assessments)}")
            
            for i, assessment in enumerate(assessments, 1):
                print(f"\n🔹 Assessment {i}:")
                print(f"   Date: {assessment['assessment_date']}")
                print(f"   Type: {assessment['report_type']} / {assessment['variant']}")
                print(f"   Grade: {assessment['grade']}")
                print(f"   Risk Level: {assessment['risk_level']}")
                print(f"   Composite Score: {assessment['composite_score']}")
                print(f"   Generated: {assessment['generation_date']}")
        
        conn.close()
    
    def show_all_students(self):
        """Show all students in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("👥 ALL STUDENTS")
        print("="*60)
        
        cursor.execute("""
            SELECT DISTINCT student_id, student_name, grade, school
            FROM student_assessments
            ORDER BY student_name
        """)
        
        students = cursor.fetchall()
        
        if not students:
            print("No students found.")
        else:
            print(f"\nTotal Students: {len(students)}\n")
            for student in students:
                print(f"• {student['student_name']} (ID: {student['student_id']})")
                print(f"  Grade: {student['grade']} | School: {student['school']}")
        
        conn.close()
    
    def export_to_csv(self, table_name: str, output_file: str):
        """Export table to CSV"""
        import csv
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"❌ No data in table: {table_name}")
            conn.close()
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow([description[0] for description in cursor.description])
            # Write data
            writer.writerows(rows)
        
        print(f"✅ Exported {len(rows)} rows to: {output_file}")
        conn.close()


def main():
    """Main menu"""
    viewer = DatabaseViewer()
    
    while True:
        print("\n" + "="*60)
        print("🗄️  REPORT DATABASE VIEWER")
        print("="*60)
        print("\n1. Show Statistics")
        print("2. Show Recent Generations")
        print("3. Show Generation Details")
        print("4. Show Student History")
        print("5. Show All Students")
        print("6. Export Table to CSV")
        print("7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        
        if choice == '1':
            viewer.show_statistics()
        
        elif choice == '2':
            limit = input("How many recent generations? (default 10): ").strip()
            limit = int(limit) if limit.isdigit() else 10
            viewer.show_recent_generations(limit)
        
        elif choice == '3':
            gen_id = input("Enter Generation ID: ").strip()
            if gen_id.isdigit():
                viewer.show_generation_details(int(gen_id))
            else:
                print("❌ Invalid ID")
        
        elif choice == '4':
            student_id = input("Enter Student ID: ").strip()
            viewer.show_student_history(student_id)
        
        elif choice == '5':
            viewer.show_all_students()
        
        elif choice == '6':
            print("\nAvailable tables:")
            print("  - report_generations")
            print("  - student_assessments")
            print("  - assessment_data")
            print("  - generated_reports")
            print("  - system_logs")
            table = input("Enter table name: ").strip()
            output = input("Enter output filename (e.g., export.csv): ").strip()
            viewer.export_to_csv(table, output)
        
        elif choice == '7':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
