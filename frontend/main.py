import flet as ft
from flet import Colors, Icons
import requests
import os
import webbrowser
from datetime import datetime, timedelta
import subprocess
import sys
import time
import math

API_URL = "http://127.0.0.1:8000"


class OfflineReportGenerator:
    """Wizard-based Report Generator with Date Range and Pagination"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Report Generation Wizard"
        self.page.window_width = 1100
        self.page.window_height = 800
        self.page.window_resizable = True
        self.page.padding = 20
        self.page.scroll = "adaptive"
        
        # Wizard state
        self.current_step = 0
        self.total_steps = 4
        self.step_names = ["Select Files", "Configure Report", "Date Range", "Review & Generate"]
        
        # Data state
        self.selected_file1 = None
        self.selected_file2 = None
        self.report_types = {}
        self.backend_process = None
        self.backend_running = False
        self.start_date = None
        self.end_date = None
        
        # Pagination state
        self.generated_reports = []
        self.current_page = 0
        self.items_per_page = 5
        
        # Initialize UI
        self.setup_ui()
        self.check_backend_status()
    
    def setup_ui(self):
        """Setup wizard-based user interface"""
        
        # Header
        self.header = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(Icons.AUTO_AWESOME, size=40, color=Colors.BLUE_700),
                    ft.Text(
                        "Report Generation Wizard",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.BLUE_700
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text(
                    "Follow the steps to generate your reports",
                    size=14,
                    color=Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=Colors.BLUE_50,
            border_radius=10
        )
        
        # Backend status indicator
        self.backend_status_icon = ft.Icon(Icons.CIRCLE, size=12, color=Colors.RED)
        self.backend_status_text = ft.Text("Backend: Disconnected", size=12, color=Colors.RED)
        self.backend_status = ft.Row([
            self.backend_status_icon,
            self.backend_status_text,
            ft.IconButton(
                icon=Icons.REFRESH,
                icon_size=16,
                tooltip="Refresh status",
                on_click=lambda e: self.check_backend_status()
            ),
            ft.IconButton(
                icon=Icons.PLAY_ARROW,
                icon_size=16,
                tooltip="Start backend",
                on_click=lambda e: self.start_backend()
            )
        ], spacing=5)
        
        # Wizard progress indicator
        self.progress_row = self.create_wizard_progress()
        
        # Content area for wizard steps
        self.content_area = ft.Container(
            content=ft.Column([], scroll="adaptive"),
            padding=20,
            bgcolor=Colors.WHITE,
            border_radius=10,
            border=ft.border.all(1, Colors.GREY_300),
            height=400
        )
        
        # Navigation buttons
        self.prev_button = ft.ElevatedButton(
            "← Previous",
            on_click=self.go_previous,
            disabled=True
        )
        
        self.next_button = ft.ElevatedButton(
            "Next →",
            on_click=self.go_next,
            bgcolor=Colors.BLUE_700,
            color=Colors.WHITE
        )
        
        self.generate_button = ft.ElevatedButton(
            "✓ Generate Reports",
            on_click=self.generate_reports,
            bgcolor=Colors.GREEN_700,
            color=Colors.WHITE,
            visible=False
        )
        
        navigation = ft.Row([
            self.prev_button,
            ft.Container(expand=True),
            self.next_button,
            self.generate_button
        ])
        
        # Status and logs
        self.status_text = ft.Text("Ready", size=14, weight=ft.FontWeight.BOLD, color=Colors.GREEN_700)
        self.log_list = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        self.progress_bar = ft.ProgressBar(width=400, visible=False)
        
        log_section = ft.Container(
            content=ft.Column([
                ft.Text("Activity Log", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(
                    content=self.log_list,
                    height=150,
                    border=ft.border.all(1, Colors.GREY_300),
                    border_radius=5,
                    bgcolor=Colors.GREY_50
                )
            ]),
            padding=10,
            visible=False
        )
        self.log_section = log_section
        
        # Add to page
        self.page.add(
            self.header,
            ft.Container(height=10),
            self.backend_status,
            ft.Container(height=20),
            self.progress_row,
            ft.Container(height=20),
            self.content_area,
            ft.Container(height=20),
            navigation,
            ft.Container(height=10),
            self.progress_bar,
            self.status_text,
            ft.Container(height=10),
            log_section
        )
        
        # Show first step
        self.show_step(0)
        self.load_report_types()
    
    def create_wizard_progress(self):
        """Create wizard progress indicator"""
        steps = []
        for i in range(self.total_steps):
            is_current = (i == 0)
            circle = ft.Container(
                content=ft.Text(str(i + 1), size=16, weight=ft.FontWeight.BOLD, 
                               color=Colors.WHITE if is_current else Colors.GREY_600),
                width=40, height=40, border_radius=20,
                bgcolor=Colors.BLUE_700 if is_current else Colors.GREY_300,
                alignment=ft.alignment.center
            )
            label = ft.Text(self.step_names[i], size=11, 
                           color=Colors.BLUE_700 if is_current else Colors.GREY_600,
                           weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                           text_align=ft.TextAlign.CENTER)
            step_col = ft.Column([circle, label], horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                                spacing=5, width=100)
            steps.append(step_col)
            if i < self.total_steps - 1:
                connector = ft.Container(width=80, height=2, bgcolor=Colors.GREY_300, 
                                        margin=ft.margin.only(top=20))
                steps.append(connector)
        return ft.Row(steps, alignment=ft.MainAxisAlignment.CENTER, spacing=0)
    
    def update_wizard_progress(self):
        """Update wizard progress indicator"""
        steps = []
        for i in range(self.total_steps):
            is_current = (i == self.current_step)
            is_completed = (i < self.current_step)
            
            if is_completed:
                circle_content = ft.Icon(Icons.CHECK, size=20, color=Colors.WHITE)
                circle_color = Colors.GREEN_700
            else:
                circle_content = ft.Text(str(i + 1), size=16, weight=ft.FontWeight.BOLD,
                                        color=Colors.WHITE if is_current else Colors.GREY_600)
                circle_color = Colors.BLUE_700 if is_current else Colors.GREY_300
            
            circle = ft.Container(content=circle_content, width=40, height=40, border_radius=20,
                                 bgcolor=circle_color, alignment=ft.alignment.center)
            
            label_color = Colors.GREEN_700 if is_completed else (Colors.BLUE_700 if is_current else Colors.GREY_600)
            label = ft.Text(self.step_names[i], size=11, color=label_color,
                           weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                           text_align=ft.TextAlign.CENTER)
            
            step_col = ft.Column([circle, label], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=5, width=100)
            steps.append(step_col)
            
            if i < self.total_steps - 1:
                connector_color = Colors.GREEN_700 if is_completed else Colors.GREY_300
                connector = ft.Container(width=80, height=2, bgcolor=connector_color,
                                        margin=ft.margin.only(top=20))
                steps.append(connector)
        
        self.progress_row.controls = steps
        self.page.update()
    
    def show_step(self, step_num):
        """Show specific wizard step"""
        self.current_step = step_num
        self.update_wizard_progress()
        
        self.prev_button.disabled = (step_num == 0)
        self.next_button.visible = (step_num < self.total_steps - 1)
        self.generate_button.visible = (step_num == self.total_steps - 1)
        
        if step_num == 0:
            self.show_file_selection()
        elif step_num == 1:
            self.show_report_configuration()
        elif step_num == 2:
            self.show_date_range_selection()
        elif step_num == 3:
            self.show_review()
        
        self.page.update()
    
    def show_file_selection(self):
        """Step 1: File Selection"""
        self.file1_text = ft.Text("No file selected", size=12, color=Colors.GREY_600)
        self.file1_picker = ft.FilePicker(on_result=self.on_file1_selected)
        self.page.overlay.append(self.file1_picker)
        
        self.file2_text = ft.Text("No file selected (optional)", size=12, color=Colors.GREY_600)
        self.file2_picker = ft.FilePicker(on_result=self.on_file2_selected)
        self.page.overlay.append(self.file2_picker)
        
        if self.selected_file1:
            self.file1_text.value = os.path.basename(self.selected_file1)
            self.file1_text.color = Colors.GREEN_700
        if self.selected_file2:
            self.file2_text.value = os.path.basename(self.selected_file2)
            self.file2_text.color = Colors.GREEN_700
        
        content = ft.Column([
            ft.Text("Step 1: Select Data Files", size=22, weight=ft.FontWeight.BOLD, color=Colors.BLUE_700),
            ft.Divider(),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Primary Data File *", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Required: Main assessment data file", size=12, color=Colors.GREY_600),
                    ft.Container(height=5),
                    ft.Row([
                        ft.ElevatedButton("📁 Select First File", icon=Icons.UPLOAD_FILE,
                                         on_click=lambda e: self.file1_picker.pick_files(
                                             allowed_extensions=["csv", "xlsx", "xls"])),
                        self.file1_text
                    ])
                ]),
                padding=15, bgcolor=Colors.BLUE_50, border_radius=10
            ),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Text("Secondary Data File (Optional)", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Optional: Additional data to merge", size=12, color=Colors.GREY_600),
                    ft.Container(height=5),
                    ft.Row([
                        ft.ElevatedButton("📁 Select Second File", icon=Icons.UPLOAD_FILE,
                                         on_click=lambda e: self.file2_picker.pick_files(
                                             allowed_extensions=["csv", "xlsx", "xls"])),
                        self.file2_text
                    ])
                ]),
                padding=15, bgcolor=Colors.GREY_50, border_radius=10
            )
        ], spacing=5)
        
        self.content_area.content = content
    
    def show_report_configuration(self):
        """Step 2: Report Configuration"""
        self.report_type_dropdown = ft.Dropdown(
            label="Report Type", hint_text="Select report type", options=[],
            on_change=self.on_report_type_changed, width=400
        )
        self.variant_dropdown = ft.Dropdown(
            label="Report Variant", hint_text="Select variant", options=[],
            disabled=True, width=400
        )
        
        content = ft.Column([
            ft.Text("Step 2: Configure Report", size=22, weight=ft.FontWeight.BOLD, color=Colors.BLUE_700),
            ft.Divider(),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Report Type *", size=15, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    self.report_type_dropdown
                ]),
                padding=15, bgcolor=Colors.BLUE_50, border_radius=10
            ),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Text("Report Variant *", size=15, weight=ft.FontWeight.BOLD),
                    ft.Container(height=5),
                    self.variant_dropdown
                ]),
                padding=15, bgcolor=Colors.GREEN_50, border_radius=10
            )
        ], spacing=5)
        
        self.content_area.content = content
        self.load_report_types()
    
    def show_date_range_selection(self):
        """Step 3: Date Range Selection"""
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        # Initialize date values
        if not self.start_date:
            self.start_date = thirty_days_ago.strftime("%Y-%m-%d")
        if not self.end_date:
            self.end_date = today.strftime("%Y-%m-%d")
        
        # Text fields for date display
        self.start_date_field = ft.TextField(
            label="Start Date",
            value=self.start_date,
            width=200,
            read_only=True,
            suffix=ft.IconButton(
                icon=Icons.CALENDAR_MONTH,
                tooltip="Pick start date",
                on_click=lambda e: self.pick_start_date(e)
            )
        )
        
        self.end_date_field = ft.TextField(
            label="End Date",
            value=self.end_date,
            width=200,
            read_only=True,
            suffix=ft.IconButton(
                icon=Icons.CALENDAR_MONTH,
                tooltip="Pick end date",
                on_click=lambda e: self.pick_end_date(e)
            )
        )
        
        content = ft.Column([
            ft.Text("Step 3: Date Range Filter", size=22, weight=ft.FontWeight.BOLD, color=Colors.BLUE_700),
            ft.Divider(),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Text("Quick Select", size=15, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Row([
                        ft.OutlinedButton("Last 7 Days", on_click=lambda e: self.set_date_range(7)),
                        ft.OutlinedButton("Last 30 Days", on_click=lambda e: self.set_date_range(30)),
                        ft.OutlinedButton("Last 90 Days", on_click=lambda e: self.set_date_range(90)),
                        ft.OutlinedButton("All Time", on_click=lambda e: self.set_date_range(None))
                    ], wrap=True)
                ]),
                padding=15, bgcolor=Colors.PURPLE_50, border_radius=10
            ),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Text("📅 Pick Date Range from Calendar", size=15, weight=ft.FontWeight.BOLD),
                    ft.Text("Click the calendar icon to select dates", size=12, color=Colors.GREY_600),
                    ft.Container(height=10),
                    ft.Row([
                        self.start_date_field,
                        ft.Icon(Icons.ARROW_FORWARD, size=24, color=Colors.BLUE_700),
                        self.end_date_field
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ]),
                padding=15, bgcolor=Colors.BLUE_50, border_radius=10
            )
        ], spacing=5)
        
        self.content_area.content = content
    
    def pick_start_date(self, e):
        """Open date picker for start date"""
        def on_change(e):
            if e.control.value:
                self.start_date = e.control.value.strftime("%Y-%m-%d")
                self.start_date_field.value = self.start_date
                self.start_date_picker.open = False
                self.page.update()
        
        def on_dismiss(e):
            self.start_date_picker.open = False
            self.page.update()
        
        # Create date picker if not exists
        if not hasattr(self, 'start_date_picker'):
            self.start_date_picker = ft.DatePicker(
                on_change=on_change,
                on_dismiss=on_dismiss,
                first_date=datetime(2020, 1, 1),
                last_date=datetime.now()
            )
            self.page.overlay.append(self.start_date_picker)
        
        self.start_date_picker.open = True
        self.page.update()
    
    def pick_end_date(self, e):
        """Open date picker for end date"""
        def on_change(e):
            if e.control.value:
                self.end_date = e.control.value.strftime("%Y-%m-%d")
                self.end_date_field.value = self.end_date
                self.end_date_picker.open = False
                self.page.update()
        
        def on_dismiss(e):
            self.end_date_picker.open = False
            self.page.update()
        
        # Create date picker if not exists
        if not hasattr(self, 'end_date_picker'):
            self.end_date_picker = ft.DatePicker(
                on_change=on_change,
                on_dismiss=on_dismiss,
                first_date=datetime(2020, 1, 1),
                last_date=datetime.now()
            )
            self.page.overlay.append(self.end_date_picker)
        
        self.end_date_picker.open = True
        self.page.update()
    
    def show_review(self):
        """Step 4: Review and Generate"""
        file1_name = os.path.basename(self.selected_file1) if self.selected_file1 else "❌ Not selected"
        file2_name = os.path.basename(self.selected_file2) if self.selected_file2 else "Not selected"
        report_type_text = getattr(self.report_type_dropdown, 'value', None) or "❌ Not selected"
        variant_text = getattr(self.variant_dropdown, 'value', None) or "❌ Not selected"
        start_date_text = self.start_date or "Not set (all dates)"
        end_date_text = self.end_date or "Not set (all dates)"
        
        is_ready = self.selected_file1 and hasattr(self, 'report_type_dropdown') and self.report_type_dropdown.value and hasattr(self, 'variant_dropdown') and self.variant_dropdown.value
        
        content = ft.Column([
            ft.Text("Step 4: Review & Generate", size=22, weight=ft.FontWeight.BOLD, color=Colors.BLUE_700),
            ft.Divider(),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.FOLDER_OPEN, size=24, color=Colors.BLUE_700),
                           ft.Text("Data Files", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Container(height=5),
                    ft.Text(f"Primary: {file1_name}", size=13),
                    ft.Text(f"Secondary: {file2_name}", size=13, color=Colors.GREY_600)
                ]),
                padding=15, bgcolor=Colors.BLUE_50, border_radius=10
            ),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.SETTINGS, size=24, color=Colors.GREEN_700),
                           ft.Text("Report Configuration", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Container(height=5),
                    ft.Text(f"Type: {report_type_text}", size=13),
                    ft.Text(f"Variant: {variant_text}", size=13)
                ]),
                padding=15, bgcolor=Colors.GREEN_50, border_radius=10
            ),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.DATE_RANGE, size=24, color=Colors.PURPLE_700),
                           ft.Text("Date Range", size=16, weight=ft.FontWeight.BOLD)]),
                    ft.Container(height=5),
                    ft.Text(f"From: {start_date_text}", size=13),
                    ft.Text(f"To: {end_date_text}", size=13)
                ]),
                padding=15, bgcolor=Colors.PURPLE_50, border_radius=10
            ),
            ft.Container(height=15),
            ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.CHECK_CIRCLE if is_ready else Icons.WARNING, size=24,
                           color=Colors.GREEN_700 if is_ready else Colors.ORANGE_700),
                    ft.Text("Ready to generate!" if is_ready else "Complete required fields",
                           size=14, weight=ft.FontWeight.BOLD,
                           color=Colors.GREEN_900 if is_ready else Colors.ORANGE_900)
                ]),
                padding=15,
                bgcolor=Colors.GREEN_50 if is_ready else Colors.ORANGE_50,
                border_radius=10,
                border=ft.border.all(2, Colors.GREEN_700 if is_ready else Colors.ORANGE_700)
            )
        ], spacing=5)
        
        self.content_area.content = content
        self.generate_button.disabled = not is_ready
    
    def go_previous(self, e):
        """Go to previous step"""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def go_next(self, e):
        """Go to next step with validation"""
        if self.current_step == 0:
            if not self.selected_file1:
                self.add_log("❌ Please select at least the primary data file", Colors.RED)
                return
        elif self.current_step == 1:
            if not hasattr(self, 'report_type_dropdown') or not self.report_type_dropdown.value:
                self.add_log("❌ Please select a report type", Colors.RED)
                return
            if not hasattr(self, 'variant_dropdown') or not self.variant_dropdown.value:
                self.add_log("❌ Please select a report variant", Colors.RED)
                return
        
        if self.current_step < self.total_steps - 1:
            self.show_step(self.current_step + 1)
    
    def set_date_range(self, days):
        """Set date range based on days"""
        today = datetime.now()
        if days is None:
            self.start_date_field.value = ""
            self.end_date_field.value = ""
            self.start_date = None
            self.end_date = None
        else:
            start = today - timedelta(days=days)
            self.start_date_field.value = start.strftime("%Y-%m-%d")
            self.end_date_field.value = today.strftime("%Y-%m-%d")
            self.start_date = self.start_date_field.value
            self.end_date = self.end_date_field.value
        self.page.update()
    
    def add_log(self, message: str, color: str = None):
        """Add a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = ft.Text(
            f"[{timestamp}] {message}",
            size=12,
            color=color or Colors.BLACK
        )
        self.log_list.controls.append(log_entry)
        self.page.update()
    
    def check_backend_status(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                self.backend_running = True
                self.backend_status_icon.color = Colors.GREEN
                self.backend_status_text.value = "Backend: Connected"
                self.backend_status_text.color = Colors.GREEN
                self.add_log("✓ Backend connected successfully", Colors.GREEN_700)
            else:
                self.backend_running = False
                self.backend_status_icon.color = Colors.RED
                self.backend_status_text.value = "Backend: Error"
                self.backend_status_text.color = Colors.RED
        except:
            self.backend_running = False
            self.backend_status_icon.color = Colors.RED
            self.backend_status_text.value = "Backend: Disconnected"
            self.backend_status_text.color = Colors.RED
            self.add_log("⚠ Backend not running. Click play button to start.", Colors.ORANGE_700)
        
        self.page.update()
    
    def start_backend(self):
        """Start the backend server"""
        if self.backend_running:
            self.add_log("Backend is already running", Colors.BLUE_700)
            return
        
        try:
            self.add_log("Starting backend server...", Colors.BLUE_700)
            
            # Try to start backend using uvicorn
            if sys.platform == "win32":
                # Windows
                self.backend_process = subprocess.Popen(
                    ["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # macOS/Linux
                self.backend_process = subprocess.Popen(
                    ["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Wait a moment for server to start
            time.sleep(2)
            self.check_backend_status()
            
            if self.backend_running:
                self.add_log("✓ Backend started successfully", Colors.GREEN_700)
                self.load_report_types()
        except Exception as e:
            self.add_log(f"✗ Failed to start backend: {str(e)}", Colors.RED)
            self.add_log("Please start backend manually: uvicorn backend.main:app --reload", Colors.ORANGE_700)
    
    def load_report_types(self):
        """Load available report types from backend"""
        if not self.backend_running:
            return
        
        try:
            response = requests.get(f"{API_URL}/api/report-types", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.report_types = data.get('report_types', {})
                
                # Populate report type dropdown
                self.report_type_dropdown.options = [
                    ft.dropdown.Option(key=rt_key, text=rt_data['name'])
                    for rt_key, rt_data in self.report_types.items()
                ]
                
                self.add_log(f"✓ Loaded {len(self.report_types)} report types", Colors.GREEN_700)
                self.page.update()
        except Exception as e:
            self.add_log(f"✗ Failed to load report types: {str(e)}", Colors.RED)
    
    def on_report_type_changed(self, e):
        """Handle report type selection change"""
        selected_type = self.report_type_dropdown.value
        
        if selected_type and selected_type in self.report_types:
            variants = self.report_types[selected_type].get('variants', [])
            
            self.variant_dropdown.options = [
                ft.dropdown.Option(
                    key=v['id'],
                    text=f"{v['name']} ({v['grade_range']})"
                )
                for v in variants
            ]
            self.variant_dropdown.disabled = False
            self.variant_dropdown.value = None
            
            self.add_log(f"Selected: {self.report_types[selected_type]['name']}", Colors.BLUE_700)
        else:
            self.variant_dropdown.options = []
            self.variant_dropdown.disabled = True
        
        self.page.update()
    
    def on_file1_selected(self, e: ft.FilePickerResultEvent):
        """Handle first file selection"""
        if e.files:
            self.selected_file1 = e.files[0].path
            self.file1_text.value = os.path.basename(self.selected_file1)
            self.file1_text.color = Colors.GREEN_700
            self.add_log(f"✓ File 1 selected: {os.path.basename(self.selected_file1)}", Colors.GREEN_700)
        else:
            self.selected_file1 = None
            self.file1_text.value = "No file selected"
            self.file1_text.color = Colors.GREY_600
        
        self.page.update()
    
    def on_file2_selected(self, e: ft.FilePickerResultEvent):
        """Handle second file selection"""
        if e.files:
            self.selected_file2 = e.files[0].path
            self.file2_text.value = os.path.basename(self.selected_file2)
            self.file2_text.color = Colors.GREEN_700
            self.add_log(f"✓ File 2 selected: {os.path.basename(self.selected_file2)}", Colors.GREEN_700)
        else:
            self.selected_file2 = None
            self.file2_text.value = "No file selected (optional)"
            self.file2_text.color = Colors.GREY_600
        
        self.page.update()
    
    def generate_reports(self, e):
        """Generate PDF reports"""
        if not self.selected_file1:
            self.add_log("✗ Please select at least one data file", Colors.RED)
            return
        
        if not self.report_type_dropdown.value or not self.variant_dropdown.value:
            self.add_log("✗ Please select report type and variant", Colors.RED)
            return
        
        # Show progress
        self.progress_bar.visible = True
        self.generate_button.disabled = True
        self.log_section.visible = True
        self.status_text.value = "Generating reports..."
        self.status_text.color = Colors.BLUE_700
        self.page.update()
        
        try:
            # Prepare files
            files = {
                'file1': (os.path.basename(self.selected_file1), open(self.selected_file1, 'rb'))
            }
            
            if self.selected_file2:
                files['file2'] = (os.path.basename(self.selected_file2), open(self.selected_file2, 'rb'))
            
            # Prepare data
            data = {
                'report_type': self.report_type_dropdown.value,
                'variant': self.variant_dropdown.value
            }
            
            # Add date range if specified
            if self.start_date:
                data['start_date'] = self.start_date
                self.add_log(f"📅 Start date: {self.start_date}", Colors.GREY_700)
            if self.end_date:
                data['end_date'] = self.end_date
                self.add_log(f"📅 End date: {self.end_date}", Colors.GREY_700)
            
            self.add_log("📤 Uploading files and generating reports...", Colors.BLUE_700)
            
            # Send request
            response = requests.post(
                f"{API_URL}/api/generate-report",
                files=files,
                data=data,
                timeout=60
            )
            
            # Close file handles
            for file_tuple in files.values():
                file_tuple[1].close()
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'application/pdf' in content_type:
                    # Single PDF returned
                    output_dir = "generated_reports"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"Report_{timestamp}.pdf"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    self.add_log(f"✓ Report generated: {filename}", Colors.GREEN_700)
                    self.status_text.value = "Report generated successfully!"
                    self.status_text.color = Colors.GREEN_700
                    
                    # Ask to open file
                    self.show_success_dialog(filepath)
                
                else:
                    # Multiple reports generated
                    result = response.json()
                    message = result.get('message', 'Reports generated')
                    files_list = result.get('files', [])
                    output_dir = result.get('output_directory', 'generated_reports')
                    
                    self.add_log(f"✓ {message}", Colors.GREEN_700)
                    for filename in files_list:
                        self.add_log(f"  - {filename}", Colors.GREEN_700)
                    
                    self.status_text.value = message
                    self.status_text.color = Colors.GREEN_700
                    self.show_success_dialog(output_dir, multiple=True)
            
            else:
                # Error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    error_details = error_data.get('details', '')
                    suggestions = error_data.get('suggestions', [])
                    
                    self.add_log(f"✗ Error: {error_msg}", Colors.RED)
                    if error_details:
                        self.add_log(f"  Details: {error_details}", Colors.ORANGE_700)
                    for suggestion in suggestions:
                        self.add_log(f"  💡 {suggestion}", Colors.BLUE_700)
                    
                    self.status_text.value = "Report generation failed"
                    self.status_text.color = Colors.RED
                except:
                    self.add_log(f"✗ Error: {response.text}", Colors.RED)
                    self.status_text.value = "Report generation failed"
                    self.status_text.color = Colors.RED
        
        except Exception as ex:
            self.add_log(f"✗ Exception: {str(ex)}", Colors.RED)
            self.status_text.value = "Report generation failed"
            self.status_text.color = Colors.RED
        
        finally:
            self.progress_bar.visible = False
            self.generate_button.disabled = False
            self.page.update()
    
    def show_success_dialog(self, path: str, multiple: bool = False):
        """Show success dialog with option to open file/folder"""
        if multiple:
            message = f"Reports have been generated successfully!\n\nLocation: {path}"
            button_text = "Open Folder"
        else:
            message = f"Report has been generated successfully!\n\nSaved to: {path}"
            button_text = "Open Report"
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        def open_file(e):
            if multiple:
                self.open_folder(path)
            else:
                webbrowser.open(path)
            close_dialog(e)
        
        dialog = ft.AlertDialog(
            title=ft.Text("✅ Success!"),
            content=ft.Text(message),
            actions=[
                ft.TextButton(button_text, on_click=open_file),
                ft.TextButton("Close", on_click=close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def open_folder(self, path: str):
        """Open folder in file explorer"""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.add_log(f"✗ Failed to open folder: {str(e)}", Colors.RED)
    
    def open_output_folder(self, e):
        """Open the output folder"""
        output_dir = "generated_reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.open_folder(output_dir)
        self.add_log("📂 Opened output folder", Colors.BLUE_700)


def main(page: ft.Page):
    """Main entry point"""
    app = OfflineReportGenerator(page)


ft.app(target=main)
