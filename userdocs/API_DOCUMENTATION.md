# FastShell API Documentation

FastShell is a FastAPI-like interactive shell framework that allows you to build command-line applications with decorator-based command registration, automatic argument parsing, and rich interactive features.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Decorators](#decorators)
- [Command Registration](#command-registration)
- [Argument Parsing](#argument-parsing)
- [Interactive Features](#interactive-features)
- [System Commands](#system-commands)
- [Subinstances](#subinstances)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Quick Start

```python
from fastshell import FastShell
from pydantic import BaseModel

# Create a shell application
app = FastShell("MyApp", description="My awesome CLI application")

# Define a command with Pydantic model
class UserArgs(BaseModel):
    name: str
    age: int = 25
    active: bool = True

@app.command()
def create_user(args: UserArgs):
    """Create a new user"""
    return f"Created user {args.name}, age {args.age}, active: {args.active}"

# Run the application
if __name__ == "__main__":
    app.run()
```

## Core Classes

### FastShell

The main application class that manages commands, subinstances, and interactive features.

#### Constructor

```python
FastShell(
    name: str = "FastShell",
    description: str = "",
    allow_system_commands: bool = True
)
```

**Parameters:**

- `name`: Application name displayed in prompts and help
- `description`: Application description shown in help
- `allow_system_commands`: Enable system command execution

#### Methods

##### `command(name: Optional[str] = None, root: bool = False)`

Decorator to register a command function.

**Parameters:**

- `name`: Command name (defaults to function name)
- `root`: Whether command can be called without explicit name in CLI mode

**Returns:** Decorator function

##### `subinstance(name: str, description: str = "") -> FastShell`

Create a subcommand group (nested commands).

**Parameters:**

- `name`: Subinstance name
- `description`: Subinstance description

**Returns:** New FastShell instance for the subcommand group

##### `run(args: Optional[List[str]] = None)`

Run the application in CLI or interactive mode.

**Parameters:**

- `args`: Command line arguments (if None, uses sys.argv)

**Behavior:**

- If args provided: CLI mode (execute once and exit)
- If no args: Interactive mode (start shell session)

##### `run_interactive()`

Start interactive shell session (async method).

##### `execute_command(command_line: str, interactive_mode: bool = False)`

Execute a command from string (async method).

**Parameters:**

- `command_line`: Command string to execute
- `interactive_mode`: Whether running in interactive mode

##### `print(text: Any)`

Safe print method that handles various data types including JSON serialization.

### CommandInfo

Internal class storing command metadata.

**Attributes:**

- `func`: Command function
- `name`: Command name
- `root`: Whether it's a root command
- `model`: Pydantic model for arguments
- `is_async`: Whether function is async
- `doc`: Function docstring

## Decorators

### @app.command()

Register a function as a command.

```python
# Basic command
@app.command()
def hello():
    """Say hello"""
    return "Hello, World!"

# Command with custom name
@app.command("greet")
def greeting():
    """Greet the user"""
    return "Greetings!"

# Root command (can be called without name in CLI mode)
@app.command(root=True)
def default_action():
    """Default action when no command specified"""
    return "Default action executed"
```

## Command Registration

### Using Pydantic Models

```python
from pydantic import BaseModel, Field

class ServerArgs(BaseModel):
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")

@app.command()
def start_server(args: ServerArgs):
    """Start the development server"""
    return f"Starting server on {args.host}:{args.port} (debug={args.debug})"
```

### Using Function Parameters

```python
@app.command()
def deploy(environment: str, version: str = "latest", force: bool = False):
    """Deploy application to environment"""
    return f"Deploying {version} to {environment} (force={force})"
```

### Async Commands

```python
import asyncio

@app.command()
async def fetch_data(url: str, timeout: int = 30):
    """Fetch data from URL"""
    # Simulate async operation
    await asyncio.sleep(1)
    return f"Fetched data from {url} with timeout {timeout}s"
```

## Argument Parsing

FastShell supports multiple argument input styles:

### Positional Arguments

```bash
# Function: create_user(name: str, age: int = 25)
create_user "John Doe" 30
```

### Flag Arguments

```bash
# Same function
create_user --name "John Doe" --age 30
```

### Mixed Style

```bash
# Positional + flags
create_user "John Doe" --age 30
```

### Boolean Flags

```bash
# For boolean parameters
deploy production --force        # force=True
deploy production               # force=False (default)
```

### Argument Types

FastShell automatically handles type conversion for:

- `str`: String values
- `int`: Integer values
- `float`: Floating point values
- `bool`: Boolean flags
- `List[T]`: Lists of values
- Custom Pydantic models

## Interactive Features

### Syntax Highlighting

Commands, arguments, strings, and numbers are highlighted with different colors:

- **Commands**: Light blue (`#66aaff`)
- **Arguments**: Light green (`#66dd66`)
- **Strings**: Light orange (`#ffcc66`)
- **Numbers**: Light purple (`#dd66dd`)
- **Text**: Light gray (`#cccccc`)

### Tab Completion

- Command name completion
- Argument name completion
- File path completion for system commands
- Context-aware suggestions

### Command History

- Previous commands are saved and accessible with up/down arrows
- Auto-suggestion from history

### Built-in Commands

- `help [command]`: Show help information
- `exit` / `quit`: Exit the shell (main shell only)
- `exec <command>`: Force system command execution

## System Commands

When `allow_system_commands=True`, FastShell provides:

### Persistent Shell Context

- Directory changes persist across commands
- Environment variables maintained
- Cross-platform support (Windows/Unix)

### Interactive Command Support

Commands like `python`, `vim`, `top` run with full keyboard interaction:

```bash
python          # Starts Python REPL with Ctrl+C support
vim file.txt    # Opens vim with full keyboard support
```

### System Command Examples

```bash
# Directory operations
cd /path/to/directory
ls -la
pwd

# File operations
cat file.txt
grep "pattern" *.py

# Development commands
git status
npm install
python script.py
```

## Subinstances

Create nested command structures:

```python
# Create main app
app = FastShell("CloudCLI", "Cloud management CLI")

# Create AWS subinstance
aws = app.subinstance("aws", "AWS services")
ec2 = aws.subinstance("ec2", "EC2 management")
s3 = aws.subinstance("s3", "S3 management")

# Add commands to subinstances
@ec2.command()
def list_instances(region: str = "us-east-1"):
    """List EC2 instances"""
    return f"Listing instances in {region}"

@s3.command()
def list_buckets():
    """List S3 buckets"""
    return "Listing S3 buckets"
```

Usage:

```bash
# Interactive mode
aws ec2 list-instances --region us-west-2
aws s3 list-buckets

# CLI mode
python app.py aws ec2 list-instances --region us-west-2
```

## Error Handling

### Validation Errors

FastShell provides clear error messages for invalid arguments:

```bash
$ create_user --age "not_a_number"
Error in command 'create_user':
  --age: 'not_a_number' is not a valid integer.
  Example: --age 25

Use 'help create_user' for detailed usage information.
```

### Missing Arguments

```bash
$ create_user
Error in command 'create_user':
  name: This argument is required.
  Provide it as: name <str> or --name <str>
```

### Custom Exception Handling

```python
from fastshell.exceptions import MultiplePossibleMatchError

@app.command()
def risky_operation():
    """Operation that might fail"""
    try:
        # Your code here
        pass
    except Exception as e:
        return f"Operation failed: {e}"
```

## Examples

### Basic CLI Application

```python
from fastshell import FastShell
from pydantic import BaseModel

app = FastShell("FileTool", "File management utility")

class CopyArgs(BaseModel):
    source: str
    destination: str
    recursive: bool = False

@app.command()
def copy(args: CopyArgs):
    """Copy files or directories"""
    mode = "recursively" if args.recursive else ""
    return f"Copying {args.source} to {args.destination} {mode}"

@app.command()
def list_files(path: str = ".", show_hidden: bool = False):
    """List files in directory"""
    hidden = "including hidden" if show_hidden else "excluding hidden"
    return f"Listing files in {path} ({hidden})"

if __name__ == "__main__":
    app.run()
```

### Complex Application with Subinstances

```python
from fastshell import FastShell
from pydantic import BaseModel
import asyncio

# Main application
app = FastShell("DevTools", "Development tools CLI")

# Database subinstance
db = app.subinstance("db", "Database operations")

class MigrationArgs(BaseModel):
    direction: str = "up"  # up or down
    steps: int = 1

@db.command()
async def migrate(args: MigrationArgs):
    """Run database migrations"""
    await asyncio.sleep(1)  # Simulate migration
    return f"Ran {args.steps} migration(s) {args.direction}"

@db.command()
def seed():
    """Seed database with test data"""
    return "Database seeded successfully"

# Docker subinstance
docker = app.subinstance("docker", "Docker operations")

@docker.command()
def build(tag: str, dockerfile: str = "Dockerfile"):
    """Build Docker image"""
    return f"Building image {tag} from {dockerfile}"

@docker.command()
def run(image: str, port: int = 8000, detached: bool = False):
    """Run Docker container"""
    mode = "detached" if detached else "interactive"
    return f"Running {image} on port {port} in {mode} mode"

if __name__ == "__main__":
    app.run()
```

Usage examples:

```bash
# Interactive mode
$ python devtools.py
DevTools> db migrate --direction up --steps 3
DevTools> docker build myapp --dockerfile Dockerfile.prod
DevTools> docker run myapp --port 3000 --detached

# CLI mode
$ python devtools.py db migrate --steps 2
$ python devtools.py docker build myapp
```

### Integration with External APIs

```python
import httpx
from fastshell import FastShell
from pydantic import BaseModel

app = FastShell("WeatherCLI", "Weather information CLI")

class WeatherArgs(BaseModel):
    city: str
    units: str = "metric"  # metric, imperial, kelvin

@app.command()
async def current(args: WeatherArgs):
    """Get current weather for a city"""
    async with httpx.AsyncClient() as client:
        # Simulate API call
        await asyncio.sleep(0.5)
        return f"Current weather in {args.city}: 22°C, Sunny ({args.units} units)"

@app.command()
async def forecast(city: str, days: int = 5):
    """Get weather forecast"""
    async with httpx.AsyncClient() as client:
        await asyncio.sleep(0.5)
        return f"{days}-day forecast for {city}: Mostly sunny"

if __name__ == "__main__":
    app.run()
```

## Best Practices

1. **Use Pydantic Models**: For complex commands with multiple parameters
2. **Provide Descriptions**: Add docstrings and field descriptions for better help
3. **Handle Errors Gracefully**: Use try-catch blocks for external operations
4. **Use Async When Needed**: For I/O operations, API calls, etc.
5. **Organize with Subinstances**: Group related commands logically
6. **Test Both Modes**: Ensure commands work in both CLI and interactive modes
7. **Validate Input**: Use Pydantic validators for complex validation rules

## Advanced Features

### Custom Validation

```python
from pydantic import BaseModel, validator

class ServerArgs(BaseModel):
    port: int
    host: str = "localhost"

    @validator('port')
    def port_must_be_valid(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
```

### Environment Integration

```python
import os
from pydantic import BaseModel, Field

class DatabaseArgs(BaseModel):
    url: str = Field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///app.db'))
    debug: bool = Field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
```

### Custom Output Formatting

```python
import json
from rich.console import Console
from rich.table import Table

console = Console()

@app.command()
def list_users():
    """List all users with rich formatting"""
    table = Table(title="Users")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Email", style="yellow")

    # Add sample data
    table.add_row("1", "John Doe", "john@example.com")
    table.add_row("2", "Jane Smith", "jane@example.com")

    console.print(table)
```

This completes the comprehensive API documentation for FastShell. The framework provides a powerful and flexible way to build command-line applications with modern Python features.
