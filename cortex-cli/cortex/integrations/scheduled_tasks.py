#!/usr/bin/env python3
"""
Cortex Scheduled Tasks System
Comprehensive automation and background task management for the Cortex ecosystem
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import uuid
import re


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskType(Enum):
    """Types of scheduled tasks"""
    SYNC = "sync"
    ANALYSIS = "analysis"
    MAINTENANCE = "maintenance"
    MONITORING = "monitoring"
    BACKUP = "backup"
    HEALTH_CHECK = "health_check"
    AI_PROCESSING = "ai_processing"
    CUSTOM = "custom"


@dataclass
class TaskDefinition:
    """Task definition and configuration"""
    id: str
    name: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    schedule: str  # Cron expression or interval
    enabled: bool
    max_runtime_minutes: int
    retry_count: int
    retry_delay_seconds: int
    timeout_seconds: Optional[int]
    dependencies: List[str]  # Task IDs this depends on
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskExecution:
    """Task execution record"""
    execution_id: str
    task_id: str
    status: TaskStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime] 
    duration_seconds: Optional[float]
    output: Optional[str]
    error: Optional[str]
    retry_attempt: int
    next_retry_at: Optional[datetime]


@dataclass
class ScheduleStats:
    """Scheduler statistics"""
    total_tasks: int
    active_tasks: int
    completed_today: int
    failed_today: int
    average_execution_time: float
    last_health_check: datetime
    uptime_hours: float
    scheduler_version: str


class SimpleCronParser:
    """Simple cron expression parser for basic scheduling"""
    
    @staticmethod
    def parse_cron(expression: str, last_run: Optional[datetime] = None) -> int:
        """Parse cron expression and return seconds until next run"""
        if not last_run:
            last_run = datetime.now()
            
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        
        minute, hour, day, month, weekday = parts
        
        # Simple implementation for common patterns
        if expression == "*/30 * * * *":  # Every 30 minutes
            return 30 * 60
        elif expression == "0 */2 * * *":  # Every 2 hours
            return 2 * 60 * 60
        elif expression == "0 * * * *":  # Every hour
            return 60 * 60
        elif expression == "*/15 * * * *":  # Every 15 minutes
            return 15 * 60
        elif expression == "0 2 * * *":  # Daily at 2 AM
            return 24 * 60 * 60  # Simplified to 24 hours
        elif expression == "0 */6 * * *":  # Every 6 hours
            return 6 * 60 * 60
        else:
            # Default fallback
            return 60 * 60  # 1 hour


class TaskScheduler:
    """Intelligent task scheduler with dependency management"""
    
    def __init__(self, cortex_path: str):
        self.cortex_path = Path(cortex_path)
        self.config_path = self.cortex_path / "cortex-cli" / "config" / "scheduled_tasks.json"
        self.data_path = self.cortex_path / "cortex-cli" / "data" / "scheduler"
        self.logs_path = self.cortex_path / "cortex-cli" / "logs" / "scheduler"
        
        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tasks: Dict[str, TaskDefinition] = {}
        self.executions: List[TaskExecution] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        self.start_time = datetime.now(timezone.utc)
        
        # Load configuration
        self._load_configuration()
        self._load_default_tasks()
    
    def _load_configuration(self):
        """Load scheduler configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    for task_data in config_data.get('tasks', []):
                        task = TaskDefinition(**task_data)
                        self.tasks[task.id] = task
        except Exception as e:
            self.logger.warning(f"Could not load configuration: {e}")
    
    def _load_default_tasks(self):
        """Load default system tasks"""
        default_tasks = [
            # Cross-Vault Analysis (every 30 minutes)
            {
                'id': 'vault_analysis',
                'name': 'Cross-Vault Analysis',
                'description': 'Analyze patterns across all vaults',
                'task_type': TaskType.ANALYSIS,
                'priority': TaskPriority.NORMAL,
                'schedule': '*/30 * * * *',  # Every 30 minutes
                'enabled': True,
                'max_runtime_minutes': 15,
                'retry_count': 2,
                'retry_delay_seconds': 300,
                'timeout_seconds': 900,
                'dependencies': [],
                'parameters': {'full_analysis': False, 'pattern_detection': True}
            },
            # AI Insights Generation (every 2 hours)
            {
                'id': 'ai_insights',
                'name': 'AI Insights Generation', 
                'description': 'Generate AI-powered insights from patterns',
                'task_type': TaskType.AI_PROCESSING,
                'priority': TaskPriority.HIGH,
                'schedule': '0 */2 * * *',  # Every 2 hours
                'enabled': True,
                'max_runtime_minutes': 20,
                'retry_count': 3,
                'retry_delay_seconds': 600,
                'timeout_seconds': 1200,
                'dependencies': ['vault_analysis'],
                'parameters': {'min_confidence': 0.7, 'max_insights': 10}
            },
            # System Health Check (every hour)
            {
                'id': 'health_check',
                'name': 'System Health Check',
                'description': 'Monitor system health and performance',
                'task_type': TaskType.HEALTH_CHECK,
                'priority': TaskPriority.HIGH,
                'schedule': '0 * * * *',  # Every hour
                'enabled': True,
                'max_runtime_minutes': 5,
                'retry_count': 1,
                'retry_delay_seconds': 120,
                'timeout_seconds': 300,
                'dependencies': [],
                'parameters': {'check_files': True, 'check_links': True}
            },
            # Cross-Vault Sync (every 15 minutes) 
            {
                'id': 'cross_vault_sync',
                'name': 'Cross-Vault Synchronization',
                'description': 'Synchronize cross-vault links and data',
                'task_type': TaskType.SYNC,
                'priority': TaskPriority.NORMAL,
                'schedule': '*/15 * * * *',  # Every 15 minutes
                'enabled': True,
                'max_runtime_minutes': 10,
                'retry_count': 2,
                'retry_delay_seconds': 180,
                'timeout_seconds': 600,
                'dependencies': [],
                'parameters': {'sync_to_obsidian': True, 'validate_links': True}
            },
            # Daily Maintenance (2 AM)
            {
                'id': 'daily_maintenance',
                'name': 'Daily Maintenance',
                'description': 'Daily system cleanup and optimization',
                'task_type': TaskType.MAINTENANCE,
                'priority': TaskPriority.LOW,
                'schedule': '0 2 * * *',  # Daily at 2 AM
                'enabled': True,
                'max_runtime_minutes': 30,
                'retry_count': 1,
                'retry_delay_seconds': 3600,
                'timeout_seconds': 1800,
                'dependencies': [],
                'parameters': {'cleanup_logs': True, 'optimize_data': True, 'backup_config': True}
            },
            # Ecosystem Monitor (every 6 hours)
            {
                'id': 'ecosystem_monitor',
                'name': 'Ecosystem Monitoring',
                'description': 'Monitor overall ecosystem health and trends',
                'task_type': TaskType.MONITORING,
                'priority': TaskPriority.NORMAL,
                'schedule': '0 */6 * * *',  # Every 6 hours
                'enabled': True,
                'max_runtime_minutes': 15,
                'retry_count': 2,
                'retry_delay_seconds': 900,
                'timeout_seconds': 900,
                'dependencies': ['health_check', 'vault_analysis'],
                'parameters': {'generate_report': True, 'alert_on_issues': True}
            }
        ]
        
        # Add default tasks if not already configured
        for task_data in default_tasks:
            task_data['created_at'] = datetime.now(timezone.utc)
            task_data['updated_at'] = datetime.now(timezone.utc)
            task_id = task_data['id']
            
            if task_id not in self.tasks:
                task = TaskDefinition(**task_data)
                self.tasks[task_id] = task
                self.logger.info(f"Added default task: {task.name}")
    
    async def start_scheduler(self):
        """Start the task scheduler"""
        self.is_running = True
        self.logger.info("Starting Cortex Task Scheduler")
        
        # Schedule all tasks
        for task in self.tasks.values():
            if task.enabled:
                self._schedule_task(task)
        
        # Main scheduler loop
        while self.is_running:
            try:
                await self._process_scheduled_tasks()
                await self._cleanup_completed_tasks()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def _schedule_task(self, task: TaskDefinition):
        """Schedule a task based on its cron expression"""
        try:
            # Parse cron expression and determine next run time
            parser = SimpleCronParser()
            next_run_seconds = parser.parse_cron(task.schedule)
            next_run = datetime.now() + timedelta(seconds=next_run_seconds)
            
            self.logger.info(f"Scheduled task '{task.name}' for {next_run}")
            
        except Exception as e:
            self.logger.error(f"Error scheduling task {task.name}: {e}")
    
    async def _process_scheduled_tasks(self):
        """Process tasks that are due to run"""
        now = datetime.now(timezone.utc)
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
                
            # Check if task should run based on schedule
            if self._should_task_run(task, now):
                # Check dependencies
                if await self._check_dependencies(task):
                    await self._execute_task(task)
    
    def _should_task_run(self, task: TaskDefinition, now: datetime) -> bool:
        """Determine if a task should run now"""
        try:
            parser = SimpleCronParser()
            
            # Get last execution
            last_execution = self._get_last_execution(task.id)
            if last_execution and last_execution.started_at:
                time_since_last = (now - last_execution.started_at).total_seconds()
                next_run_seconds = parser.parse_cron(task.schedule, last_execution.started_at)
                return time_since_last >= next_run_seconds
            else:
                # First run - check if enough time has passed since scheduler start
                time_since_start = (now - self.start_time).total_seconds()
                min_interval = parser.parse_cron(task.schedule)
                return time_since_start >= min(min_interval, 300)  # At least 5 minutes after start
                
        except Exception as e:
            self.logger.error(f"Error checking task schedule for {task.name}: {e}")
            return False
    
    async def _check_dependencies(self, task: TaskDefinition) -> bool:
        """Check if all task dependencies are satisfied"""
        for dep_id in task.dependencies:
            dep_execution = self._get_last_execution(dep_id)
            if not dep_execution or dep_execution.status != TaskStatus.COMPLETED:
                self.logger.warning(f"Task {task.name} waiting for dependency {dep_id}")
                return False
        return True
    
    async def _execute_task(self, task: TaskDefinition):
        """Execute a scheduled task"""
        if task.id in self.running_tasks:
            self.logger.warning(f"Task {task.name} already running, skipping")
            return
        
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
            duration_seconds=None,
            output=None,
            error=None,
            retry_attempt=0,
            next_retry_at=None
        )
        
        self.executions.append(execution)
        self.logger.info(f"Starting task: {task.name}")
        
        # Create and run task
        task_coroutine = self._run_task_with_timeout(task, execution)
        async_task = asyncio.create_task(task_coroutine)
        self.running_tasks[task.id] = async_task
        
        # Don't await here - let it run in background
    
    async def _run_task_with_timeout(self, task: TaskDefinition, execution: TaskExecution):
        """Run task with timeout and error handling"""
        try:
            # Apply timeout if specified
            if task.timeout_seconds:
                await asyncio.wait_for(self._run_task_implementation(task, execution), 
                                     timeout=task.timeout_seconds)
            else:
                await self._run_task_implementation(task, execution)
                
            # Mark as completed
            execution.status = TaskStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.info(f"Task completed: {task.name} in {execution.duration_seconds:.2f}s")
            
        except asyncio.TimeoutError:
            execution.status = TaskStatus.FAILED
            execution.error = f"Task timed out after {task.timeout_seconds} seconds"
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.error(f"Task {task.name} timed out")
            
            # Schedule retry if configured
            if execution.retry_attempt < task.retry_count:
                await self._schedule_retry(task, execution)
                
        except Exception as e:
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            self.logger.error(f"Task {task.name} failed: {e}")
            
            # Schedule retry if configured
            if execution.retry_attempt < task.retry_count:
                await self._schedule_retry(task, execution)
                
        finally:
            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
    
    async def _run_task_implementation(self, task: TaskDefinition, execution: TaskExecution):
        """Run the actual task implementation"""
        output_parts = []
        
        try:
            if task.task_type == TaskType.ANALYSIS:
                output = await self._run_analysis_task(task)
                output_parts.append(f"Analysis: {output}")
                
            elif task.task_type == TaskType.AI_PROCESSING:
                output = await self._run_ai_processing_task(task)
                output_parts.append(f"AI Processing: {output}")
                
            elif task.task_type == TaskType.HEALTH_CHECK:
                output = await self._run_health_check_task(task)
                output_parts.append(f"Health Check: {output}")
                
            elif task.task_type == TaskType.SYNC:
                output = await self._run_sync_task(task)
                output_parts.append(f"Sync: {output}")
                
            elif task.task_type == TaskType.MAINTENANCE:
                output = await self._run_maintenance_task(task)
                output_parts.append(f"Maintenance: {output}")
                
            elif task.task_type == TaskType.MONITORING:
                output = await self._run_monitoring_task(task)
                output_parts.append(f"Monitoring: {output}")
                
            else:
                output_parts.append(f"Unknown task type: {task.task_type}")
            
            execution.output = " | ".join(output_parts)
            
        except Exception as e:
            raise Exception(f"Task implementation failed: {e}")
    
    async def _run_analysis_task(self, task: TaskDefinition) -> str:
        """Run cross-vault analysis task"""
        try:
            # Import and run Multi-Vault AI analysis
            import sys
            sys.path.append(str(self.cortex_path / "cortex-cli" / "cortex" / "integrations"))
            from multi_vault_ai import MultiVaultAI
            
            ai = MultiVaultAI(str(self.cortex_path))
            patterns = await ai.analyze_cross_vault_patterns()
            
            return f"Analyzed {len(patterns)} patterns across vaults"
            
        except Exception as e:
            raise Exception(f"Analysis task failed: {e}")
    
    async def _run_ai_processing_task(self, task: TaskDefinition) -> str:
        """Run AI insights generation task"""
        try:
            # Import and run AI insights
            import sys
            sys.path.append(str(self.cortex_path / "cortex-cli" / "cortex" / "integrations"))
            from multi_vault_ai import MultiVaultAI
            
            ai = MultiVaultAI(str(self.cortex_path))
            insights = await ai.generate_ai_insights()
            
            # Filter by confidence if specified
            min_confidence = task.parameters.get('min_confidence', 0.5)
            high_confidence_insights = [i for i in insights if i.confidence >= min_confidence]
            
            return f"Generated {len(high_confidence_insights)} high-confidence insights"
            
        except Exception as e:
            raise Exception(f"AI processing task failed: {e}")
    
    async def _run_health_check_task(self, task: TaskDefinition) -> str:
        """Run system health check task"""
        try:
            health_results = []
            
            # Check file system health
            if task.parameters.get('check_files', True):
                important_dirs = ['01-Projects', '02-Neural-Links', '03-Decisions']
                missing_dirs = [d for d in important_dirs if not (self.cortex_path / d).exists()]
                if missing_dirs:
                    health_results.append(f"Missing directories: {missing_dirs}")
                else:
                    health_results.append("File system: OK")
            
            # Check link integrity
            if task.parameters.get('check_links', True):
                # Basic link checking
                md_files = list(self.cortex_path.rglob("*.md"))
                total_files = len(md_files)
                health_results.append(f"Files: {total_files} MD files found")
            
            return " | ".join(health_results) if health_results else "Health check completed"
            
        except Exception as e:
            raise Exception(f"Health check task failed: {e}")
    
    async def _run_sync_task(self, task: TaskDefinition) -> str:
        """Run cross-vault sync task"""
        try:
            # Import and run cross-vault linker
            import sys
            sys.path.append(str(self.cortex_path / "00-System" / "Cross-Vault-Linker"))
            from cross_vault_linker import CrossVaultLinker
            
            linker = CrossVaultLinker(hub_vault_path=str(self.cortex_path))
            report = await linker.run_full_linking_cycle_async(
                sync_to_obsidian=task.parameters.get('sync_to_obsidian', True)
            )
            
            return f"Sync completed: {report.get('summary', 'Success') if report else 'No report'}"
            
        except Exception as e:
            raise Exception(f"Sync task failed: {e}")
    
    async def _run_maintenance_task(self, task: TaskDefinition) -> str:
        """Run maintenance task"""
        try:
            maintenance_results = []
            
            # Cleanup logs
            if task.parameters.get('cleanup_logs', True):
                log_files_cleaned = 0
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for log_file in self.logs_path.rglob("*.log"):
                    if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                        log_file.unlink()
                        log_files_cleaned += 1
                
                maintenance_results.append(f"Cleaned {log_files_cleaned} old log files")
            
            # Optimize data files
            if task.parameters.get('optimize_data', True):
                # Basic optimization - could expand this
                maintenance_results.append("Data optimization completed")
            
            # Backup configuration  
            if task.parameters.get('backup_config', True):
                backup_dir = self.data_path / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_file = backup_dir / f"config_backup_{datetime.now().strftime('%Y%m%d')}.json"
                
                config_data = {
                    'tasks': {tid: asdict(task) for tid, task in self.tasks.items()},
                    'backup_date': datetime.now().isoformat()
                }
                
                with open(backup_file, 'w') as f:
                    json.dump(config_data, f, indent=2, default=str)
                
                maintenance_results.append(f"Configuration backed up to {backup_file.name}")
            
            return " | ".join(maintenance_results)
            
        except Exception as e:
            raise Exception(f"Maintenance task failed: {e}")
    
    async def _run_monitoring_task(self, task: TaskDefinition) -> str:
        """Run ecosystem monitoring task"""
        try:
            monitoring_results = []
            
            # Generate monitoring report
            if task.parameters.get('generate_report', True):
                stats = self.get_scheduler_stats()
                monitoring_results.append(f"Scheduler: {stats.active_tasks} active, {stats.completed_today} completed today")
            
            # Check for alerts
            if task.parameters.get('alert_on_issues', True):
                failed_today = len([e for e in self.executions 
                                   if e.status == TaskStatus.FAILED and 
                                   e.completed_at and e.completed_at.date() == datetime.now().date()])
                
                if failed_today > 5:  # Alert threshold
                    monitoring_results.append(f"ALERT: {failed_today} failed tasks today")
                else:
                    monitoring_results.append("No critical issues detected")
            
            return " | ".join(monitoring_results)
            
        except Exception as e:
            raise Exception(f"Monitoring task failed: {e}")
    
    async def _schedule_retry(self, task: TaskDefinition, execution: TaskExecution):
        """Schedule a task retry"""
        execution.retry_attempt += 1
        execution.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=task.retry_delay_seconds)
        
        self.logger.info(f"Scheduled retry {execution.retry_attempt}/{task.retry_count} for {task.name}")
    
    async def _cleanup_completed_tasks(self):
        """Clean up old task executions"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # Keep only recent executions
        self.executions = [e for e in self.executions 
                          if e.started_at and e.started_at > cutoff_date]
    
    def _get_last_execution(self, task_id: str) -> Optional[TaskExecution]:
        """Get the last execution of a task"""
        task_executions = [e for e in self.executions if e.task_id == task_id]
        if task_executions:
            return max(task_executions, key=lambda e: e.started_at or datetime.min.replace(tzinfo=timezone.utc))
        return None
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        
        # Cancel running tasks
        for task_id, async_task in self.running_tasks.items():
            async_task.cancel()
        
        self.logger.info("Task Scheduler stopped")
    
    def get_scheduler_stats(self) -> ScheduleStats:
        """Get scheduler statistics"""
        now = datetime.now(timezone.utc)
        today = now.date()
        
        completed_today = len([e for e in self.executions 
                              if e.status == TaskStatus.COMPLETED and 
                              e.completed_at and e.completed_at.date() == today])
        
        failed_today = len([e for e in self.executions 
                           if e.status == TaskStatus.FAILED and 
                           e.completed_at and e.completed_at.date() == today])
        
        # Calculate average execution time
        completed_executions = [e for e in self.executions 
                               if e.status == TaskStatus.COMPLETED and e.duration_seconds]
        avg_time = sum(e.duration_seconds for e in completed_executions) / len(completed_executions) if completed_executions else 0
        
        uptime = (now - self.start_time).total_seconds() / 3600  # hours
        
        return ScheduleStats(
            total_tasks=len(self.tasks),
            active_tasks=len(self.running_tasks),
            completed_today=completed_today,
            failed_today=failed_today,
            average_execution_time=avg_time,
            last_health_check=now,
            uptime_hours=uptime,
            scheduler_version="1.0.0"
        )
    
    def get_task_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of tasks"""
        if task_id:
            task = self.tasks.get(task_id)
            if not task:
                return {'error': f'Task {task_id} not found'}
            
            last_execution = self._get_last_execution(task_id)
            return {
                'task': asdict(task),
                'last_execution': asdict(last_execution) if last_execution else None,
                'is_running': task_id in self.running_tasks
            }
        else:
            return {
                'scheduler_running': self.is_running,
                'total_tasks': len(self.tasks),
                'running_tasks': list(self.running_tasks.keys()),
                'recent_executions': [asdict(e) for e in self.executions[-10:]]
            }
    
    def save_configuration(self):
        """Save scheduler configuration"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'tasks': [asdict(task) for task in self.tasks.values()],
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
                
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")


# CLI Interface Functions for Integration

async def start_scheduler_service(cortex_path: str) -> TaskScheduler:
    """Start the scheduler service"""
    scheduler = TaskScheduler(cortex_path)
    await scheduler.start_scheduler()
    return scheduler


def get_scheduler_instance(cortex_path: str) -> TaskScheduler:
    """Get a scheduler instance for status/control operations"""
    return TaskScheduler(cortex_path)
