#!/usr/bin/env python3
"""
FastShell CLI entry point
"""

import sys, os
from pathlib import Path
from toml import load
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
        name="FastShell CLI", description="FastShell command-line interface"
    )

    @app.command()
    def version():
        """Show FastShell version"""
        parent_dir = Path(__file__).parent.parent
        files = os.listdir(parent_dir)
        if "pyproject.toml" in files:
            pyproject_path = parent_dir / "pyproject.toml"
            with open(pyproject_path, "r") as f:
                data = load(f)
                version = data["tool"]["poetry"]["version"]
                return f"FastShell v{version}"
        elif x := next(
            filter(
                lambda x: x.startswith("fastshell-") and x.endswith(".dist-info"), files
            ),
            None,
        ):
            metadata_path = parent_dir / x / "METADATA"
            with open(metadata_path, "r") as f:
                data = f.read().split("\n")
                version = next(filter(lambda x: x.startswith("Version:"), data), None)
                if version:
                    version = version.split(":")[1].strip()
                    return f"FastShell v{version}"
        return "FastShell version not found"

    # Run the app
    app.run(args)


if __name__ == "__main__":
    main()
