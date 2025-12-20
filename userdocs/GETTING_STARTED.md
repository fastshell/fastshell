# Getting Started with FastShell

FastShell is a modern Python framework for building interactive command-line applications with FastAPI-like syntax. This guide will help you get started quickly.

## Installation

### From Source

```bash
git clone https://github.com/fastshell/fastshell.git
cd fastshell
pip install -e .
```

### Dependencies

FastShell requires Python 3.7+ and the following packages:

- `pydantic` - For data validation and parsing
- `prompt-toolkit` - For interactive shell features
- `toml` - For configuration file support

## Your First FastShell Application

Create a file called `hello.py`:

```python
from fastshell import FastShell

# Create the application
app = FastShell("HelloApp", "A simple greeting application")

@app.command()
def hello(name: str = "World"):
    """Say hello to someone"""
    return f"Hello, {name}!"

@app.command()
def goodbye(name: str):
    """Say goodbye to someone"""
    return f"Goodbye, {name}!"

if __name__ == "__main__":
    app.run()
```

## Running Your Application

### Interactive Mode

Run without arguments to start interactive mode:

```bash
python hello.py
```

This starts an interactive shell:

```
Welcome to HelloApp
A simple greeting application
Type 'exit' or 'quit' to exit, 'help' for help.
System commands are enabled with persistent context.
[C:\path\to\directory] HelloApp> hello --name Alice
Hello, Alice!
[C:\path\to\directory] HelloApp> goodbye Bob
Goodbye, Bob!
[C:\path\to\directory] HelloApp> help
...
[C:\path\to\directory] HelloApp> exit
Goodbye!
```

### CLI Mode

Run with arguments for one-time command execution:

```bash
python hello.py hello --name Alice
# Output: Hello, Alice!

python hello.py goodbye Bob
# Output: Goodbye, Bob!
```

## Key Features Demonstrated

### 1. Automatic Argument Parsing

FastShell automatically converts function parameters to command arguments:

```python
@app.command()
def create_user(name: str, age: int = 25, active: bool = True):
    """Create a new user"""
    return f"User: {name}, Age: {age}, Active: {active}"
```

Can be called as:

```bash
# Positional arguments
create_user "John Doe" 30 false

# Flag arguments
create_user --name "John Doe" --age 30 --active false

# Mixed style
create_user "John Doe" --age 30
```

### 2. Interactive Features

- **Tab completion**: Press Tab to complete commands and arguments
- **Command history**: Use up/down arrows to navigate previous commands
- **Syntax highlighting**: Commands, arguments, and values are color-coded
- **Built-in help**: Use `help` or `help <command>` for documentation

### 3. System Command Integration

When `allow_system_commands=True` (default), you can run system commands:

```bash
[C:\path\to\directory] HelloApp> dir
[C:\path\to\directory] HelloApp> cd path/to/directory
[C:\path\to\directory] HelloApp> python --version
[C:\path\to\directory] HelloApp> git status
```

## Next Steps

### Using Pydantic Models

For more complex commands, use Pydantic models:

```python
from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port", ge=1, le=65535)
    debug: bool = Field(default=False, description="Enable debug mode")
    workers: int = Field(default=1, description="Number of workers", ge=1)

@app.command()
def start_server(config: ServerConfig):
    """Start the development server"""
    return f"Starting server on {config.host}:{config.port} with {config.workers} workers (debug={config.debug})"
```

### Creating Subcommands

Organize related commands into groups:

```python
# Create a subinstance for database operations
db = app.subinstance("db", "Database management commands")

@db.command()
def migrate():
    """Run database migrations"""
    return "Migrations completed"

@db.command()
def seed():
    """Seed database with test data"""
    return "Database seeded"

# Usage: db migrate, db seed
```

### Async Commands

For I/O operations, use async commands:

```python
import asyncio
import httpx

@app.command()
async def fetch_weather(city: str):
    """Fetch weather data for a city"""
    async with httpx.AsyncClient() as client:
        # Simulate API call
        await asyncio.sleep(1)
        return f"Weather in {city}: Sunny, 22°C"
```

## Common Patterns

### Configuration Management

```python
import os
from pathlib import Path

class AppConfig(BaseModel):
    config_file: Path = Field(default=Path.home() / ".myapp" / "config.json")
    verbose: bool = Field(default=False)
    api_key: str = Field(default_factory=lambda: os.getenv("API_KEY", ""))

@app.command()
def configure(config: AppConfig):
    """Configure the application"""
    config.config_file.parent.mkdir(parents=True, exist_ok=True)
    return f"Configuration saved to {config.config_file}"
```

### Error Handling

```python
@app.command()
def risky_operation(file_path: str):
    """Perform a risky file operation"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return f"File has {len(content)} characters"
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found"
    except PermissionError:
        return f"Error: Permission denied accessing '{file_path}'"
```

### Output Formatting

```python
import json

@app.command()
def list_data(format: str = "table"):
    """List data in different formats"""
    data = [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"}
    ]

    if format == "json":
        return json.dumps(data, indent=2)
    elif format == "table":
        # Simple table format
        lines = ["ID | Name  | Email"]
        lines.append("-" * 30)
        for item in data:
            lines.append(f"{item['id']:2} | {item['name']:5} | {item['email']}")
        return "\n".join(lines)
    else:
        return "Unsupported format. Use 'json' or 'table'"
```

## Tips for Development

1. **Start Simple**: Begin with basic commands and add complexity gradually
2. **Use Type Hints**: They enable automatic argument parsing and validation
3. **Add Docstrings**: They become command descriptions in help text
4. **Test Both Modes**: Ensure commands work in both CLI and interactive modes
5. **Handle Errors**: Provide meaningful error messages for better user experience
6. **Use Pydantic**: For complex validation and automatic documentation

## Troubleshooting

### Common Issues

**Command not found in interactive mode:**

- Make sure you're using the exact command name
- Use `help` to see available commands
- Check if it's a system command vs. FastShell command

**Argument parsing errors:**

- Check parameter types match your input
- Use quotes for strings with spaces
- Boolean flags don't need values: `--debug` (not `--debug true`)

**Import errors:**

- Ensure all dependencies are installed
- Check Python version compatibility (3.7+)

### Getting Help

- Use `help` in interactive mode for general help
- Use `help <command>` for specific command help
- Check the API documentation for advanced features
- Look at example applications for patterns

## What's Next?

- Read the [API Documentation](API_DOCUMENTATION.md) for complete reference
- Explore [Advanced Examples](EXAMPLES.md) for complex use cases
- Check out the [Best Practices Guide](BEST_PRACTICES.md) for production tips

Happy coding with FastShell! 🚀
