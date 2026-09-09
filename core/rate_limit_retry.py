import asyncio
import logging
import random
import re
from typing import Callable, TypeVar, Awaitable

import openai
from graphiti_core.llm_client.errors import RateLimitError as GraphitiRateLimitError

logger = logging.getLogger(__name__)

T = TypeVar("T")

async def with_rate_limit_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    op_name: str,
    request_id: str | None = None,
    max_attempts: int = 12,
    base_sleep: float = 2.0,
    on_rate_limit: Callable[[float, int], None] | None = None
) -> T:
    """
    Executes an async operation with retries on RateLimitError.
    
    Args:
        operation: A callable that returns the coroutine to execute (e.g. lambda: func(...))
        op_name: Name of the operation for logging
        request_id: Optional request ID for logging context
        max_attempts: Maximum number of attempts
        base_sleep: Base sleep time for exponential backoff
        on_rate_limit: Optional callback(sleep_seconds, attempt) to update status
    """
    attempt = 1
    req_tag = f" [req_id={request_id}]" if request_id else ""
    
    while True:
        try:
            return await operation()
        except (openai.RateLimitError, GraphitiRateLimitError) as e:
            if attempt >= max_attempts:
                logger.error(f"[{op_name}]{req_tag} Rate limit exceeded, max attempts ({max_attempts}) reached. Error: {e}")
                raise

            # Determine sleep time
            sleep_s = 0.0
            error_msg = str(e)
            
            # Try to parse "Please try again in X.Xs" or similar variants
            match = re.search(r"Please try again in (\d+(\.\d+)?)s", error_msg)
            if match:
                sleep_s = float(match.group(1)) + 0.5  # Add small buffer
            else:
                # Exponential backoff: 1, 2, 4, 8...
                sleep_s = base_sleep * (2 ** (attempt - 1))
                # Cap at 30s
                sleep_s = min(sleep_s, 30.0)
            
            # Add jitter (0-10% of sleep time)
            jitter = sleep_s * 0.1 * random.random()
            sleep_s += jitter

            logger.warning(f"[{op_name}]{req_tag} Rate limit hit (attempt {attempt}/{max_attempts}). Sleeping {sleep_s:.2f}s. Error: {e}")
            
            if on_rate_limit:
                try:
                    on_rate_limit(sleep_s, attempt)
                except Exception as cb_err:
                    logger.error(f"[{op_name}]{req_tag} Error in on_rate_limit callback: {cb_err}")
            
            await asyncio.sleep(sleep_s)
            attempt += 1
