class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    """Raised when authentication or authorization fails."""


class ChatError(AppError):
    """Raised when chat or file upload operations fail."""
