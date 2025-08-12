#!/usr/bin/env python3
"""
Cortex Learning Service
Continuous pattern recognition and learning from Cortex data
"""

import json
import logging
import schedule
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class LearningStats:
    """Statistics for learning performance tracking"""
    patterns_detected: int = 0
    insights_generated: int = 0
    quality_alerts: int = 0
    last_learning_cycle: Optional[str] = None
    uptime_hours: float = 0.0
    
class CortexLearningService:
    """Main service class for background Cortex learning"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = Path(cortex_path)
        self.service_path = self.cortex_path / "00-System" / "Services"
        self.config_path = self.service_path / "config"
        self.logs_path = self.service_path / "logs"
        self.data_path = self.service_path / "data"
        
        # Ensure directories exist
        for path in [self.config_path, self.logs_path, self.data_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Service state
        self.start_time = datetime.now()
        self.stats = self.load_learning_stats()
        
        self.logger.info("Cortex Learning Service initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.logs_path / "cortex_learner.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('CortexLearner')
    
    def load_config(self) -> Dict:
        """Load service configuration"""
        config_file = self.config_path / "service_config.yaml"
        default_config = {
            'learning_interval_minutes': 30,
            'pattern_detection_enabled': True,
            'quality_monitoring_enabled': True,
            'notifications_enabled': True,
            'min_confidence_threshold': 0.7
        }
        
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                return {**default_config, **config}
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return default_config
        
        return default_config
    
    def load_learning_stats(self) -> LearningStats:
        """Load learning statistics"""
        stats_file = self.data_path / "learning_stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return LearningStats(**data)
            except Exception as e:
                self.logger.error(f"Error loading stats: {e}")
        
        return LearningStats()
    
    def save_learning_stats(self):
        """Save learning statistics"""
        stats_file = self.data_path / "learning_stats.json"
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.stats), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving stats: {e}")
    
    def run_learning_cycle(self):
        """Execute one learning cycle"""
        self.logger.info("Starting learning cycle")
        
        try:
            # Update uptime
            uptime = (datetime.now() - self.start_time).total_seconds() / 3600
            self.stats.uptime_hours = uptime
            
            # Pattern detection
            if self.config['pattern_detection_enabled']:
                patterns = self.detect_patterns()
                self.stats.patterns_detected += len(patterns)
                
                for pattern in patterns:
                    self.logger.info(f"Pattern detected: {pattern.get('name')}")
            
            # Quality monitoring
            if self.config['quality_monitoring_enabled']:
                issues = self.check_quality()
                self.stats.quality_alerts += len(issues)
                
                for issue in issues:
                    self.logger.warning(f"Quality issue: {issue.get('description')}")
            
            # Update stats
            self.stats.last_learning_cycle = datetime.now().isoformat()
            self.save_learning_stats()
            
        except Exception as e:
            self.logger.error(f"Error in learning cycle: {e}")
    
    def detect_patterns(self) -> List[Dict]:
        """Detect patterns in Cortex data"""
        patterns = []
        
        try:
            from .pattern_detector import AdvancedPatternDetector
            
            detector = AdvancedPatternDetector(self.cortex_path)
            
            # Detect different types of patterns
            decision_patterns = detector.detect_decision_patterns()
            project_patterns = detector.detect_project_patterns()
            ai_patterns = detector.detect_ai_session_patterns()
            
            all_patterns = decision_patterns + project_patterns + ai_patterns
            
            # Filter by confidence threshold
            threshold = self.config['min_confidence_threshold']
            filtered_patterns = [p for p in all_patterns if p.confidence >= threshold]
            
            # Save detected patterns
            if filtered_patterns:
                detector.save_detected_patterns(filtered_patterns)
            
            patterns = [p.to_dict() for p in filtered_patterns]
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def check_quality(self) -> List[Dict]:
        """Check system quality"""
        issues = []
        
        try:
            # Check data integrity
            integrity_report = self.check_data_integrity()
            if integrity_report['status'] != 'healthy':
                issues.append({
                    'type': 'data_integrity',
                    'description': 'Data integrity issues detected',
                    'details': integrity_report
                })
            
            # Check for unusually large files
            large_files = self.check_file_sizes()
            issues.extend(large_files)
            
        except Exception as e:
            self.logger.error(f"Error checking quality: {e}")
        
        return issues
    
    def check_data_integrity(self) -> Dict:
        """Check data integrity and consistency"""
        integrity_report = {
            'total_files': 0,
            'accessible_files': 0,
            'broken_links': 0,
            'large_files': 0,
            'status': 'healthy'
        }
        
        try:
            for md_file in self.cortex_path.glob("**/*.md"):
                integrity_report['total_files'] += 1
                
                if md_file.exists() and md_file.is_file():
                    integrity_report['accessible_files'] += 1
                    
                    # Check file size (>1MB might be unusually large for markdown)
                    if md_file.stat().st_size > 1024 * 1024:
                        integrity_report['large_files'] += 1
        
        except Exception as e:
            self.logger.error(f"Error checking data integrity: {e}")
            integrity_report['status'] = 'error'
        
        return integrity_report
    
    def check_file_sizes(self) -> List[Dict]:
        """Check for unusually large files"""
        issues = []
        
        try:
            large_threshold = 5 * 1024 * 1024  # 5MB
            
            for md_file in self.cortex_path.glob("**/*.md"):
                if md_file.stat().st_size > large_threshold:
                    issues.append({
                        'type': 'large_file',
                        'severity': 'low',
                        'description': f'Large file detected: {md_file.name}',
                        'file_path': str(md_file),
                        'size_mb': md_file.stat().st_size / (1024 * 1024)
                    })
        except Exception as e:
            self.logger.error(f"Error checking file sizes: {e}")
        
        return issues
    
    def schedule_learning(self):
        """Schedule regular learning cycles"""
        interval = self.config['learning_interval_minutes']
        schedule.every(interval).minutes.do(self.run_learning_cycle)
        
        self.logger.info(f"Scheduled learning cycles every {interval} minutes")
    
    def run(self):
        """Run the service"""
        self.logger.info("Starting Cortex Learning Service")
        
        # Schedule learning cycles
        self.schedule_learning()
        
        # Initial learning cycle
        self.run_learning_cycle()
        
        # Keep running
        while True:
            schedule.run_pending()
            import time
            time.sleep(60)  # Check every minute
    
    def get_service_status(self) -> Dict:
        """Get current service status"""
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return {
            'status': 'running',
            'uptime_hours': uptime,
            'stats': asdict(self.stats),
            'config': self.config,
            'last_cycle': self.stats.last_learning_cycle
        }
