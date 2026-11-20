class LLMError(Exception):
    """Base exception for LLM-related failures."""


class LLMTemporaryError(LLMError):
    """Temporary failure that may succeed on retry."""


class LLMConfigurationError(LLMError):
    """Configuration or authentication failure."""