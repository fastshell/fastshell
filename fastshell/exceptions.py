# Copyright (c) 2026 github.com/fastshell
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

class FastShellException(Exception):
    """Base exception for FastShell"""

    pass


class MultiplePossibleMatchError(FastShellException):
    """Raised when arguments are specified both positionally and as flags"""

    pass
