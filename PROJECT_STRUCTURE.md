# FastShell Project Structure

```
fastshell/
├── fastshell/                 # Core framework package
│   ├── __init__.py           # Package initialization
│   ├── core.py               # Main FastShell class and functionality
│   ├── parser.py             # Argument parsing logic
│   ├── completer.py          # Autocompletion system
│   ├── lexer.py              # Syntax highlighting
│   ├── exceptions.py         # Custom exceptions
│   ├── decorators.py         # Command decorators
│   ├── models.py             # Pydantic models
│   └── cli.py                # CLI entry point
│
├── pyproject.toml            # Poetry configuration (modern)
├── .gitignore                # Git ignore rules
├── README.md                 # Main project README
├── example.py                # Quick start example
└── PROJECT_STRUCTURE.md      # This file
```

## Directory Purposes

### `/fastshell/` - Core Package
Contains the main FastShell framework implementation:
- **core.py**: Main FastShell class, command execution, interactive shell
- **parser.py**: Argument parsing with Pydantic integration
- **completer.py**: Context-aware autocompletion system
- **lexer.py**: Syntax highlighting for commands
- **exceptions.py**: Custom exception classes
- **decorators.py**: Command registration decorators
- **models.py**: Pydantic model utilities

## Key Files

### Root Level
- **README.md**: Project overview, installation, quick start
- **pyproject.toml**: Poetry configuration (modern Python packaging)
- **setup.py**: Legacy setuptools configuration (compatibility)
- **.gitignore**: Git ignore patterns
- **example.py**: Minimal working example for quick testing

### Framework Core
- **fastshell/core.py**: 700+ lines, main framework implementation
- **fastshell/completer.py**: 200+ lines, autocompletion logic
- **fastshell/parser.py**: 100+ lines, argument parsing
- **fastshell/lexer.py**: 100+ lines, syntax highlighting
- **fastshell/cli.py**: CLI entry point for the fastshell command

## Development Workflow

### Modern (Poetry)
1. **Setup**: `poetry install` - Install dependencies
2. **Development**: `poetry shell` - Activate environment
3. **Testing**: `poetry run pytest` or `make test`
4. **Quality**: `make quality` - Run all checks
5. **Build**: `poetry build` - Build package

## File Naming Conventions

- **Core files**: Descriptive names (core.py, parser.py, etc.)

This structure provides clear separation of concerns while maintaining easy navigation and development workflow.