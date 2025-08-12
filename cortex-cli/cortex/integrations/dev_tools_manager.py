"""
Cortex Development Tools CLI Module

Manages development tool configurations and integration guides.
Provides commands for setting up and managing Claude Desktop, Continue,
and other development tools within the Cortex system.
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm

console = Console()

@dataclass
class ToolConfig:
    """Configuration for a development tool"""
    name: str
    category: str
    status: str  # active, inactive, not_configured
    config_path: Optional[str] = None
    description: str = ""
    features: List[str] = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = []

class CortexDevToolsManager:
    """Manages development tools for Cortex system"""
    
    def __init__(self, cortex_root: str = None):
        self.cortex_root = Path(cortex_root) if cortex_root else Path.cwd()
        self.tools_dir = self.cortex_root / "00-System" / "Development-Tools"
        self.cli_root = self.cortex_root / "cortex-cli"
        
        # Tool configurations
        self.tools = {
            "claude_desktop": ToolConfig(
                name="Claude Desktop",
                category="AI Assistant",
                status="not_configured",
                description="Native file system access, persistent context sessions",
                features=["Multi-file analysis", "System architecture", "Code reviews"]
            ),
            "continue": ToolConfig(
                name="Continue",
                category="VS Code Extension", 
                status="not_configured",
                description="Unlimited code generation, direct file editing",
                features=["Code implementation", "Multi-file development", "Real-time editing"]
            ),
            "web_claude": ToolConfig(
                name="Web Claude",
                category="Web Interface",
                status="active",
                description="Quick access, mobile support, web research",
                features=["Quick queries", "Mobile access", "URL analysis"]
            ),
            "cortex_ai": ToolConfig(
                name="Cortex AI System",
                category="Automated Intelligence", 
                status="active",
                description="Pattern learning, cross-vault connections",
                features=["Pattern detection", "Automated insights", "Cross-vault analysis"]
            )
        }
    
    def get_tool_status(self) -> Dict[str, ToolConfig]:
        """Get current status of all development tools"""
        # Update statuses based on actual system state
        self._detect_tool_configurations()
        return self.tools
    
    def _detect_tool_configurations(self):
        """Detect which tools are actually configured"""
        
        # Check Claude Desktop - look for common config locations
        claude_config_paths = [
            Path.home() / ".config" / "claude-desktop" / "config.json",
            Path.home() / "Library" / "Application Support" / "Claude" / "config.json"
        ]
        
        for config_path in claude_config_paths:
            if config_path.exists():
                self.tools["claude_desktop"].status = "active"
                self.tools["claude_desktop"].config_path = str(config_path)
                break
        
        # Check Continue - look for VS Code extension
        vscode_extensions = Path.home() / ".vscode" / "extensions"
        if vscode_extensions.exists():
            continue_ext = list(vscode_extensions.glob("continue.*"))
            if continue_ext:
                self.tools["continue"].status = "active"
                self.tools["continue"].config_path = str(continue_ext[0])
    
    def display_tool_matrix(self):
        """Display comprehensive tool overview matrix"""
        
        table = Table(title="🛠️ Cortex Development Tools Matrix", show_header=True)
        table.add_column("Tool", style="bold blue", width=20)
        table.add_column("Category", style="cyan", width=18)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Key Features", style="green", width=40)
        
        for tool_id, tool in self.tools.items():
            # Color-code status
            if tool.status == "active":
                status_text = "[bold green]✅ Active[/bold green]"
            elif tool.status == "inactive":
                status_text = "[bold yellow]⏸️ Inactive[/bold yellow]"
            else:
                status_text = "[bold red]❌ Not Config[/bold red]"
            
            features_text = " • ".join(tool.features[:3])  # Show top 3 features
            
            table.add_row(
                tool.name,
                tool.category,
                status_text,
                features_text
            )
        
        console.print(table)
        console.print()
        
        # Show workflow recommendations
        self._show_workflow_recommendations()
    
    def _show_workflow_recommendations(self):
        """Show recommended workflows based on tool status"""
        
        panel_content = []
        
        # Check tool combinations and recommend workflows
        claude_active = self.tools["claude_desktop"].status == "active"
        continue_active = self.tools["continue"].status == "active"
        
        if claude_active and continue_active:
            panel_content.append("🎯 [bold green]OPTIMAL SETUP[/bold green] - Full Trinity Available!")
            panel_content.append("  → System Architecture: Claude Desktop")
            panel_content.append("  → Code Implementation: Continue + VS Code")
            panel_content.append("  → Quick Questions: Web Claude")
            
        elif claude_active:
            panel_content.append("🏗️ [bold blue]ARCHITECTURE FOCUS[/bold blue] - Claude Desktop Active")
            panel_content.append("  → Perfect for: System design, code reviews, multi-file analysis")
            panel_content.append("  💡 Add Continue for unlimited code generation!")
            
        elif continue_active:
            panel_content.append("⚡ [bold yellow]DEVELOPMENT FOCUS[/bold yellow] - Continue Active")
            panel_content.append("  → Perfect for: Code implementation, real-time development")
            panel_content.append("  💡 Add Claude Desktop for system architecture!")
            
        else:
            panel_content.append("🚀 [bold red]SETUP NEEDED[/bold red] - Configure development tools")
            panel_content.append("  💡 Start with: [cyan]cortex dev-tools setup claude[/cyan]")
            panel_content.append("  💡 Then add: [cyan]cortex dev-tools setup continue[/cyan]")
        
        if panel_content:
            console.print(Panel(
                "\n".join(panel_content),
                title="🎮 Recommended Workflows",
                border_style="bright_blue"
            ))
    
    def setup_claude_desktop(self):
        """Interactive Claude Desktop setup"""
        
        console.print(Panel(
            "[bold blue]🖥️ Claude Desktop Integration Setup[/bold blue]\n\n"
            "Setting up optimal Claude Desktop configuration for Cortex development.",
            title="Claude Desktop Setup",
            border_style="blue"
        ))
        
        # Check if already configured
        if self.tools["claude_desktop"].status == "active":
            if not Confirm.ask("Claude Desktop appears to be configured. Reconfigure?"):
                return
        
        # Get Claude Desktop app path
        claude_app_paths = [
            "/Applications/Claude.app",
            Path.home() / "Applications" / "Claude.app"
        ]
        
        claude_app = None
        for path in claude_app_paths:
            if Path(path).exists():
                claude_app = path
                break
        
        if not claude_app:
            console.print("[red]❌ Claude Desktop app not found![/red]")
            console.print("Please install Claude Desktop first: https://claude.ai/download")
            return
        
        # Create project configurations
        self._create_claude_project_configs()
        
        # Show integration guide
        self._show_claude_integration_guide()
        
        console.print("[green]✅ Claude Desktop setup completed![/green]")
        self.tools["claude_desktop"].status = "active"
    
    def setup_continue(self):
        """Interactive Continue extension setup"""
        
        console.print(Panel(
            "[bold purple]💻 Continue VS Code Extension Setup[/bold purple]\n\n"
            "Setting up Continue for unlimited code generation in Cortex projects.",
            title="Continue Setup",
            border_style="purple"
        ))
        
        # Check VS Code installation
        vscode_paths = [
            "/Applications/Visual Studio Code.app",
            "/usr/local/bin/code",
            shutil.which("code")
        ]
        
        vscode_found = any(Path(p).exists() if p else False for p in vscode_paths)
        
        if not vscode_found:
            console.print("[red]❌ VS Code not found![/red]")
            console.print("Please install VS Code first: https://code.visualstudio.com")
            return
        
        # Create Continue configuration
        self._create_continue_config()
        
        # Show setup instructions
        self._show_continue_setup_guide()
        
        console.print("[green]✅ Continue setup configuration created![/green]")
        self.tools["continue"].status = "active"
    
    def _create_claude_project_configs(self):
        """Create Claude Desktop project configurations"""
        
        config_dir = self.cortex_root / ".claude-desktop"
        config_dir.mkdir(exist_ok=True)
        
        # Main Cortex project config
        cortex_config = {
            "name": "Cortex Hub Management",
            "description": "Multi-vault AI learning system with cross-vault intelligence",
            "path": str(self.cortex_root),
            "focus_areas": [
                "System architecture",
                "AI learning patterns", 
                "Vault management",
                "Cross-vault analysis"
            ],
            "key_directories": [
                "00-System",
                "01-Projects", 
                "02-Neural-Links",
                "03-Decisions",
                "cortex-cli"
            ]
        }
        
        with open(config_dir / "cortex-project.json", "w") as f:
            json.dump(cortex_config, f, indent=2)
    
    def _create_continue_config(self):
        """Create Continue configuration for Cortex development"""
        
        continue_config = {
            "models": [
                {
                    "title": "Claude Sonnet 3.5",
                    "provider": "anthropic",
                    "model": "claude-3-5-sonnet-20241022",
                    "apiKey": "[YOUR_ANTHROPIC_API_KEY]"
                }
            ],
            "tabAutocompleteModel": {
                "title": "Claude Sonnet 3.5 Fast",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022"
            },
            "contextProviders": [
                {"name": "code", "params": {}},
                {"name": "docs", "params": {}},
                {"name": "diff", "params": {}},
                {"name": "terminal", "params": {}},
                {"name": "problems", "params": {}},
                {"name": "folder", "params": {}}
            ],
            "slashCommands": [
                {
                    "name": "cortex-analyze",
                    "description": "Analyze Cortex vault structure and patterns"
                },
                {
                    "name": "cross-vault",
                    "description": "Perform cross-vault analysis"
                }
            ]
        }
        
        config_dir = Path.home() / ".continue"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "config.json", "w") as f:
            json.dump(continue_config, f, indent=2)
    
    def _show_claude_integration_guide(self):
        """Show Claude Desktop integration guide"""
        
        guide = """
🖥️ [bold blue]Claude Desktop Integration Guide[/bold blue]

[bold]1. Project Setup:[/bold]
  • Open Claude Desktop
  • Create new project: "Cortex Hub Management"
  • Add project folder: {cortex_root}
  • Description: "Multi-vault AI learning system"

[bold]2. Optimal Usage Patterns:[/bold]
  • 🏗️ System Architecture - Upload diagrams, review vault structures  
  • 📋 Project Planning - Multi-file analysis, cross-vault comparisons
  • 📊 Data Analysis - Analyze reports, metrics, logs
  • 🔍 Code Review - Upload complete codebases for review
  • 📝 Documentation - Create comprehensive docs with file refs

[bold]3. Best Practices:[/bold]
  • Upload multiple related files for better context
  • Use project-specific conversations for different vaults
  • Save important conversations for future reference
  • Combine with Continue for implementation workflow
        """.format(cortex_root=self.cortex_root)
        
        console.print(Panel(guide, border_style="blue", title="Integration Guide"))
    
    def _show_continue_setup_guide(self):
        """Show Continue setup guide"""
        
        guide = f"""
💻 [bold purple]Continue Setup Instructions[/bold purple]

[bold]1. Install Extension:[/bold]
  • Open VS Code
  • Go to Extensions (⌘+Shift+X)
  • Search for "Continue"
  • Install the Continue extension

[bold]2. Configure API:[/bold]
  • Configuration saved to: ~/.continue/config.json
  • Add your Anthropic API key to the config
  • Restart VS Code after configuration

[bold]3. Cortex Development Workflow:[/bold]
  • Use ⌘+L to start Continue chat
  • Select multiple files for context
  • Use /cortex-analyze for vault analysis
  • Use /cross-vault for multi-vault insights

[bold]4. Pro Tips:[/bold]
  • Select entire file ranges for better context
  • Use Continue for unlimited code generation
  • Combine with Claude Desktop for planning
        """
        
        console.print(Panel(guide, border_style="purple", title="Setup Guide"))
    
    def show_workflow_examples(self):
        """Show example workflows using the configured tools"""
        
        workflows = [
            {
                "name": "🏗️ New Project Architecture",
                "tools": ["Claude Desktop", "Continue"],
                "steps": [
                    "Claude Desktop: Analyze existing patterns in cortex hub",
                    "Claude Desktop: Upload project template and requirements", 
                    "Claude Desktop: Generate comprehensive architecture plan",
                    "Continue: Implement project structure and core components",
                    "Claude Desktop: Review generated code and documentation"
                ]
            },
            {
                "name": "🔍 Cross-Vault Analysis", 
                "tools": ["Claude Desktop", "Cortex AI"],
                "steps": [
                    "Claude Desktop: Upload files from multiple vaults",
                    "Claude Desktop: Compare architecture patterns",
                    "Claude Desktop: Identify reusable components",
                    "Cortex AI: Learn from identified patterns",
                    "Claude Desktop: Generate insights report"
                ]
            },
            {
                "name": "⚡ Rapid Development",
                "tools": ["Continue", "Web Claude"],
                "steps": [
                    "Continue: Generate initial code structure",
                    "Continue: Implement core functionality with context",
                    "Web Claude: Quick syntax and concept questions",
                    "Continue: Iterate and refine implementation",
                    "Continue: Generate tests and documentation"
                ]
            }
        ]
        
        for workflow in workflows:
            console.print(f"\n[bold cyan]{workflow['name']}[/bold cyan]")
            console.print(f"Tools: {', '.join(workflow['tools'])}")
            
            for i, step in enumerate(workflow['steps'], 1):
                console.print(f"  {i}. {step}")
    
    def open_integration_docs(self, tool: str = None):
        """Open integration documentation for specified tool"""
        
        docs = {
            "claude": self.tools_dir / "Claude-Desktop-Integration.md",
            "continue": self.tools_dir / "Continue-Integration-Guide.md", 
            "matrix": self.tools_dir / "Tool-Overview-Matrix.md"
        }
        
        if tool and tool in docs:
            doc_path = docs[tool]
            if doc_path.exists():
                console.print(f"[green]📖 Opening {doc_path.name}...[/green]")
                os.system(f"open '{doc_path}'" if os.name != 'nt' else f"start '{doc_path}'")
            else:
                console.print(f"[red]❌ Documentation not found: {doc_path}[/red]")
        else:
            console.print("[bold]Available documentation:[/bold]")
            for key, path in docs.items():
                status = "✅" if path.exists() else "❌"
                console.print(f"  {status} {key}: {path.name}")


# CLI Commands for dev-tools management
@click.group(name="dev-tools")
def dev_tools():
    """Development tools management and integration"""
    pass

@dev_tools.command()
def status():
    """Show status of all development tools"""
    manager = CortexDevToolsManager()
    manager.display_tool_matrix()

@dev_tools.command()
@click.argument('tool', type=click.Choice(['claude', 'continue', 'all']))
def setup(tool):
    """Setup development tool integration"""
    manager = CortexDevToolsManager()
    
    if tool == 'claude':
        manager.setup_claude_desktop()
    elif tool == 'continue':
        manager.setup_continue()
    elif tool == 'all':
        console.print("[bold blue]🚀 Setting up all development tools...[/bold blue]\n")
        manager.setup_claude_desktop()
        console.print()
        manager.setup_continue()
        console.print("\n[bold green]✅ All development tools setup completed![/bold green]")

@dev_tools.command()
def workflows():
    """Show example development workflows"""
    manager = CortexDevToolsManager()
    manager.show_workflow_examples()

@dev_tools.command()
@click.argument('doc', type=click.Choice(['claude', 'continue', 'matrix', 'all']), required=False)
def docs(doc):
    """Open integration documentation"""
    manager = CortexDevToolsManager()
    
    if doc and doc != 'all':
        manager.open_integration_docs(doc)
    elif doc == 'all':
        for tool in ['claude', 'continue', 'matrix']:
            manager.open_integration_docs(tool)
    else:
        manager.open_integration_docs()

if __name__ == "__main__":
    dev_tools()
