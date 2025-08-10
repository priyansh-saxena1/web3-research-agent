from typing import Dict, Any

class CustomException(Exception):
    pass

class APIError(CustomException):
    pass

class RateLimitError(APIError):
    pass

class DataValidationError(CustomException):
    pass

class ConfigurationError(CustomException):
    pass
