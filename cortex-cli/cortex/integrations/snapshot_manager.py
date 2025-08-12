"""
Cortex CLI Snapshot Integration
System state snapshots for backup and restoration
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import subprocess
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class CortexSnapshotManager:
    """Manages system snapshots for backup and restoration"""
    
    def __init__(self, cortex_path: str):
        self.cortex_path = Path(cortex_path)
        self.snapshots_dir = self.cortex_path / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
    
    def create_snapshot(self, name: str = None, description: str = None):
        """Create a new system snapshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = name or f"snapshot_{timestamp}"
        
        snapshot_data = {
            "name": snapshot_name,
            "timestamp": datetime.now().isoformat(),
            "description": description or "System snapshot",
            "git_commit": self._get_git_commit(),
            "system_state": self._capture_system_state(),
            "cli_config": self._capture_cli_config(),
            "dependencies": self._capture_dependencies(),
            "health_metrics": self._capture_health_metrics()
        }
        
        snapshot_file = self.snapshots_dir / f"{snapshot_name}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2, default=str)
        
        # Also create markdown version for readability
        self._create_markdown_snapshot(snapshot_data)
        
        console.print(f"✅ Snapshot created: {snapshot_name}", style="green")
        return snapshot_name
    
    def list_snapshots(self):
        """List all available snapshots"""
        snapshots = []
        for snapshot_file in self.snapshots_dir.glob("*.json"):
            try:
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)
                snapshots.append({
                    "name": data["name"],
                    "timestamp": data["timestamp"], 
                    "description": data["description"],
                    "file": snapshot_file.name
                })
            except Exception as e:
                console.print(f"⚠️ Error reading {snapshot_file}: {e}", style="yellow")
        
        if not snapshots:
            console.print("No snapshots found", style="yellow")
            return
        
        table = Table(title="Cortex System Snapshots")
        table.add_column("Name", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Description", style="white")
        
        for snapshot in sorted(snapshots, key=lambda x: x["timestamp"], reverse=True):
            table.add_row(
                snapshot["name"],
                datetime.fromisoformat(snapshot["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                snapshot["description"]
            )
        
        console.print(table)
    
    def restore_snapshot(self, snapshot_name: str, dry_run: bool = True):
        """Restore from a snapshot"""
        snapshot_file = self.snapshots_dir / f"{snapshot_name}.json"
        
        if not snapshot_file.exists():
            console.print(f"❌ Snapshot not found: {snapshot_name}", style="red")
            return False
        
        with open(snapshot_file, 'r') as f:
            snapshot_data = json.load(f)
        
        if dry_run:
            console.print("🔍 Dry run - showing what would be restored:", style="blue")
            self._show_restore_plan(snapshot_data)
        else:
            console.print(f"🔄 Restoring snapshot: {snapshot_name}", style="blue")
            return self._execute_restore(snapshot_data)
    
    def _capture_system_state(self):
        """Capture current system state"""
        return {
            "directory_structure": self._get_directory_tree(),
            "file_count": self._count_files_by_type(),
            "git_status": self._get_git_status(),
            "cli_version": self._get_cli_version()
        }
    
    def _capture_cli_config(self):
        """Capture CLI configuration"""
        config_files = [
            "cortex-cli/setup.py",
            "cortex-cli/requirements.txt", 
            ".cortex/config.yaml"
        ]
        
        config_data = {}
        for config_file in config_files:
            config_path = self.cortex_path / config_file
            if config_path.exists():
                try:
                    config_data[config_file] = config_path.read_text()
                except Exception as e:
                    config_data[config_file] = f"Error reading: {e}"
        
        return config_data
    
    def _capture_health_metrics(self):
        """Capture system health metrics"""
        try:
            # Run health check via CLI
            result = subprocess.run(
                ["python3", "-m", "cortex.cli.main", "status", "--json"],
                cwd=self.cortex_path / "cortex-cli",
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
    
    def _create_markdown_snapshot(self, snapshot_data):
        """Create human-readable markdown version"""
        markdown_content = f"""# Cortex System Snapshot - {snapshot_data['name']}

## Snapshot Overview
- **Date**: {datetime.fromisoformat(snapshot_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}
- **Description**: {snapshot_data['description']}
- **Git Commit**: {snapshot_data.get('git_commit', 'N/A')}

## System State
### Directory Structure
{self._format_directory_tree(snapshot_data['system_state']['directory_structure'])}

### File Statistics
{self._format_file_stats(snapshot_data['system_state']['file_count'])}

## Health Metrics
{self._format_health_metrics(snapshot_data['health_metrics'])}

## Restoration
To restore this snapshot:
```bash
cortex snapshot restore {snapshot_data['name']}
```

For dry-run (preview):
```bash
cortex snapshot restore {snapshot_data['name']} --dry-run
```
"""
        
        markdown_file = self.snapshots_dir / f"{snapshot_data['name']}.md"
        with open(markdown_file, 'w') as f:
            f.write(markdown_content)
    
    def _get_git_commit(self):
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.cortex_path,
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None


@click.group()
def snapshot():
    """System snapshot management"""
    pass

@snapshot.command()
@click.option('--name', help='Snapshot name')
@click.option('--description', help='Snapshot description')
@click.pass_context
def create(ctx, name, description):
    """Create a new system snapshot"""
    cortex_path = ctx.obj.get('cortex_path', '.')
    manager = CortexSnapshotManager(cortex_path)
    
    snapshot_name = manager.create_snapshot(name, description)
    console.print(Panel(
        f"Snapshot '{snapshot_name}' created successfully!\n\n"
        "This includes:\n"
        "• Complete directory structure\n"
        "• CLI configuration\n" 
        "• Health metrics\n"
        "• Git state\n\n"
        f"Restore with: cortex snapshot restore {snapshot_name}",
        title="Snapshot Created",
        style="green"
    ))

@snapshot.command()
def list():
    """List all available snapshots"""
    cortex_path = "."  # Would be passed from main CLI context
    manager = CortexSnapshotManager(cortex_path)
    manager.list_snapshots()

@snapshot.command()
@click.argument('snapshot_name')
@click.option('--dry-run', is_flag=True, help='Show what would be restored without executing')
def restore(snapshot_name, dry_run):
    """Restore from a snapshot"""
    cortex_path = "."  # Would be passed from main CLI context
    manager = CortexSnapshotManager(cortex_path)
    
    if dry_run:
        manager.restore_snapshot(snapshot_name, dry_run=True)
    else:
        click.confirm(f"Are you sure you want to restore snapshot '{snapshot_name}'? This may overwrite current state.")
        manager.restore_snapshot(snapshot_name, dry_run=False)

if __name__ == "__main__":
    snapshot()
