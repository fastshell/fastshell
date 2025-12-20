from typing import Callable, Optional


def command(name: Optional[str] = None, root: bool = False):
    """
    Decorator to register a command with FastShell
    
    Args:
        name: Command name (defaults to function name)
        root: If True, command can be called directly without command name
    """
    def decorator(func: Callable):
        # Store metadata on the function for later registration
        func._fastshell_command = True
        func._fastshell_name = name or func.__name__
        func._fastshell_root = root
        return func
    return decorator