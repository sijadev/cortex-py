#!/usr/bin/env python3
"""
Cortex Multi-Vault Management Service
Orchestrates AI learning and cross-vault linking for the entire Cortex ecosystem
"""

import os
import sys
import time
import json
import logging
import schedule
from pathlib import Path
from datetime import datetime
import subprocess

# Add system paths
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/AI-Learning-Engine')
sys.path.append('/Users/simonjanke/Projects/cortex/00-System/Cross-Vault-Linker')

from multi_vault_ai import MultiVaultAILearningEngine
from cross_vault_linker import CrossVaultLinker

class CortexManagementService:
    """Main orchestration service for Cortex multi-vault system"""
    
    def __init__(self, hub_vault_path: str = "/Users/simonjanke/Projects/cortex"):
        self.hub_path = Path(hub_vault_path)
        self.service_path = self.hub_path / "00-System" / "Management-Service"
        self.logs_path = self.service_path / "logs"
        self.data_path = self.service_path / "data"
        
        # Ensure directories exist
        for path in [self.service_path, self.logs_path, self.data_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.ai_engine = MultiVaultAILearningEngine(hub_vault_path)
        self.vault_linker = CrossVaultLinker(hub_vault_path)
        
        # Service state
        self.last_full_analysis = None
        self.last_linking_cycle = None
        self.service_stats = {
            'cycles_completed': 0,
            'vaults_discovered': 0,
            'links_generated': 0,
            'patterns_detected': 0,
            'uptime_start': datetime.now().isoformat()
        }
        
        self.logger.info("Cortex Management Service initialized")
    
    def setup_logging(self):
        """Configure logging for the management service"""
        log_file = self.logs_path / "management_service.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('CortexManagementService')
    
    def run_full_cycle(self):
        """Run complete AI analysis and cross-vault linking cycle"""
        self.logger.info("Starting full Cortex learning and linking cycle")
        cycle_start = datetime.now()
        
        try:
            # 1. Run AI Learning Analysis
            self.logger.info("Phase 1: Running AI learning analysis")
            ai_report = self.ai_engine.run_full_analysis()
            
            if ai_report:
                self.logger.info(f"AI Analysis completed: {ai_report['summary']}")
                self.last_full_analysis = cycle_start.isoformat()
            else:
                self.logger.error("AI analysis failed")
                return False
            
            # 2. Run Cross-Vault Linking
            self.logger.info("Phase 2: Running cross-vault linking")
            linking_report = self.vault_linker.run_full_linking_cycle()
            
            if linking_report:
                self.logger.info(f"Cross-vault linking completed: {linking_report['summary']}")
                self.last_linking_cycle = cycle_start.isoformat()
            else:
                self.logger.error("Cross-vault linking failed")
                return False
            
            # 3. Update service statistics
            self.service_stats['cycles_completed'] += 1
            self.service_stats['vaults_discovered'] = ai_report['summary']['vaults_analyzed']
            self.service_stats['links_generated'] = linking_report['summary']['total_link_suggestions']
            self.service_stats['patterns_detected'] = ai_report['summary']['cross_vault_patterns']
            
            # 4. Generate combined report
            combined_report = self.generate_combined_report(ai_report, linking_report)
            
            # 5. Update vault registry
            self.update_vault_registry(ai_report, linking_report)
            
            # 6. Send notifications if significant findings
            self.send_notifications(combined_report)
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.logger.info(f"Full cycle completed in {cycle_duration:.1f} seconds")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in full cycle: {e}")
            return False
    
    def generate_combined_report(self, ai_report, linking_report):
        """Generate combined analysis and linking report"""
        combined_report = {
            'timestamp': datetime.now().isoformat(),
            'cycle_id': f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'service_stats': self.service_stats,
            'ai_analysis': {
                'vaults_analyzed': ai_report['summary']['vaults_analyzed'],
                'tag_correlations': ai_report['summary']['tag_correlations_found'],
                'patterns_detected': ai_report['summary']['cross_vault_patterns'],
                'insights_generated': ai_report['summary']['insights_generated']
            },
            'cross_vault_linking': {
                'total_suggestions': linking_report['summary']['total_link_suggestions'],
                'strong_links': linking_report['summary']['strong_links'],
                'medium_links': linking_report['summary']['medium_links'],
                'weak_links': linking_report['summary']['weak_links'],
                'vault_connections': linking_report['summary']['vault_connections']
            },
            'top_insights': ai_report.get('insights', [])[:3],
            'top_connections': linking_report.get('top_suggestions', [])[:5],
            'recommendations': self.generate_cycle_recommendations(ai_report, linking_report)
        }
        
        # Save combined report
        report_file = self.logs_path / f"combined_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(combined_report, f, indent=2, default=str)
        
        return combined_report
    
    def send_notifications(self, report):
        """Send macOS notifications for significant findings"""
        try:
            # Notify for strong connections
            if report['cross_vault_linking']['strong_links'] > 0:
                title = "Cortex: Strong Connections Found"
                message = f"Found {report['cross_vault_linking']['strong_links']} high-confidence cross-vault connections"
                self.send_macos_notification(title, message)
            
            # Notify for new patterns
            if report['ai_analysis']['patterns_detected'] > 0:
                title = "Cortex: New Patterns Detected"
                message = f"AI discovered {report['ai_analysis']['patterns_detected']} new cross-vault patterns"
                self.send_macos_notification(title, message)
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
    
    def send_macos_notification(self, title, message):
        """Send macOS notification"""
        try:
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], check=False)
        except Exception as e:
            self.logger.error(f"Error sending macOS notification: {e}")
    
    def generate_cycle_recommendations(self, ai_report, linking_report):
        """Generate recommendations based on cycle results"""
        recommendations = []
        
        # AI-based recommendations
        if ai_report['summary']['tag_correlations_found'] > 10:
            recommendations.append("Consider creating a tag taxonomy to organize the many correlations")
        elif ai_report['summary']['tag_correlations_found'] < 3:
            recommendations.append("Increase consistent tagging across vaults to improve AI learning")
        
        # Linking-based recommendations
        if linking_report['summary']['strong_links'] > 5:
            recommendations.append("Review strong cross-vault connections for manual linking opportunities")
        
        if linking_report['summary']['vault_connections'] == 0:
            recommendations.append("Consider adding shared tags between vaults to enable connections")
        
        return recommendations
    
    def update_vault_registry(self, ai_report, linking_report):
        """Update the vault registry with latest information"""
        try:
            registry_file = self.hub_path / "08-Docs" / "Vault-Registry.md"
            
            if registry_file.exists():
                # Read current registry
                with open(registry_file, 'r') as f:
                    content = f.read()
                
                # Update statistics section
                stats_section = f"""
## 📊 **Real-Time Statistics** (Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')})

### **System Performance:**
- **Cycles Completed:** {self.service_stats['cycles_completed']}
- **Vaults Discovered:** {self.service_stats['vaults_discovered']}
- **Active Cross-Vault Links:** {linking_report['summary']['total_link_suggestions']}
- **Detected Patterns:** {ai_report['summary']['cross_vault_patterns']}
- **Tag Correlations:** {ai_report['summary']['tag_correlations_found']}

### **Last Analysis Results:**
- **AI Learning Accuracy:** {ai_report['summary']['insights_generated']} insights generated
- **Strong Connections:** {linking_report['summary']['strong_links']} high-confidence links
- **Vault Connections:** {linking_report['summary']['vault_connections']} inter-vault relationships

"""
                
                # Update or append statistics
                if "## 📊 **Real-Time Statistics**" in content:
                    # Replace existing statistics
                    lines = content.split('\n')
                    new_lines = []
                    skip_stats = False
                    
                    for line in lines:
                        if "## 📊 **Real-Time Statistics**" in line:
                            skip_stats = True
                            new_lines.extend(stats_section.strip().split('\n'))
                        elif skip_stats and line.startswith('## ') and "Real-Time Statistics" not in line:
                            skip_stats = False
                            new_lines.append(line)
                        elif not skip_stats:
                            new_lines.append(line)
                    
                    content = '\n'.join(new_lines)
                else:
                    # Append statistics before the end
                    content = content.rstrip() + '\n\n' + stats_section
                
                # Write updated registry
                with open(registry_file, 'w') as f:
                    f.write(content)
                
                self.logger.info("Vault registry updated with latest statistics")
            
        except Exception as e:
            self.logger.error(f"Error updating vault registry: {e}")
    
    def get_status_summary(self):
        """Get current status summary"""
        return {
            'service_status': 'running',
            'uptime_hours': (datetime.now() - datetime.fromisoformat(self.service_stats['uptime_start'])).total_seconds() / 3600,
            'cycles_completed': self.service_stats['cycles_completed'],
            'vaults_discovered': self.service_stats['vaults_discovered'],
            'links_generated': self.service_stats['links_generated'],
            'last_analysis': self.last_full_analysis,
            'last_linking': self.last_linking_cycle
        }


def main():
    """Main entry point"""
    service = CortexManagementService()
    
    print("🤖 Cortex Multi-Vault Management Service")
    print("Starting comprehensive Cortex ecosystem management...")
    
    # Run single cycle for testing
    success = service.run_full_cycle()
    
    if success:
        print("\n✅ Management cycle completed successfully!")
        status = service.get_status_summary()
        print(f"📊 Status Summary:")
        print(f"  - Service uptime: {status['uptime_hours']:.1f} hours")
        print(f"  - Cycles completed: {status['cycles_completed']}")
        print(f"  - Vaults discovered: {status['vaults_discovered']}")
        print(f"  - Links generated: {status['links_generated']}")
    else:
        print("❌ Management cycle failed")


if __name__ == "__main__":
    main()
