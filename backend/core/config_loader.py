"""
Configuration Loader Module
Loads and manages report configuration files
"""
import json
import os
from typing import Dict, Optional, List


class ConfigLoader:
    """Loads and manages report configurations"""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir is None:
            # Default to config directory in backend
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(backend_dir, 'config')
        
        self.config_dir = config_dir
        self.configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files from config directory"""
        if not os.path.exists(self.config_dir):
            print(f"Warning: Config directory not found: {self.config_dir}")
            return
        
        # Load progress monitoring config
        pm_config_path = os.path.join(self.config_dir, 'progress_monitoring_config.json')
        if os.path.exists(pm_config_path):
            self.configs['progress_monitoring'] = self._load_config_file(pm_config_path)
        
        # Load screening config
        screening_config_path = os.path.join(self.config_dir, 'screening_config.json')
        if os.path.exists(screening_config_path):
            self.configs['screening'] = self._load_config_file(screening_config_path)
    
    def _load_config_file(self, file_path: str) -> Optional[Dict]:
        """
        Load a single configuration file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Configuration dictionary or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            print(f"Error loading config file {file_path}: {str(e)}")
            return None
    
    def get_config(self, report_type: str) -> Optional[Dict]:
        """
        Get configuration for a specific report type
        
        Args:
            report_type: Type of report ('progress_monitoring' or 'screening')
            
        Returns:
            Configuration dictionary or None
        """
        return self.configs.get(report_type)
    
    def get_variant_config(self, report_type: str, variant: str) -> Optional[Dict]:
        """
        Get configuration for a specific report variant
        
        Args:
            report_type: Type of report
            variant: Variant name (e.g., 'early_reading', 'cbmr_english')
            
        Returns:
            Variant configuration dictionary or None
        """
        config = self.get_config(report_type)
        if config is None:
            return None
        
        variants = config.get('variants', {})
        return variants.get(variant)
    
    def list_report_types(self) -> List[str]:
        """
        List all available report types
        
        Returns:
            List of report type names
        """
        return list(self.configs.keys())
    
    def list_variants(self, report_type: str) -> List[str]:
        """
        List all variants for a report type
        
        Args:
            report_type: Type of report
            
        Returns:
            List of variant names
        """
        config = self.get_config(report_type)
        if config is None:
            return []
        
        variants = config.get('variants', {})
        return list(variants.keys())
    
    def get_variant_display_name(self, report_type: str, variant: str) -> str:
        """
        Get display name for a variant
        
        Args:
            report_type: Type of report
            variant: Variant name
            
        Returns:
            Display name
        """
        variant_config = self.get_variant_config(report_type, variant)
        if variant_config:
            return variant_config.get('name', variant)
        return variant
    
    def get_metrics(self, report_type: str, variant: str) -> List[Dict]:
        """
        Get metrics configuration for a variant
        
        Args:
            report_type: Type of report
            variant: Variant name
            
        Returns:
            List of metric configurations
        """
        variant_config = self.get_variant_config(report_type, variant)
        if variant_config:
            return variant_config.get('metrics', [])
        return []
    
    def get_risk_thresholds(self, report_type: str, variant: str) -> Dict:
        """
        Get risk thresholds for a variant
        
        Args:
            report_type: Type of report
            variant: Variant name
            
        Returns:
            Risk threshold configuration
        """
        variant_config = self.get_variant_config(report_type, variant)
        if variant_config:
            return variant_config.get('risk_thresholds', {})
        return {}
    
    def get_pdf_layout(self, report_type: str) -> Dict:
        """
        Get PDF layout configuration
        
        Args:
            report_type: Type of report
            
        Returns:
            PDF layout configuration
        """
        config = self.get_config(report_type)
        if config:
            return config.get('pdf_layout', {})
        return {}
    
    def get_understanding_page(self, report_type: str) -> Dict:
        """
        Get "Understanding This Report" page configuration
        
        Args:
            report_type: Type of report
            
        Returns:
            Understanding page configuration
        """
        config = self.get_config(report_type)
        if config:
            return config.get('understanding_page', {})
        return {}
    
    def validate_config(self, report_type: str) -> tuple[bool, List[str]]:
        """
        Validate configuration completeness
        
        Args:
            report_type: Type of report
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        config = self.get_config(report_type)
        if config is None:
            errors.append(f"Configuration not found for report type: {report_type}")
            return False, errors
        
        # Check required top-level keys
        required_keys = ['report_type', 'report_name', 'variants', 'input_mapping']
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required configuration key: {key}")
        
        # Check variants
        variants = config.get('variants', {})
        if not variants:
            errors.append("No variants defined in configuration")
        
        for variant_name, variant_config in variants.items():
            # Check required variant keys
            variant_required = ['name', 'grade_range', 'subject', 'metrics']
            for key in variant_required:
                if key not in variant_config:
                    errors.append(f"Variant '{variant_name}' missing required key: {key}")
            
            # Check metrics
            metrics = variant_config.get('metrics', [])
            if not metrics:
                errors.append(f"Variant '{variant_name}' has no metrics defined")
        
        return len(errors) == 0, errors
    
    def reload_configs(self):
        """Reload all configuration files"""
        self.configs = {}
        self._load_all_configs()
    
    def add_custom_config(self, report_type: str, config: Dict):
        """
        Add a custom configuration programmatically
        
        Args:
            report_type: Type of report
            config: Configuration dictionary
        """
        self.configs[report_type] = config
    
    def save_config(self, report_type: str, file_path: str = None) -> bool:
        """
        Save configuration to file
        
        Args:
            report_type: Type of report
            file_path: Optional custom file path
            
        Returns:
            True if successful
        """
        config = self.get_config(report_type)
        if config is None:
            return False
        
        if file_path is None:
            file_path = os.path.join(self.config_dir, f'{report_type}_config.json')
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {str(e)}")
            return False
