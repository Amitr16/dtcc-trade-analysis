import os
import sys
import subprocess
import logging
import threading
import time
from datetime import datetime
import signal

logger = logging.getLogger(__name__)

class DTCCScheduler:
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.thread = None
        self.script_dir = os.path.dirname(os.path.dirname(__file__))
        
    def start(self):
        """Start the background scheduler"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.thread.start()
            logger.info("DTCC Scheduler started - will run scripts every 60 seconds")
            
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("DTCC Scheduler stopped")
        
    def _run_scheduler(self):
        """Main scheduler loop - runs every 60 seconds"""
        logger.info("Scheduler loop started")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Log the execution attempt
                logger.info(f"Starting automatic execution at {datetime.now()}")
                
                # Step 1: Run DTCCParser.py to fetch new data
                self._run_dtcc_parser()
                
                # Step 2: Run DTCCAnalysis.py to analyze data
                self._run_dtcc_analysis()
                
                execution_time = time.time() - start_time
                logger.info(f"Automatic execution completed in {execution_time:.2f} seconds")
                
                # Sleep for 60 seconds (1 minute)
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Continue running even if there's an error
                time.sleep(60)
                
    def _run_dtcc_parser(self):
        """Run DTCCParser.py to fetch new data"""
        try:
            parser_script = os.path.join(self.script_dir, 'DTCCParser.py')
            
            if os.path.exists(parser_script):
                logger.info("Running DTCCParser.py...")
                
                result = subprocess.run([
                    'python3', parser_script
                ], cwd=self.script_dir, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("DTCCParser.py completed successfully")
                    if result.stdout:
                        logger.info(f"Parser output: {result.stdout.strip()}")
                else:
                    logger.error(f"DTCCParser.py failed: {result.stderr}")
                    
            else:
                logger.warning("DTCCParser.py not found")
                
        except subprocess.TimeoutExpired:
            logger.error("DTCCParser.py timed out")
        except Exception as e:
            logger.error(f"Error running DTCCParser.py: {e}")
            
    def _run_dtcc_analysis(self):
        """Run DTCCAnalysis.py to analyze data"""
        try:
            analysis_script = os.path.join(self.script_dir, 'DTCCAnalysis.py')
            
            if os.path.exists(analysis_script):
                logger.info("Running DTCCAnalysis.py...")
                
                result = subprocess.run([
                    'python3', analysis_script
                ], cwd=self.script_dir, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    logger.info("DTCCAnalysis.py completed successfully")
                    if result.stdout:
                        logger.info(f"Analysis output: {result.stdout.strip()}")
                else:
                    logger.error(f"DTCCAnalysis.py failed: {result.stderr}")
                    
            else:
                logger.warning("DTCCAnalysis.py not found")
                
        except subprocess.TimeoutExpired:
            logger.error("DTCCAnalysis.py timed out")
        except Exception as e:
            logger.error(f"Error running DTCCAnalysis.py: {e}")
            
    def run_manual(self):
        """Manually trigger both scripts"""
        try:
            logger.info("Manual execution triggered")
            self._run_dtcc_parser()
            self._run_dtcc_analysis()
            return True
        except Exception as e:
            logger.error(f"Error in manual execution: {e}")
            return False
            
    def run_analysis_only(self):
        """Manually trigger analysis only"""
        try:
            logger.info("Manual analysis triggered")
            self._run_dtcc_analysis()
            return True
        except Exception as e:
            logger.error(f"Error in manual analysis: {e}")
            return False
            
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'script_dir': self.script_dir
        }

# Global scheduler instance
scheduler = None

def init_scheduler(app):
    """Initialize the global scheduler"""
    global scheduler
    scheduler = DTCCScheduler(app)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal")
        if scheduler:
            scheduler.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    return scheduler

def get_scheduler():
    """Get the global scheduler instance"""
    return scheduler

