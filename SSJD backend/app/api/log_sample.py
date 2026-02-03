import logging

logger = logging.getLogger(__name__)

logger.info("Society created successfully")
logger.warning("Invalid login attempt")
logger.error("Database connection failed", exc_info=True)
