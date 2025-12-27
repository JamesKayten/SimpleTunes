#!/usr/bin/env python3
"""SimpleTunes Backend Daemon - Production server wrapper."""

import os
import sys
import signal
import logging
from pathlib import Path

import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            Path.home() / "Library" / "Application Support" / "SimpleTunes" / "daemon.log"
        ),
    ],
)

logger = logging.getLogger("simpletunes.daemon")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Run the SimpleTunes backend daemon."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configuration
    host = os.getenv("SIMPLETUNES_HOST", "127.0.0.1")
    port = int(os.getenv("SIMPLETUNES_PORT", "49917"))
    reload = os.getenv("SIMPLETUNES_RELOAD", "false").lower() == "true"
    workers = int(os.getenv("SIMPLETUNES_WORKERS", "1"))

    logger.info(f"Starting SimpleTunes daemon on {host}:{port}")
    logger.info(f"Workers: {workers}, Reload: {reload}")

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level="info",
            access_log=True,
        )
    except Exception as e:
        logger.error(f"Failed to start daemon: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
