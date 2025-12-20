# FastShell

A FastAPI-like framework for building interactive shell applications with fish-like features including autocompletion, syntax highlighting, and history-based suggestions.

## Features

- **FastAPI-like syntax** - Familiar decorator-based command registration
- **Pydantic integration** - Type-safe argument parsing with validation
- **Interactive shell** - Fish-like experience with autocompletion and syntax highlighting
- **Async support** - Full support for async/await commands
- **Subcommands** - Organize commands into logical groups
- **System commands** - Optional integration with system executables
- **Flexible arguments** - Support for positional, optional, and flag-based arguments

## Quick Start

```python
from fastshell import FastShell
from pydantic import BaseModel

app = FastShell(name="MyApp", description="My awesome shell app")

class Arguments(BaseModel):
    name: str
    age: int = 18

@app.command(name='hello', root=True)
def hello(args: Arguments):
    app.print(f'Hello, {args.name}! You are {args.age} years old.')

if __name__ == "__main__":
    app.run()
```

## Command Usage Examples

The above command can be called in multiple ways:

```bash
# Positional arguments
hello John 25

# Mixed positional and flags
hello --age 25 John

# All flags
hello --name John --age 25

# Default values
hello John  # age defaults to 18
```

## Installation

### Using Poetry (Recommended)
```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone <repository-url>
cd fastshell
poetry install

# Activate the environment
poetry shell
```

### Using pip (Traditional)
```bash
pip install -r requirements.txt
```

### Development Installation
```bash
# Install with development dependencies
poetry install

# Set up pre-commit hooks
poetry run pre-commit install
```

## Running Examples

### Quick Start
```bash
# With Poetry
poetry run python example.py

# With pip
python example.py
```

### Comprehensive Demo
```bash
# With Poetry
poetry run python demos/final_fastshell_demo.py

# With pip
python demos/final_fastshell_demo.py
```

### Feature-Specific Demos
```bash
# With Poetry
poetry run python demos/completion_demo.py          # Autocompletion features
poetry run python demos/syntax_highlighting_demo.py # Syntax highlighting
poetry run python demos/pydantic_features_demo.py   # Pydantic integration
poetry run python demos/system_command_demo.py      # System command integration

# With pip - same commands without 'poetry run'
```

### CLI Tool
```bash
# After Poetry installation
poetry run fastshell

# Or activate shell first
poetry shell
fastshell
```

The interactive shell supports commands like:
- `hello John Doe 25`
- `echo "Hello World"`
- `add 5 3`
- `sleep hrs 1`
- `file write test.txt "Hello World"`

## Features in Detail

### Autocompletion
- Command name completion
- Argument flag completion with type information
- Context-aware suggestions

### Syntax Highlighting
- Commands highlighted in blue
- Arguments in green
- Strings in yellow
- Numbers in magenta
- Flags in cyan

### Argument Parsing
- Automatic conversion between flag names and field names (`--first-name` ↔ `first_name`)
- Type validation using Pydantic
- Error handling for ambiguous arguments
- Support for boolean flags

### Subcommands
Create command groups for better organization:

```python
file_ops = app.subinstance('file')

@file_ops.command('read')
def read_file(path: str):
    # Implementation
    pass
```

Usage: `file read myfile.txt`

## Development

### Using Poetry
```bash
# Install development dependencies
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy fastshell/

# Run all quality checks
make quality

# Build package
poetry build
```

### Using Make (Poetry required)
```bash
# On Linux/macOS
make help           # Show all available commands
make install-dev    # Install development dependencies
make test           # Run tests
make format         # Format code
make lint           # Run linting
make type-check     # Run type checking
make build          # Build package

# On Windows (PowerShell)
.\make.ps1 help           # Show all available commands
.\make.ps1 install-dev    # Install development dependencies
.\make.ps1 test           # Run tests
.\make.ps1 format         # Format code
.\make.ps1 lint           # Run linting
.\make.ps1 type-check     # Run type checking
.\make.ps1 build          # Build package
```

## Project Structure

```
fastshell/
├── fastshell/          # Core framework package
├── demos/              # Interactive demonstrations
├── tests/              # Comprehensive test suite
├── docs/               # Documentation and guides
├── example.py          # Quick start example
└── README.md           # This file
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information.

## Documentation

- **[docs/USAGE.md](docs/USAGE.md)** - Comprehensive usage guide
- **[docs/SUMMARY.md](docs/SUMMARY.md)** - Complete development history
- **[docs/](docs/)** - Feature-specific documentation
- **[demos/](demos/)** - Interactive examples and demonstrations
- **[tests/](tests/)** - Test suite for all features

## License

MIT License