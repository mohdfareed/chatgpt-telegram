"""The errors generated by chat completions."""


class CompletionError(Exception):
    """An exception raised when a completion request fails."""
    pass


class ConnectionError(CompletionError):
    """An exception raised when a completion fails due to connectivity."""
    pass


class TokenLimitError(CompletionError):
    """An exception raised when a completion reaches the tokens limit."""
    pass


class InvalidParameterError(Exception):
    """An exception raised when a model's parameter is invalid."""
    pass