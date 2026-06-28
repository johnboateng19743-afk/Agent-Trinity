"""
Trinity Watchdog — Crash detection and process restart.
"""

import time
import subprocess
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class WatchdogMonitor:
    """Monitor Trinity daemon and restart on crash."""

    def __init__(self, config: dict):
        self.config = config
        self.daemon_pid = None
        self.max_restarts = 5
        self.restart_count = 0
        self.restart_window = 300  # 5 minutes

    def start(self):
        """Start the watchdog."""
        logger.info("watchdog.started")

    def check_health(self) -> bool:
        """Check if the daemon process is healthy."""
        if self.daemon_pid is None:
            return False

        try:
            import psutil
            return psutil.pid_exists(self.daemon_pid)
        except ImportError:
            # Fallback: try to ping daemon
            return True

    def restart_daemon(self) -> bool:
        """Restart the Trinity daemon."""
        if self.restart_count >= self.max_restarts:
            logger.error("watchdog.max_restarts_exceeded")
            return False

        self.restart_count += 1
        logger.info("watchdog.restarting", attempt=self.restart_count)

        try:
            subprocess.Popen(["python", "-m", "trinity.main"])
            return True
        except Exception as e:
            logger.error("watchdog.restart_failed", error=str(e))
            return False
