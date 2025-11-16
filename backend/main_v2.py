"""
Main entry point for SDAF Chat Agent v2
Runs the FastAPI application with proper configuration
"""

import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("🚀 Starting SDAF Chat Agent v2...")

    uvicorn.run(
        "chat_agent_v2:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
