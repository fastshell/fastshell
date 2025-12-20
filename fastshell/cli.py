#!/usr/bin/env python3
"""
FastShell CLI entry point
"""

import sys
from typing import Optional, List
from .core import FastShell


def main(args: Optional[List[str]] = None) -> None:
    """
    Main CLI entry point for FastShell
    
    This is a placeholder implementation. In a real application,
    you would create your FastShell app here or import it from
    your application module.
    """
    if args is None:
        args = sys.argv[1:]
    
    # Example FastShell app
    app = FastShell(
        name="FastShell CLI",
        description="FastShell command-line interface"
    )
    
    @app.command()
    def hello(name: str = "World"):
        """Say hello to someone"""
        return f"Hello, {name}!"
    
    @app.command()
    def version():
        """Show FastShell version"""
        return "FastShell v0.1.0"
    
    # Run the app
    app.run(args)


if __name__ == "__main__":
    main()