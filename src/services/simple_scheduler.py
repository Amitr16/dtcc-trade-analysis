import os
import sys
import subprocess
import logging
import time
import threading
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SimpleScheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.script_dir = os.path.dirname(os.path.dirname(__file__))
        self.last_run = None
        self.status_file = os.path.join(self.script_dir, 'scheduler_status.json')
        
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("Simple scheduler started")
            self._update_status("started")
            
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Simple scheduler stopped")
        
    def _run_loop(self):
        """Main loop - runs every 60 seconds"""
        while self.running:
            try:
                current_time = datetime.now()
                logger.info(f"Running automatic execution at {current_time}")
                
                # Run both scripts
                success = self._run_scripts()
                
                # Update status
                self._update_status("completed" if success else "failed")
                self.last_run = current_time
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self._update_status("error", str(e))
                time.sleep(60)
                
    def _run_scripts(self):
        """Run both DTCCParser and DTCCAnalysis"""
        try:
            # Get the correct Python executable path
            python_exe = sys.executable
            
            # Run DTCCParser.py
            parser_path = os.path.join(self.script_dir, 'DTCCParser.py')
            if os.path.exists(parser_path):
                logger.info("Running DTCCParser.py...")
                result = subprocess.run([
                    python_exe, parser_path
                ], cwd=self.script_dir, capture_output=True, text=True, timeout=120)
                
                if result.returncode != 0:
                    logger.error(f"DTCCParser failed: {result.stderr}")
            
            # Run DTCCAnalysis.py
            analysis_path = os.path.join(self.script_dir, 'DTCCAnalysis.py')
            if os.path.exists(analysis_path):
                logger.info("Running DTCCAnalysis.py...")
                result = subprocess.run([
                    python_exe, analysis_path
                ], cwd=self.script_dir, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("Scripts completed successfully")
                    return True
                else:
                    logger.error(f"DTCCAnalysis failed: {result.stderr}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error running scripts: {e}")
            return False
            
    def _update_status(self, status, error=None):
        """Update status file"""
        try:
            status_data = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'last_run': self.last_run.isoformat() if self.last_run else None,
                'error': error,
                'running': self.running
            }
            
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f)
                
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            
    def get_status(self):
        """Get current status"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'status': 'not_started',
                    'timestamp': None,
                    'last_run': None,
                    'error': None,
                    'running': self.running
                }
        except Exception as e:
            logger.error(f"Error reading status: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'last_run': None,
                'error': str(e),
                'running': False
            }
            
    def run_manual(self):
        """Manual execution"""
        try:
            logger.info("Manual execution triggered")
            success = self._run_scripts()
            self._update_status("manual_completed" if success else "manual_failed")
            return success
        except Exception as e:
            logger.error(f"Error in manual execution: {e}")
            self._update_status("manual_error", str(e))
            return False

# Global instance
_scheduler = None

def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = SimpleScheduler()
    return _scheduler

def init_scheduler():
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler

