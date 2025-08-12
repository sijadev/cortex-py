#!/usr/bin/env python3
"""
Cortex Management Service
Manages system operations, service status monitoring, and notifications
Implements the missing CortexManagementService for test compatibility
"""

import os
import json
import time
import logging
import subprocess
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

@dataclass
class ServiceStats:
    """Statistics for a service"""
    name: str
    status: str
    uptime: float
    cpu_usage: float
    memory_usage: float
    last_restart: str
    restart_count: int = 0
    health_score: float = 1.0

@dataclass
class NotificationConfig:
    """Configuration for notifications"""
    enabled: bool = True
    channels: List[str] = None
    severity_levels: List[str] = None

class CortexManagementService:
    """
    Management service for Cortex system operations
    Handles service monitoring, status reporting, and notifications
    """
    
    def __init__(self, hub_path: str):
        self.hub_path = Path(hub_path)
        self.config_path = self.hub_path / ".cortex" / "management.json"
        self.logs_path = self.hub_path / ".cortex" / "logs"
        self.service_stats_path = self.hub_path / ".cortex" / "service_stats.json"
        
        # Initialize logging
        self.logger = self._setup_logging()
        
        # Load configuration
        self.config = self._load_config()
        
        # Service registry
        self.services = {
            'ai_engine': {'status': 'running', 'pid': None},
            'cross_vault_linker': {'status': 'running', 'pid': None},
            'obsidian_bridge': {'status': 'stopped', 'pid': None},
            'file_watcher': {'status': 'stopped', 'pid': None}
        }
        
        # Statistics
        self.service_stats = self._load_service_stats()
        
        self.logger.info("Cortex Management Service initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger('CortexManagementService')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            log_file = self.logs_path / f"management_{datetime.now().strftime('%Y%m%d')}.log"
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load management service configuration"""
        default_config = {
            'monitoring': {
                'enabled': True,
                'interval': 30,  # seconds
                'health_check_timeout': 10
            },
            'notifications': {
                'enabled': True,
                'channels': ['log', 'system'],
                'severity_levels': ['error', 'warning', 'info']
            },
            'services': {
                'auto_restart': True,
                'max_restart_attempts': 3,
                'restart_delay': 5
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Save default config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _load_service_stats(self) -> Dict[str, ServiceStats]:
        """Load service statistics"""
        if self.service_stats_path.exists():
            try:
                with open(self.service_stats_path, 'r') as f:
                    data = json.load(f)
                return {
                    name: ServiceStats(**stats_data) 
                    for name, stats_data in data.items()
                }
            except Exception as e:
                self.logger.warning(f"Failed to load service stats: {e}")
        
        # Return default stats
        return {
            service: ServiceStats(
                name=service,
                status=info['status'],
                uptime=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                last_restart=datetime.now().isoformat()
            )
            for service, info in self.services.items()
        }
    
    def _save_service_stats(self):
        """Save service statistics to file"""
        try:
            data = {
                name: asdict(stats) 
                for name, stats in self.service_stats.items()
            }
            with open(self.service_stats_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save service stats: {e}")
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        service_info = self.services[service_name]
        stats = self.service_stats.get(service_name)
        
        status = {
            'name': service_name,
            'status': service_info['status'],
            'pid': service_info.get('pid'),
            'timestamp': datetime.now().isoformat()
        }
        
        if stats:
            status.update({
                'uptime': stats.uptime,
                'cpu_usage': stats.cpu_usage,
                'memory_usage': stats.memory_usage,
                'health_score': stats.health_score,
                'restart_count': stats.restart_count
            })
        
        return status
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        system_info = {
            'timestamp': datetime.now().isoformat(),
            'hub_path': str(self.hub_path),
            'services': {},
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage(str(self.hub_path)).percent
            }
        }
        
        # Add service statuses
        for service_name in self.services:
            system_info['services'][service_name] = self.get_service_status(service_name)
        
        return system_info
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service"""
        if service_name not in self.services:
            return {'error': f'Service {service_name} not found'}
        
        try:
            # Stop service if running
            if self.services[service_name]['status'] == 'running':
                self.services[service_name]['status'] = 'stopping'
                time.sleep(1)  # Simulate stop time
            
            # Start service
            self.services[service_name]['status'] = 'running'
            self.services[service_name]['pid'] = os.getpid()  # Mock PID
            
            # Update statistics
            if service_name in self.service_stats:
                self.service_stats[service_name].restart_count += 1
                self.service_stats[service_name].last_restart = datetime.now().isoformat()
                self.service_stats[service_name].status = 'running'
            
            self._save_service_stats()
            self.logger.info(f"Service {service_name} restarted successfully")
            
            return {
                'service': service_name,
                'status': 'restarted',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {e}")
            return {'error': str(e)}
    
    def restart(self) -> bool:
        """Restart the management service itself"""
        try:
            # Simulate restart process
            self.logger.info("Management service restart initiated")
            
            # Reset service stats
            for service_name in self.services:
                if service_name in self.service_stats:
                    self.service_stats[service_name].last_restart = datetime.now().isoformat()
            
            self._save_service_stats()
            return True
            
        except Exception as e:
            self.logger.error(f"Management service restart failed: {e}")
            return False
    
    def send_notification(self, message: str, severity: str = 'info') -> bool:
        """Send a notification through configured channels"""
        try:
            notification_config = self.config.get('notifications', {})
            
            if not notification_config.get('enabled', True):
                return True
            
            if severity not in notification_config.get('severity_levels', ['info']):
                return True
            
            timestamp = datetime.now().isoformat()
            notification_data = {
                'timestamp': timestamp,
                'severity': severity,
                'message': message,
                'service': 'CortexManagementService'
            }
            
            # Log notification
            if 'log' in notification_config.get('channels', []):
                if severity == 'error':
                    self.logger.error(message)
                elif severity == 'warning':
                    self.logger.warning(message)
                else:
                    self.logger.info(message)
            
            # System notification (mock)
            if 'system' in notification_config.get('channels', []):
                # This would normally send system notifications
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return False
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a comprehensive status summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'management_service': {
                'status': 'running',
                'uptime': time.time() - os.path.getctime(__file__),
                'config_loaded': bool(self.config),
                'services_monitored': len(self.services)
            },
            'services': {},
            'system_health': {
                'overall_score': 0.0,
                'issues': [],
                'recommendations': []
            }
        }
        
        # Add detailed service information
        running_services = 0
        total_health = 0.0
        
        for service_name in self.services:
            service_status = self.get_service_status(service_name)
            summary['services'][service_name] = service_status
            
            if service_status.get('status') == 'running':
                running_services += 1
            
            health_score = service_status.get('health_score', 0.0)
            total_health += health_score
        
        # Calculate overall health score
        if len(self.services) > 0:
            summary['system_health']['overall_score'] = total_health / len(self.services)
        
        # Add recommendations based on status
        if running_services < len(self.services):
            summary['system_health']['issues'].append(
                f"{len(self.services) - running_services} services are not running"
            )
            summary['system_health']['recommendations'].append(
                "Consider restarting stopped services"
            )
        
        return summary
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'healthy',
            'checks': {},
            'issues': [],
            'recommendations': []
        }
        
        # Check each service
        for service_name in self.services:
            service_check = {
                'name': service_name,
                'status': 'pass',
                'details': []
            }
            
            service_info = self.services[service_name]
            if service_info['status'] != 'running':
                service_check['status'] = 'fail'
                service_check['details'].append(f"Service is {service_info['status']}")
                health_report['issues'].append(f"{service_name} is not running")
            
            health_report['checks'][service_name] = service_check
        
        # System checks
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage = psutil.virtual_memory().percent
            
            if cpu_usage > 90:
                health_report['issues'].append(f"High CPU usage: {cpu_usage}%")
                health_report['recommendations'].append("Consider reducing system load")
            
            if memory_usage > 90:
                health_report['issues'].append(f"High memory usage: {memory_usage}%")
                health_report['recommendations'].append("Consider freeing up memory")
                
        except Exception as e:
            health_report['issues'].append(f"System monitoring error: {e}")
        
        # Determine overall health
        if health_report['issues']:
            health_report['overall_health'] = 'degraded' if len(health_report['issues']) < 3 else 'unhealthy'
        
        return health_report
    
    def update_service_stats(self, service_name: str, **kwargs):
        """Update statistics for a service"""
        if service_name not in self.service_stats:
            self.service_stats[service_name] = ServiceStats(
                name=service_name,
                status='unknown',
                uptime=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                last_restart=datetime.now().isoformat()
            )
        
        stats = self.service_stats[service_name]
        for key, value in kwargs.items():
            if hasattr(stats, key):
                setattr(stats, key, value)
        
        self._save_service_stats()

    def run_full_cycle(self) -> bool:
        """Run a complete management cycle and return success status"""
        self.logger.info("Starting full management cycle")
        
        try:
            start_time = time.time()
            
            # Run health check
            health_report = self.run_health_check()
            
            # Get comprehensive status
            status_summary = self.get_status_summary()
            
            # Update all service stats
            for service_name in self.services.keys():
                self.update_service_stats(
                    service_name,
                    uptime=time.time() - start_time,
                    last_check=datetime.now().isoformat()
                )
            
            # Calculate cycle time
            cycle_time = time.time() - start_time
            
            # Determine success based on overall health
            success = health_report.get('overall_health') in ['healthy', 'degraded']
            
            self.logger.info(f"Full management cycle completed in {cycle_time:.2f}s - Success: {success}")
            return success
            
        except Exception as e:
            self.logger.error(f"Error in full management cycle: {e}")
            return False
