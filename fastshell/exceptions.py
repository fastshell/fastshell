class FastShellException(Exception):
    """Base exception for FastShell"""
    pass


class MultiplePossibleMatchError(FastShellException):
    """Raised when arguments are specified both positionally and as flags"""
    pass


class CommandNotFoundError(FastShellException):
    """Raised when a command is not found"""
    pass


class ArgumentParsingError(FastShellException):
    """Raised when argument parsing fails"""
    pass