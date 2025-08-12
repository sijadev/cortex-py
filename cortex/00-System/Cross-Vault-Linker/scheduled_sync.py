#!/usr/bin/env python3
"""
Scheduled Sync Tool - Alternative zum File-Watcher
Führt periodische Synchronisation ohne File-Watching durch
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import argparse

class ScheduledSync:
    """Periodische Synchronisation ohne File-Watching"""
    
    def __init__(self, cortex_path: str, interval_minutes: int = 30):
        self.cortex_path = Path(cortex_path)
        self.interval_minutes = interval_minutes
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_running = False
        self.last_sync = None
        
    async def start_scheduled_sync(self):
        """Startet die geplante Synchronisation"""
        self.is_running = True
        self.logger.info(f"Starting scheduled sync every {self.interval_minutes} minutes")
        
        while self.is_running:
            try:
                await self._run_sync_cycle()
                self.last_sync = datetime.now()
                
                # Warten bis zum nächsten Zyklus
                await asyncio.sleep(self.interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in sync cycle: {e}")
                await asyncio.sleep(60)  # Bei Fehler 1 Minute warten
    
    async def _run_sync_cycle(self):
        """Führt einen Synchronisationszyklus aus"""
        self.logger.info("Running scheduled sync cycle...")
        
        try:
            # Import und Ausführung der Cortex-Komponenten
            from cross_vault_linker import CrossVaultLinker
            
            linker = CrossVaultLinker(hub_vault_path=str(self.cortex_path))
            report = await linker.run_full_linking_cycle_async(sync_to_obsidian=True)
            
            if report:
                self.logger.info(f"Sync completed: {report.get('summary', 'Success')}")
            else:
                self.logger.warning("Sync cycle returned no report")
                
        except ImportError as e:
            self.logger.error(f"Could not import required components: {e}")
        except Exception as e:
            self.logger.error(f"Error during sync cycle: {e}")
    
    def stop_sync(self):
        """Stoppt die geplante Synchronisation"""
        self.is_running = False
        self.logger.info("Scheduled sync stopped")
    
    def get_status(self) -> dict:
        """Gibt den aktuellen Status zurück"""
        return {
            'is_running': self.is_running,
            'interval_minutes': self.interval_minutes,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'cortex_path': str(self.cortex_path)
        }

async def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description="Scheduled Sync for Cortex")
    parser.add_argument("--cortex-path", default="/Users/simonjanke/Projects/cortex",
                       help="Path to Cortex hub")
    parser.add_argument("--interval", type=int, default=30,
                       help="Sync interval in minutes")
    parser.add_argument("--test-duration", type=int, default=0,
                       help="Test duration in minutes (0 = run indefinitely)")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("ScheduledSyncCLI")
    
    sync = ScheduledSync(args.cortex_path, args.interval)
    
    try:
        logger.info(f"Starting scheduled sync with {args.interval} minute intervals")
        
        if args.test_duration > 0:
            logger.info(f"Running for {args.test_duration} minutes...")
            # Starte Sync-Task
            sync_task = asyncio.create_task(sync.start_scheduled_sync())
            
            # Warte für Test-Dauer
            await asyncio.sleep(args.test_duration * 60)
            
            # Stoppe und zeige Status
            sync.stop_sync()
            sync_task.cancel()
            
            try:
                await sync_task
            except asyncio.CancelledError:
                pass
                
            logger.info(f"Test completed. Status: {json.dumps(sync.get_status(), indent=2, default=str)}")
        else:
            logger.info("Running continuously. Press Ctrl+C to stop.")
            await sync.start_scheduled_sync()
            
    except KeyboardInterrupt:
        logger.info("Stopping scheduled sync...")
        sync.stop_sync()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())