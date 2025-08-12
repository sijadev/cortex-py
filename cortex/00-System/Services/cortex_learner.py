#!/usr/bin/env python3
"""
Cortex Learning Service - macOS Background Intelligence
Continuous pattern recognition and learning from Cortex data
"""

import os
import sys
import time
import json
import yaml
import logging
import schedule
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# Add the cortex algorithms path
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Algorithms')

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
    
    def __init__(self, cortex_path: str = "/Users/simonjanke/Projects/cortex"):
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
        
        # Initialize components
        self.pattern_detector = PatternDetector(self.cortex_path)
        self.data_miner = DataMiner(self.cortex_path)
        self.quality_monitor = QualityMonitor(self.cortex_path)
        self.notification_manager = NotificationManager()
        
        # Service state
        self.start_time = datetime.now()
        self.stats = self.load_learning_stats()
        
        self.logger.info("Cortex Learning Service initialized")
    
    def setup_logging(self):
        """Configure logging for the service"""
        log_file = self.logs_path / "cortex_learning.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('CortexLearningService')
    
    def load_config(self) -> Dict:
        """Load service configuration"""
        config_file = self.config_path / "service_config.yaml"
        
        default_config = {
            'learning_interval_minutes': 30,
            'pattern_detection_threshold': 0.7,
            'quality_check_interval_hours': 6,
            'notification_enabled': True,
            'max_log_age_days': 30,
            'learning_rules_file': 'learning_rules.json'
        }
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                default_config.update(user_config)
        else:
            # Create default config file
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
        
        return default_config
    
    def load_learning_stats(self) -> LearningStats:
        """Load learning statistics"""
        stats_file = self.data_path / "learning_stats.json"
        
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                data = json.load(f)
                return LearningStats(**data)
        
        return LearningStats()
    
    def save_learning_stats(self):
        """Save learning statistics"""
        stats_file = self.data_path / "learning_stats.json"
        
        # Update uptime
        self.stats.uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        with open(stats_file, 'w') as f:
            json.dump(asdict(self.stats), f, indent=2, default=str)
    
    def learning_cycle(self):
        """Main learning cycle - run periodically"""
        self.logger.info("Starting learning cycle")
        
        try:
            # 1. Pattern Detection
            new_patterns = self.pattern_detector.detect_new_patterns()
            if new_patterns:
                self.stats.patterns_detected += len(new_patterns)
                self.logger.info(f"Detected {len(new_patterns)} new patterns")
                
                # Notify user of significant patterns
                for pattern in new_patterns:
                    if pattern.get('confidence', 0) > 0.8:  # High-confidence patterns
                        self.notification_manager.notify_pattern_detected(pattern)
            
            # 2. Data Mining for Insights
            insights = self.data_miner.extract_insights()
            if insights:
                self.stats.insights_generated += len(insights)
                self.logger.info(f"Generated {len(insights)} new insights")
            
            # 3. Quality Monitoring
            quality_issues = self.quality_monitor.check_system_health()
            if quality_issues:
                self.stats.quality_alerts += len(quality_issues)
                for issue in quality_issues:
                    self.notification_manager.notify_quality_issue(issue)
            
            # 4. Update statistics
            self.stats.last_learning_cycle = datetime.now().isoformat()
            self.save_learning_stats()
            
            self.logger.info("Learning cycle completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in learning cycle: {e}")
    
    def quality_check(self):
        """Comprehensive quality check - run less frequently"""
        self.logger.info("Starting comprehensive quality check")
        
        try:
            # Performance analysis
            performance_report = self.quality_monitor.generate_performance_report()
            
            # Pattern validation
            pattern_validation = self.pattern_detector.validate_existing_patterns()
            
            # Data integrity check
            data_integrity = self.data_miner.check_data_integrity()
            
            # Generate summary report
            report = {
                'timestamp': datetime.now().isoformat(),
                'performance': performance_report,
                'pattern_validation': pattern_validation,
                'data_integrity': data_integrity
            }
            
            # Save report
            report_file = self.logs_path / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info("Quality check completed")
            
        except Exception as e:
            self.logger.error(f"Error in quality check: {e}")
    
    def cleanup_old_logs(self):
        """Clean up old log files"""
        max_age = timedelta(days=self.config['max_log_age_days'])
        cutoff_date = datetime.now() - max_age
        
        for log_file in self.logs_path.glob("*.log"):
            if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                log_file.unlink()
                self.logger.info(f"Cleaned up old log file: {log_file.name}")
    
    def schedule_tasks(self):
        """Schedule all recurring tasks"""
        learning_interval = self.config['learning_interval_minutes']
        quality_interval = self.config['quality_check_interval_hours']
        
        # Schedule learning cycles
        schedule.every(learning_interval).minutes.do(self.learning_cycle)
        
        # Schedule quality checks
        schedule.every(quality_interval).hours.do(self.quality_check)
        
        # Schedule daily cleanup
        schedule.every().day.at("02:00").do(self.cleanup_old_logs)
        
        self.logger.info(f"Scheduled tasks: Learning every {learning_interval}min, Quality check every {quality_interval}h")
    
    def run(self):
        """Main service loop"""
        self.logger.info("Cortex Learning Service starting")
        
        # Schedule tasks
        self.schedule_tasks()
        
        # Initial learning cycle
        self.learning_cycle()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Cortex Learning Service stopping")
        except Exception as e:
            self.logger.error(f"Service error: {e}")
        finally:
            self.save_learning_stats()


class PatternDetector:
    """Pattern detection and recognition algorithms"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = cortex_path
        self.logger = logging.getLogger('PatternDetector')
    
    def detect_new_patterns(self) -> List[Dict]:
        """Detect new patterns in Cortex data"""
        patterns = []
        
        try:
            # Analyze decision patterns
            decision_patterns = self.analyze_decision_patterns()
            patterns.extend(decision_patterns)
            
            # Analyze project patterns
            project_patterns = self.analyze_project_patterns()
            patterns.extend(project_patterns)
            
            # Analyze neural-link patterns
            ai_patterns = self.analyze_ai_session_patterns()
            patterns.extend(ai_patterns)
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
        
        return patterns
    
    def analyze_decision_patterns(self) -> List[Dict]:
        """Analyze patterns in decision-making"""
        patterns = []
        
        # Basic implementation - analyze ADR files
        try:
            decisions_path = self.cortex_path / "03-Decisions"
            if decisions_path.exists():
                adr_files = list(decisions_path.glob("*.md"))
                if len(adr_files) > 5:  # Need minimum data for pattern detection
                    patterns.append({
                        'name': 'decision_frequency_pattern',
                        'type': 'decision',
                        'confidence': 0.7,
                        'description': f'Detected {len(adr_files)} decision records',
                        'data_points': len(adr_files)
                    })
        except Exception as e:
            self.logger.error(f"Error analyzing decision patterns: {e}")
        
        return patterns
    
    def analyze_project_patterns(self) -> List[Dict]:
        """Analyze patterns across projects"""
        patterns = []
        
        try:
            projects_path = self.cortex_path / "01-Projects"
            if projects_path.exists():
                project_dirs = [d for d in projects_path.iterdir() if d.is_dir()]
                if len(project_dirs) > 3:
                    patterns.append({
                        'name': 'project_structure_pattern',
                        'type': 'project',
                        'confidence': 0.6,
                        'description': f'Analyzed {len(project_dirs)} project structures',
                        'data_points': len(project_dirs)
                    })
        except Exception as e:
            self.logger.error(f"Error analyzing project patterns: {e}")
        
        return patterns
    
    def analyze_ai_session_patterns(self) -> List[Dict]:
        """Analyze patterns in AI sessions"""
        patterns = []
        
        try:
            ai_path = self.cortex_path / "02-Neural-Links"
            if ai_path.exists():
                ai_files = list(ai_path.glob("*.md"))
                if len(ai_files) > 10:
                    patterns.append({
                        'name': 'ai_interaction_pattern',
                        'type': 'ai_session',
                        'confidence': 0.8,
                        'description': f'Analyzed {len(ai_files)} AI interaction sessions',
                        'data_points': len(ai_files)
                    })
        except Exception as e:
            self.logger.error(f"Error analyzing AI session patterns: {e}")
        
        return patterns
    
    def validate_existing_patterns(self) -> Dict:
        """Validate existing patterns against new data"""
        validation_results = {
            'validated_patterns': 0,
            'invalidated_patterns': 0,
            'confidence_changes': []
        }
        
        # Basic validation implementation
        # In a full implementation, this would check if previously detected patterns still hold
        
        return validation_results


class DataMiner:
    """Data mining and insight extraction"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = cortex_path
        self.logger = logging.getLogger('DataMiner')
    
    def extract_insights(self) -> List[Dict]:
        """Extract insights from Cortex data"""
        insights = []
        
        try:
            # Basic insight: file growth tracking
            insights.extend(self.analyze_growth_patterns())
            
            # Basic insight: usage patterns
            insights.extend(self.analyze_usage_patterns())
            
        except Exception as e:
            self.logger.error(f"Error extracting insights: {e}")
        
        return insights
    
    def analyze_growth_patterns(self) -> List[Dict]:
        """Analyze growth patterns in the Cortex"""
        insights = []
        
        try:
            # Count files in different categories
            categories = ['01-Projects', '02-Neural-Links', '03-Decisions', '04-Code-Fragments', '05-Insights']
            
            for category in categories:
                cat_path = self.cortex_path / category
                if cat_path.exists():
                    file_count = len(list(cat_path.glob("**/*.md")))
                    if file_count > 0:
                        insights.append({
                            'type': 'growth_pattern',
                            'category': category,
                            'file_count': file_count,
                            'confidence': 0.9,
                            'description': f'{category} contains {file_count} files'
                        })
        except Exception as e:
            self.logger.error(f"Error analyzing growth patterns: {e}")
        
        return insights
    
    def analyze_usage_patterns(self) -> List[Dict]:
        """Analyze usage patterns"""
        insights = []
        
        try:
            # Analyze recent activity by checking modification times
            recent_files = 0
            total_files = 0
            
            for md_file in self.cortex_path.glob("**/*.md"):
                total_files += 1
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if (datetime.now() - mtime).days <= 7:  # Modified in last week
                    recent_files += 1
            
            if total_files > 0:
                activity_rate = recent_files / total_files
                insights.append({
                    'type': 'usage_pattern',
                    'recent_activity_rate': activity_rate,
                    'recent_files': recent_files,
                    'total_files': total_files,
                    'confidence': 0.8,
                    'description': f'{recent_files} of {total_files} files modified recently'
                })
        except Exception as e:
            self.logger.error(f"Error analyzing usage patterns: {e}")
        
        return insights
    
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


class QualityMonitor:
    """System quality and performance monitoring"""
    
    def __init__(self, cortex_path: Path):
        self.cortex_path = cortex_path
        self.logger = logging.getLogger('QualityMonitor')
    
    def check_system_health(self) -> List[Dict]:
        """Check overall system health"""
        issues = []
        
        try:
            # Check file system health
            fs_issues = self.check_filesystem_health()
            issues.extend(fs_issues)
            
            # Check for very large files that might impact performance
            large_file_issues = self.check_file_sizes()
            issues.extend(large_file_issues)
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
        
        return issues
    
    def check_filesystem_health(self) -> List[Dict]:
        """Check filesystem-related health issues"""
        issues = []
        
        try:
            # Check if important directories exist
            important_dirs = ['01-Projects', '02-Neural-Links', '03-Decisions', '04-Code-Fragments', '05-Insights']
            
            for dir_name in important_dirs:
                dir_path = self.cortex_path / dir_name
                if not dir_path.exists():
                    issues.append({
                        'type': 'missing_directory',
                        'severity': 'medium',
                        'description': f'Important directory missing: {dir_name}',
                        'directory': dir_name
                    })
        except Exception as e:
            self.logger.error(f"Error checking filesystem health: {e}")
        
        return issues
    
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
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'file_counts': {},
            'directory_sizes': {},
            'system_health': 'good'
        }
        
        try:
            # Count files in each category
            categories = ['01-Projects', '02-Neural-Links', '03-Decisions', '04-Code-Fragments', '05-Insights']
            
            for category in categories:
                cat_path = self.cortex_path / category
                if cat_path.exists():
                    file_count = len(list(cat_path.glob("**/*.md")))
                    total_size = sum(f.stat().st_size for f in cat_path.glob("**/*.md"))
                    
                    report['file_counts'][category] = file_count
                    report['directory_sizes'][category] = total_size
        
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            report['system_health'] = 'error'
        
        return report


class NotificationManager:
    """macOS notification management"""
    
    def __init__(self):
        self.logger = logging.getLogger('NotificationManager')
    
    def notify_pattern_detected(self, pattern: Dict):
        """Send notification for new pattern detection"""
        try:
            import subprocess
            
            title = "Cortex: New Pattern Detected"
            message = f"Pattern '{pattern.get('name', 'Unknown')}' detected with {pattern.get('confidence', 0)*100:.0f}% confidence"
            
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], check=False)
            
        except Exception as e:
            self.logger.error(f"Error sending pattern notification: {e}")
    
    def notify_quality_issue(self, issue: Dict):
        """Send notification for quality issues"""
        try:
            import subprocess
            
            title = "Cortex: Quality Alert"
            message = f"Quality issue detected: {issue.get('description', 'Unknown issue')}"
            
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], check=False)
            
        except Exception as e:
            self.logger.error(f"Error sending quality notification: {e}")


def main():
    """Main entry point for the service"""
    service = CortexLearningService()
    service.run()


if __name__ == "__main__":
    main()
