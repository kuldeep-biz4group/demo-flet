"""
PDF Generation Engine
Creates professionally formatted PDF reports
"""
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


class PDFEngine:
    """Professional PDF report generator"""
    
    def __init__(self, config: Dict, output_dir: str = "generated_reports"):
        """
        Initialize PDF engine
        
        Args:
            config: Report configuration dictionary
            output_dir: Directory for output PDFs
        """
        self.config = config
        self.output_dir = output_dir
        self.pdf_layout = config.get('pdf_layout', {})
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Setup page size
        page_size_name = self.pdf_layout.get('page_size', 'LETTER')
        self.page_size = letter if page_size_name == 'LETTER' else A4
        
        # Setup margins
        margins = self.pdf_layout.get('margins', {})
        self.margin_top = margins.get('top', 0.75) * inch
        self.margin_bottom = margins.get('bottom', 0.75) * inch
        self.margin_left = margins.get('left', 0.75) * inch
        self.margin_right = margins.get('right', 0.75) * inch
        
        # Setup styles
        self.styles = self._create_styles()
        
        # Setup colors
        self.colors = self.pdf_layout.get('colors', {})
    
    def _create_styles(self) -> Dict:
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        fonts = self.pdf_layout.get('fonts', {})
        
        # Title style
        title_font = fonts.get('title', {})
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=title_font.get('size', 16),
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        heading_font = fonts.get('heading', {})
        styles.add(ParagraphStyle(
            name='ReportHeading',
            parent=styles['Heading2'],
            fontSize=heading_font.get('size', 12),
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body style
        body_font = fonts.get('body', {})
        styles.add(ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontSize=body_font.get('size', 10),
            textColor=colors.HexColor('#000000'),
            spaceAfter=6,
            fontName='Helvetica'
        ))
        
        # Small text style
        small_font = fonts.get('small', {})
        styles.add(ParagraphStyle(
            name='ReportSmall',
            parent=styles['Normal'],
            fontSize=small_font.get('size', 8),
            textColor=colors.HexColor('#666666'),
            fontName='Helvetica'
        ))
        
        return styles
    
    def generate_progress_monitoring_report(self, student_data: Dict, 
                                           variant_config: Dict,
                                           delta_results: Dict,
                                           risk_analysis: Dict) -> str:
        """
        Generate progress monitoring PDF report
        
        Args:
            student_data: Student information dictionary
            variant_config: Report variant configuration
            delta_results: Delta calculation results
            risk_analysis: Risk analysis results
            
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        student_name = student_data.get('student_name', 'Unknown').replace(' ', '_')
        filename = f"ProgressMonitoring_{student_name}_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=self.page_size,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._create_header(variant_config, student_data))
        story.append(Spacer(1, 0.2*inch))
        
        # Add student info table
        story.extend(self._create_student_info_table(student_data))
        story.append(Spacer(1, 0.3*inch))
        
        # Add assessment summary
        story.extend(self._create_assessment_summary(delta_results, variant_config))
        story.append(Spacer(1, 0.3*inch))
        
        # Add metrics table
        story.extend(self._create_metrics_table(delta_results, variant_config, risk_analysis))
        story.append(Spacer(1, 0.3*inch))
        
        # Add risk indicator legend
        story.extend(self._create_risk_legend())
        story.append(Spacer(1, 0.3*inch))
        
        # Add recommendations
        if risk_analysis.get('recommendations'):
            story.extend(self._create_recommendations(risk_analysis['recommendations']))
        
        # Add understanding page
        story.append(PageBreak())
        story.extend(self._create_understanding_page())
        
        # Build PDF
        doc.build(story)
        
        return file_path
    
    def generate_screening_report(self, student_data: Dict,
                                 variant_config: Dict,
                                 screening_results: Dict,
                                 risk_analysis: Dict) -> str:
        """
        Generate screening PDF report
        
        Args:
            student_data: Student information dictionary
            variant_config: Report variant configuration
            screening_results: Screening assessment results
            risk_analysis: Risk analysis results
            
        Returns:
            Path to generated PDF file
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        student_name = student_data.get('student_name', 'Unknown').replace(' ', '_')
        period = student_data.get('screening_period', 'Unknown')
        filename = f"Screening_{period}_{student_name}_{timestamp}.pdf"
        file_path = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=self.page_size,
            topMargin=self.margin_top,
            bottomMargin=self.margin_bottom,
            leftMargin=self.margin_left,
            rightMargin=self.margin_right
        )
        
        # Build content
        story = []
        
        # Add header
        story.extend(self._create_header(variant_config, student_data, is_screening=True))
        story.append(Spacer(1, 0.2*inch))
        
        # Add student info table
        story.extend(self._create_student_info_table(student_data, is_screening=True))
        story.append(Spacer(1, 0.3*inch))
        
        # Add composite score section
        story.extend(self._create_composite_section(screening_results, variant_config, risk_analysis))
        story.append(Spacer(1, 0.3*inch))
        
        # Add detailed metrics
        story.extend(self._create_screening_metrics_table(screening_results, variant_config, risk_analysis))
        story.append(Spacer(1, 0.3*inch))
        
        # Add risk indicator legend
        story.extend(self._create_risk_legend())
        
        # Add understanding page
        story.append(PageBreak())
        story.extend(self._create_understanding_page())
        
        # Build PDF
        doc.build(story)
        
        return file_path
    
    def _create_header(self, variant_config: Dict, student_data: Dict, 
                      is_screening: bool = False) -> List:
        """Create report header"""
        elements = []
        
        # Title
        report_name = variant_config.get('name', 'Report')
        title = Paragraph(report_name, self.styles['ReportTitle'])
        elements.append(title)
        
        # Subtitle with date
        date_str = datetime.now().strftime('%B %d, %Y')
        if is_screening:
            period = student_data.get('screening_period', 'Unknown')
            subtitle_text = f"{period} Screening Report - Generated {date_str}"
        else:
            subtitle_text = f"Progress Monitoring Report - Generated {date_str}"
        
        subtitle = Paragraph(subtitle_text, self.styles['ReportBody'])
        elements.append(subtitle)
        
        return elements
    
    def _create_student_info_table(self, student_data: Dict, 
                                   is_screening: bool = False) -> List:
        """Create student information table"""
        elements = []
        
        # Heading
        heading = Paragraph("Student Information", self.styles['ReportHeading'])
        elements.append(heading)
        
        # Table data
        data = [
            ['Student Name:', student_data.get('student_name', 'N/A')],
            ['Student ID:', str(student_data.get('student_id', 'N/A'))],
            ['Grade:', str(student_data.get('grade', 'N/A'))],
            ['Teacher:', student_data.get('teacher_name', 'N/A')],
            ['School:', student_data.get('school_name', 'N/A')]
        ]
        
        if is_screening:
            data.append(['District:', student_data.get('district_name', 'N/A')])
        
        # Create table
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_assessment_summary(self, delta_results: Dict, 
                                   variant_config: Dict) -> List:
        """Create assessment summary section"""
        elements = []
        
        heading = Paragraph("Assessment Summary", self.styles['ReportHeading'])
        elements.append(heading)
        
        if not delta_results.get('has_data'):
            elements.append(Paragraph("No assessment data available.", self.styles['ReportBody']))
            return elements
        
        # Date information
        latest_date = delta_results.get('latest_date')
        prior_date = delta_results.get('prior_date')
        
        if latest_date:
            latest_str = pd.to_datetime(latest_date).strftime('%B %d, %Y')
            text = f"<b>Latest Assessment:</b> {latest_str}"
            elements.append(Paragraph(text, self.styles['ReportBody']))
        
        if prior_date:
            prior_str = pd.to_datetime(prior_date).strftime('%B %d, %Y')
            text = f"<b>Previous Assessment:</b> {prior_str}"
            elements.append(Paragraph(text, self.styles['ReportBody']))
        
        return elements
    
    def _create_metrics_table(self, delta_results: Dict, variant_config: Dict,
                             risk_analysis: Dict) -> List:
        """Create metrics comparison table for progress monitoring"""
        elements = []
        
        heading = Paragraph("Performance Metrics", self.styles['ReportHeading'])
        elements.append(heading)
        
        metrics_data = delta_results.get('metrics', {})
        
        if not metrics_data:
            elements.append(Paragraph("No metrics data available.", self.styles['ReportBody']))
            return elements
        
        # Table header
        data = [['Metric', 'Previous', 'Latest', 'Change (Δ)', 'Trend']]
        
        # Add metric rows
        for field, metric_info in metrics_data.items():
            label = metric_info.get('label', field)
            prior_val = metric_info.get('prior_value')
            latest_val = metric_info.get('latest_value')
            delta = metric_info.get('delta')
            indicator = metric_info.get('growth_indicator', '→')
            
            prior_str = f"{prior_val:.1f}" if prior_val is not None else 'N/A'
            latest_str = f"{latest_val:.1f}" if latest_val is not None else 'N/A'
            delta_str = f"{delta:+.1f}" if delta is not None else 'N/A'
            
            data.append([label, prior_str, latest_str, delta_str, indicator])
        
        # Create table
        col_widths = [2.5*inch, 1*inch, 1*inch, 1*inch, 0.5*inch]
        table = Table(data, colWidths=col_widths)
        
        # Style table
        style = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors.get('header_bg', '#1976D2'))),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(self.colors.get('alt_row', '#F5F5F5'))]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]
        
        table.setStyle(TableStyle(style))
        elements.append(table)
        
        return elements
    
    def _create_composite_section(self, screening_results: Dict,
                                  variant_config: Dict,
                                  risk_analysis: Dict) -> List:
        """Create composite score section for screening reports"""
        elements = []
        
        heading = Paragraph("Composite Score", self.styles['ReportHeading'])
        elements.append(heading)
        
        # Get composite score
        composite = screening_results.get('composite_score')
        readiness = risk_analysis.get('readiness_level', 'Unknown')
        overall_risk = risk_analysis.get('overall_risk', 'unknown')
        
        if composite is not None:
            score_text = f"<b>Composite Score:</b> {composite:.0f}"
            elements.append(Paragraph(score_text, self.styles['ReportBody']))
            
            readiness_text = f"<b>Readiness Level:</b> {readiness}"
            elements.append(Paragraph(readiness_text, self.styles['ReportBody']))
            
            # Add risk indicator
            risk_color = self._get_risk_color(overall_risk)
            risk_label = self._get_risk_label(overall_risk)
            risk_text = f'<b>Risk Level:</b> <font color="{risk_color}">{risk_label}</font>'
            elements.append(Paragraph(risk_text, self.styles['ReportBody']))
        else:
            elements.append(Paragraph("Composite score not available.", self.styles['ReportBody']))
        
        return elements
    
    def _create_screening_metrics_table(self, screening_results: Dict,
                                       variant_config: Dict,
                                       risk_analysis: Dict) -> List:
        """Create detailed metrics table for screening reports"""
        elements = []
        
        heading = Paragraph("Detailed Metrics", self.styles['ReportHeading'])
        elements.append(heading)
        
        metrics = variant_config.get('metrics', [])
        metric_risks = risk_analysis.get('metric_risks', {})
        
        # Table header
        data = [['Metric', 'Score', 'Risk Level']]
        
        # Add metric rows
        for metric in metrics:
            field = metric['field']
            label = metric['label']
            
            if field in metric_risks:
                score = metric_risks[field].get('score')
                risk_level = metric_risks[field].get('risk_level', 'unknown')
                risk_label = self._get_risk_label(risk_level)
                
                score_str = f"{score:.0f}" if score is not None else 'N/A'
                data.append([label, score_str, risk_label])
        
        # Create table
        col_widths = [3*inch, 1.5*inch, 1.5*inch]
        table = Table(data, colWidths=col_widths)
        
        # Style table
        style = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colors.get('header_bg', '#1976D2'))),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(self.colors.get('alt_row', '#F5F5F5'))]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]
        
        table.setStyle(TableStyle(style))
        elements.append(table)
        
        return elements
    
    def _create_risk_legend(self) -> List:
        """Create risk indicator legend"""
        elements = []
        
        heading = Paragraph("Risk Indicator Legend", self.styles['ReportHeading'])
        elements.append(heading)
        
        # Legend data
        data = [
            ['Low Risk', 'Student is meeting or exceeding expectations'],
            ['Some Risk', 'Student may benefit from targeted support'],
            ['High Risk', 'Student requires immediate intervention']
        ]
        
        # Create table
        table = Table(data, colWidths=[1.5*inch, 4.5*inch])
        
        # Style with colors
        style = [
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(self.colors.get('low_risk', '#388E3C'))),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor(self.colors.get('some_risk', '#F57C00'))),
            ('BACKGROUND', (0, 2), (0, 2), colors.HexColor(self.colors.get('high_risk', '#D32F2F'))),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]
        
        table.setStyle(TableStyle(style))
        elements.append(table)
        
        return elements
    
    def _create_recommendations(self, recommendations: List[str]) -> List:
        """Create recommendations section"""
        elements = []
        
        heading = Paragraph("Recommendations", self.styles['ReportHeading'])
        elements.append(heading)
        
        for rec in recommendations:
            bullet = Paragraph(f"• {rec}", self.styles['ReportBody'])
            elements.append(bullet)
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_understanding_page(self) -> List:
        """Create Understanding This Report page"""
        elements = []
        
        understanding_config = self.config.get('understanding_page', {})
        
        # Title
        title = understanding_config.get('title', 'Understanding This Report')
        elements.append(Paragraph(title, self.styles['ReportTitle']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Sections
        sections = understanding_config.get('sections', [])
        for section in sections:
            heading = section.get('heading', '')
            content = section.get('content', '')
            
            elements.append(Paragraph(heading, self.styles['ReportHeading']))
            
            # Handle multi-line content
            paragraphs = content.split('\n')
            for para in paragraphs:
                if para.strip():
                    elements.append(Paragraph(para.strip(), self.styles['ReportBody']))
            
            elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color for risk level"""
        color_map = {
            'high_risk': self.colors.get('high_risk', '#D32F2F'),
            'some_risk': self.colors.get('some_risk', '#F57C00'),
            'low_risk': self.colors.get('low_risk', '#388E3C'),
            'unknown': '#757575'
        }
        return color_map.get(risk_level, '#757575')
    
    def _get_risk_label(self, risk_level: str) -> str:
        """Get label for risk level"""
        label_map = {
            'high_risk': 'High Risk',
            'some_risk': 'Some Risk',
            'low_risk': 'Low Risk',
            'unknown': 'Unknown'
        }
        return label_map.get(risk_level, 'Unknown')
