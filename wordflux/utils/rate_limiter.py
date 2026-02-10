import time
import asyncio
import logging
from collections import deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simples algorithm to limit Requests Per Minute (RPM) and Tokens Per Minute (TPM).
    Uses a sliding window approach.
    """
    def __init__(self, rpm: int, tpm: int, window: int = 60):
        self.rpm = rpm
        self.tpm = tpm
        self.window = window
        self.request_timestamps = deque()
        self.token_timestamps = deque()
        self.lock = asyncio.Lock()
        
    async def acquire(self, estimated_tokens: int = 0):
        """
        Wait until it is safe to make a request.
        """
        async with self.lock:
            while True:
                now = time.time()
                
                # Cleanup old timestamps (remove events older than window)
                while self.request_timestamps and now - self.request_timestamps[0] > self.window:
                    self.request_timestamps.popleft()
                    
                while self.token_timestamps and now - self.token_timestamps[0][0] > self.window:
                    self.token_timestamps.popleft()
                    
                # RPM Check
                current_rpm = len(self.request_timestamps)
                if self.rpm > 0 and current_rpm >= self.rpm:
                    # Wait until the oldest request expires
                    wait_time = self.window - (now - self.request_timestamps[0]) + 0.5 # Add small buffer
                    if wait_time > 0:
                        logger.warning(f"⏳ Rate Limit (RPM): {current_rpm}/{self.rpm}. Sleeping for {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        continue # Re-evaluate after sleep

                # TPM Check
                current_tpm = sum(t[1] for t in self.token_timestamps)
                if self.tpm > 0 and current_tpm + estimated_tokens > self.tpm:
                    # Wait until enough tokens expire. 
                    # Implementation detail: simply wait for the oldest token batch to expire
                    if self.token_timestamps:
                        wait_time = self.window - (now - self.token_timestamps[0][0]) + 0.5
                        if wait_time > 0:
                            logger.warning(f"⏳ Rate Limit (TPM): {current_tpm}/{self.tpm}. Sleeping for {wait_time:.2f}s...")
                            await asyncio.sleep(wait_time)
                            continue # Re-evaluate

                # If we passed checks, record this request
                self.request_timestamps.append(now)
                self.token_timestamps.append((now, estimated_tokens))
                break
