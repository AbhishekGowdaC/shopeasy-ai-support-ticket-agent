import random


BASE_DELAY = 2
MAX_DELAY = 60


def calculate_retry_delay(attempt: int) -> float:

    delay = BASE_DELAY * (2 ** (attempt - 1))

    delay = min(delay, MAX_DELAY)

    # Add random jitter between 0 and 1 second
    jitter = random.uniform(0, 1)

    return delay + jitter