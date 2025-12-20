class FastShellException(Exception):
    """Base exception for FastShell"""

    pass


class MultiplePossibleMatchError(FastShellException):
    """Raised when arguments are specified both positionally and as flags"""

    pass
