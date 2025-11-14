"""
Delta Calculation Module
Handles growth calculations for progress monitoring reports
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class DeltaCalculator:
    """Calculates delta (change) values for progress monitoring"""
    
    def __init__(self, config: Dict):
        """
        Initialize delta calculator with configuration
        
        Args:
            config: Report configuration dictionary
        """
        self.config = config
        self.calculation_rules = config.get('calculation_rules', {})
        self.delta_config = self.calculation_rules.get('delta_calculation', {})
        self.growth_indicators = self.calculation_rules.get('growth_indicator', {})
        
    def calculate_deltas(self, df: pd.DataFrame, metrics: List[Dict], 
                        date_column: str = 'assessment_date') -> pd.DataFrame:
        """
        Calculate delta values for all metrics
        
        Args:
            df: DataFrame with student assessment data (sorted by date)
            metrics: List of metric configurations
            date_column: Name of date column
            
        Returns:
            DataFrame with delta columns added
        """
        if df.empty or len(df) < 2:
            # Need at least 2 assessments to calculate delta
            for metric in metrics:
                field = metric['field']
                df[f'{field}_delta'] = np.nan
                df[f'{field}_growth_indicator'] = '→'
            return df
        
        # Sort by date to ensure proper ordering
        df = df.sort_values(by=date_column)
        
        # Calculate deltas for each metric
        for metric in metrics:
            field = metric['field']
            
            if field in df.columns:
                # Calculate delta (current - previous)
                df[f'{field}_delta'] = df[field].diff()
                
                # Add growth indicator
                df[f'{field}_growth_indicator'] = df[f'{field}_delta'].apply(
                    self._get_growth_indicator
                )
                
                # For the first row, set delta to NaN
                df.loc[df.index[0], f'{field}_delta'] = np.nan
                df.loc[df.index[0], f'{field}_growth_indicator'] = '→'
        
        return df
    
    def calculate_latest_vs_prior(self, df: pd.DataFrame, metrics: List[Dict],
                                  date_column: str = 'assessment_date') -> Dict:
        """
        Calculate delta between latest and immediately prior assessment
        
        Args:
            df: DataFrame with student assessment data
            metrics: List of metric configurations
            date_column: Name of date column
            
        Returns:
            Dictionary with latest, prior, and delta values
        """
        result = {
            'has_data': False,
            'latest_date': None,
            'prior_date': None,
            'metrics': {}
        }
        
        if df.empty:
            return result
        
        # Find date column (try multiple names)
        actual_date_col = None
        for col_name in [date_column, 'assessment_date', 'test_date', 'date', 'Date']:
            if col_name in df.columns:
                actual_date_col = col_name
                break
        
        # If no date column, just use row order
        if actual_date_col is None:
            print(f"Warning: No date column found, using row order")
            df_sorted = df
        else:
            try:
                # Sort by date descending to get latest first
                df_sorted = df.sort_values(by=actual_date_col, ascending=False)
            except Exception as e:
                print(f"Warning: Could not sort by date: {e}, using row order")
                df_sorted = df
        
        if len(df_sorted) < 1:
            return result
        
        # Get latest assessment
        latest = df_sorted.iloc[0]
        if actual_date_col and actual_date_col in latest.index:
            result['latest_date'] = latest[actual_date_col]
        result['has_data'] = True
        
        # Get prior assessment if available
        prior = None
        if len(df_sorted) >= 2:
            prior = df_sorted.iloc[1]
            if actual_date_col and actual_date_col in prior.index:
                result['prior_date'] = prior[actual_date_col]
        
        # Calculate for each metric
        for metric in metrics:
            field = metric['field']
            label = metric['label']
            precision = metric.get('precision', 1)
            
            metric_result = {
                'label': label,
                'latest_value': None,
                'prior_value': None,
                'delta': None,
                'growth_indicator': '→',
                'has_prior': False
            }
            
            # Get latest value
            if field in latest.index and pd.notna(latest[field]):
                metric_result['latest_value'] = round(latest[field], precision)
            
            # Get prior value and calculate delta
            if prior is not None and field in prior.index:
                if pd.notna(prior[field]):
                    metric_result['prior_value'] = round(prior[field], precision)
                    metric_result['has_prior'] = True
                    
                    if metric_result['latest_value'] is not None:
                        delta = metric_result['latest_value'] - metric_result['prior_value']
                        metric_result['delta'] = round(delta, precision)
                        metric_result['growth_indicator'] = self._get_growth_indicator(delta)
            
            result['metrics'][field] = metric_result
        
        return result
    
    def calculate_growth_rate(self, df: pd.DataFrame, metric_field: str,
                             date_column: str = 'assessment_date') -> Optional[float]:
        """
        Calculate average growth rate per assessment period
        
        Args:
            df: DataFrame with student assessment data
            metric_field: Name of metric field
            date_column: Name of date column
            
        Returns:
            Average growth rate or None
        """
        if df.empty or len(df) < 2 or metric_field not in df.columns:
            return None
        
        # Sort by date
        df_sorted = df.sort_values(by=date_column)
        
        # Calculate differences
        deltas = df_sorted[metric_field].diff().dropna()
        
        if len(deltas) == 0:
            return None
        
        # Return average delta
        return deltas.mean()
    
    def calculate_cumulative_growth(self, df: pd.DataFrame, metric_field: str,
                                   date_column: str = 'assessment_date') -> Optional[float]:
        """
        Calculate total growth from first to latest assessment
        
        Args:
            df: DataFrame with student assessment data
            metric_field: Name of metric field
            date_column: Name of date column
            
        Returns:
            Total growth or None
        """
        if df.empty or len(df) < 2 or metric_field not in df.columns:
            return None
        
        # Sort by date
        df_sorted = df.sort_values(by=date_column)
        
        # Get first and last values
        first_value = df_sorted[metric_field].iloc[0]
        last_value = df_sorted[metric_field].iloc[-1]
        
        if pd.isna(first_value) or pd.isna(last_value):
            return None
        
        return last_value - first_value
    
    def get_trend_direction(self, df: pd.DataFrame, metric_field: str,
                           date_column: str = 'assessment_date') -> str:
        """
        Determine overall trend direction (improving, declining, stable)
        
        Args:
            df: DataFrame with student assessment data
            metric_field: Name of metric field
            date_column: Name of date column
            
        Returns:
            Trend direction string
        """
        growth_rate = self.calculate_growth_rate(df, metric_field, date_column)
        
        if growth_rate is None:
            return 'insufficient_data'
        
        # Define threshold for "stable" (adjust as needed)
        stability_threshold = 0.5
        
        if growth_rate > stability_threshold:
            return 'improving'
        elif growth_rate < -stability_threshold:
            return 'declining'
        else:
            return 'stable'
    
    def _get_growth_indicator(self, delta: float) -> str:
        """
        Get growth indicator symbol based on delta value
        
        Args:
            delta: Change value
            
        Returns:
            Growth indicator symbol
        """
        if pd.isna(delta):
            return self.growth_indicators.get('neutral', '→')
        
        if delta > 0:
            return self.growth_indicators.get('positive', '↑')
        elif delta < 0:
            return self.growth_indicators.get('negative', '↓')
        else:
            return self.growth_indicators.get('neutral', '→')
    
    def calculate_weeks_between_assessments(self, df: pd.DataFrame,
                                           date_column: str = 'assessment_date') -> List[float]:
        """
        Calculate weeks between consecutive assessments
        
        Args:
            df: DataFrame with assessment data
            date_column: Name of date column
            
        Returns:
            List of weeks between assessments
        """
        if df.empty or len(df) < 2 or date_column not in df.columns:
            return []
        
        # Sort by date
        df_sorted = df.sort_values(by=date_column)
        
        # Calculate time differences in days
        date_diffs = df_sorted[date_column].diff()
        
        # Convert to weeks
        weeks = [diff.days / 7.0 for diff in date_diffs if pd.notna(diff)]
        
        return weeks
    
    def is_bi_weekly_schedule(self, df: pd.DataFrame,
                             date_column: str = 'assessment_date',
                             tolerance_days: int = 3) -> bool:
        """
        Check if assessments follow bi-weekly schedule
        
        Args:
            df: DataFrame with assessment data
            date_column: Name of date column
            tolerance_days: Allowed deviation from 14 days
            
        Returns:
            True if bi-weekly schedule is followed
        """
        weeks = self.calculate_weeks_between_assessments(df, date_column)
        
        if not weeks:
            return False
        
        # Check if most intervals are close to 2 weeks (14 days)
        target_weeks = 2.0
        tolerance_weeks = tolerance_days / 7.0
        
        within_tolerance = sum(
            1 for w in weeks 
            if abs(w - target_weeks) <= tolerance_weeks
        )
        
        # Consider bi-weekly if at least 70% of intervals match
        return (within_tolerance / len(weeks)) >= 0.7
