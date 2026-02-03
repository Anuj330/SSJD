import logging
from fastapi import Request

logger = logging.getLogger("request")

async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Completed {response.status_code}")
    return response
