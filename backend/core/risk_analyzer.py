"""
Risk Analysis Module
Determines risk levels and readiness indicators based on scores
"""
import pandas as pd
from typing import Dict, Optional, List


class RiskAnalyzer:
    """Analyzes student performance and assigns risk levels"""
    
    def __init__(self, config: Dict):
        """
        Initialize risk analyzer with configuration
        
        Args:
            config: Report configuration dictionary
        """
        self.config = config
        
    def determine_risk_level(self, score: float, thresholds: Dict) -> str:
        """
        Determine risk level based on score and thresholds
        
        Args:
            score: Student's score
            thresholds: Risk threshold configuration
            
        Returns:
            Risk level string ('low_risk', 'some_risk', 'high_risk')
        """
        if pd.isna(score):
            return 'unknown'
        
        # Check high risk (below minimum threshold)
        high_risk = thresholds.get('high_risk', {})
        if 'max' in high_risk and score <= high_risk['max']:
            return 'high_risk'
        
        # Check low risk (above minimum threshold)
        low_risk = thresholds.get('low_risk', {})
        if 'min' in low_risk and score >= low_risk['min']:
            return 'low_risk'
        
        # Default to some risk (in between)
        return 'some_risk'
    
    def get_risk_color(self, risk_level: str, colors: Dict) -> str:
        """
        Get color code for risk level
        
        Args:
            risk_level: Risk level string
            colors: Color configuration
            
        Returns:
            Hex color code
        """
        color_map = {
            'high_risk': colors.get('high_risk', '#D32F2F'),
            'some_risk': colors.get('some_risk', '#F57C00'),
            'low_risk': colors.get('low_risk', '#388E3C'),
            'unknown': '#757575'
        }
        
        return color_map.get(risk_level, '#757575')
    
    def get_risk_label(self, risk_level: str) -> str:
        """
        Get human-readable label for risk level
        
        Args:
            risk_level: Risk level string
            
        Returns:
            Display label
        """
        label_map = {
            'high_risk': 'High Risk',
            'some_risk': 'Some Risk',
            'low_risk': 'Low Risk',
            'unknown': 'Unknown'
        }
        
        return label_map.get(risk_level, 'Unknown')
    
    def determine_readiness_level(self, score: float, readiness_levels: List[str],
                                 thresholds: Dict) -> str:
        """
        Determine readiness level for screening reports
        
        Args:
            score: Student's composite score
            readiness_levels: List of readiness level labels
            thresholds: Risk threshold configuration
            
        Returns:
            Readiness level string
        """
        if pd.isna(score):
            return 'Unknown'
        
        # Map risk levels to readiness levels
        risk_level = self.determine_risk_level(score, thresholds)
        
        if len(readiness_levels) == 4:
            # Four-level system (e.g., Not Ready, Approaching, Ready, Advanced)
            if risk_level == 'high_risk':
                return readiness_levels[0]  # Not Ready / Below Basic
            elif risk_level == 'some_risk':
                return readiness_levels[1]  # Approaching Ready / Basic
            elif risk_level == 'low_risk':
                # Distinguish between Ready and Advanced based on score
                low_risk_min = thresholds.get('low_risk', {}).get('min', 50)
                advanced_threshold = low_risk_min + (100 - low_risk_min) * 0.5
                
                if score >= advanced_threshold:
                    return readiness_levels[3]  # Advanced
                else:
                    return readiness_levels[2]  # Ready / Proficient
        
        return readiness_levels[0] if readiness_levels else 'Unknown'
    
    def analyze_student_performance(self, student_data: pd.DataFrame,
                                   variant_config: Dict) -> Dict:
        """
        Comprehensive analysis of student performance
        
        Args:
            student_data: DataFrame with student's assessment data
            variant_config: Configuration for report variant
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            'overall_risk': 'unknown',
            'metric_risks': {},
            'readiness_level': None,
            'recommendations': []
        }
        
        if student_data.empty:
            return analysis
        
        # Get latest assessment
        latest = student_data.iloc[-1]
        
        metrics = variant_config.get('metrics', [])
        thresholds = variant_config.get('risk_thresholds', {})
        
        # Analyze each metric
        risk_scores = []
        for metric in metrics:
            field = metric['field']
            
            if field in latest.index and pd.notna(latest[field]):
                score = latest[field]
                risk_level = self.determine_risk_level(score, thresholds)
                
                analysis['metric_risks'][field] = {
                    'score': score,
                    'risk_level': risk_level,
                    'risk_label': self.get_risk_label(risk_level)
                }
                
                # Map risk to numeric for averaging
                risk_map = {'low_risk': 0, 'some_risk': 1, 'high_risk': 2}
                if risk_level in risk_map:
                    risk_scores.append(risk_map[risk_level])
        
        # Determine overall risk (most conservative approach)
        if risk_scores:
            max_risk = max(risk_scores)
            risk_reverse_map = {0: 'low_risk', 1: 'some_risk', 2: 'high_risk'}
            analysis['overall_risk'] = risk_reverse_map[max_risk]
        
        # Determine readiness level for screening reports
        if 'composite_score' in latest.index and pd.notna(latest['composite_score']):
            readiness_levels = variant_config.get('readiness_levels', [])
            if readiness_levels:
                analysis['readiness_level'] = self.determine_readiness_level(
                    latest['composite_score'],
                    readiness_levels,
                    thresholds
                )
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(
            analysis['overall_risk'],
            analysis['metric_risks']
        )
        
        return analysis
    
    def _generate_recommendations(self, overall_risk: str,
                                 metric_risks: Dict) -> List[str]:
        """
        Generate intervention recommendations based on risk analysis
        
        Args:
            overall_risk: Overall risk level
            metric_risks: Dictionary of metric-specific risks
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if overall_risk == 'high_risk':
            recommendations.append(
                "Immediate intervention recommended. Consider intensive small-group instruction."
            )
            recommendations.append(
                "Schedule progress monitoring assessments bi-weekly to track growth."
            )
        elif overall_risk == 'some_risk':
            recommendations.append(
                "Targeted support recommended. Monitor progress closely."
            )
            recommendations.append(
                "Consider supplemental instruction in areas of weakness."
            )
        elif overall_risk == 'low_risk':
            recommendations.append(
                "Student is meeting expectations. Continue current instruction."
            )
            recommendations.append(
                "Consider enrichment opportunities to maintain engagement."
            )
        
        # Add metric-specific recommendations
        high_risk_metrics = [
            field for field, data in metric_risks.items()
            if data.get('risk_level') == 'high_risk'
        ]
        
        if high_risk_metrics:
            recommendations.append(
                f"Focus intervention on: {', '.join(high_risk_metrics)}"
            )
        
        return recommendations
    
    def calculate_composite_score(self, student_data: pd.DataFrame,
                                 metrics: List[Dict],
                                 weights: Optional[Dict] = None) -> Optional[float]:
        """
        Calculate weighted composite score from multiple metrics
        
        Args:
            student_data: DataFrame with student's assessment data
            metrics: List of metric configurations
            weights: Optional dictionary of metric weights
            
        Returns:
            Composite score or None
        """
        if student_data.empty:
            return None
        
        latest = student_data.iloc[-1]
        
        # Default to equal weights if not specified
        if weights is None:
            weights = {metric['field']: 1.0 for metric in metrics}
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric in metrics:
            field = metric['field']
            
            if field in latest.index and pd.notna(latest[field]):
                weight = weights.get(field, 1.0)
                total_score += latest[field] * weight
                total_weight += weight
        
        if total_weight == 0:
            return None
        
        return total_score / total_weight
    
    def get_percentile_rank(self, score: float, all_scores: List[float]) -> Optional[int]:
        """
        Calculate percentile rank within a group
        
        Args:
            score: Student's score
            all_scores: List of all scores in comparison group
            
        Returns:
            Percentile rank (0-100) or None
        """
        if pd.isna(score) or not all_scores:
            return None
        
        # Remove NaN values
        valid_scores = [s for s in all_scores if pd.notna(s)]
        
        if not valid_scores:
            return None
        
        # Calculate percentile
        below = sum(1 for s in valid_scores if s < score)
        equal = sum(1 for s in valid_scores if s == score)
        
        percentile = ((below + 0.5 * equal) / len(valid_scores)) * 100
        
        return int(round(percentile))
