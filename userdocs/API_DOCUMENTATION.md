<!--
 Copyright (c) 2026 github.com/fastshell

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# FastShell API Documentation

FastShell is a FastAPI-like framework for building interactive command-line applications with shell-like interfaces.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Classes](#core-classes)
- [Decorators](#decorators)
- [Command Definition](#command-definition)
- [Argument Parsing](#argument-parsing)
- [Interactive Features](#interactive-features)
- [System Commands](#system-commands)
- [Subcommands](#subcommands)
- [Quote Handling](#quote-handling)
- [Error Handling](#error-handling)
- [Advanced Features](#advanced-features)

## Installation

```bash
pip install fastshell
```

## Quick Start

```python
from fastshell import FastShell

app = FastShell("MyApp", description="A sample FastShell application")

@app.command()
def hello(name: str = "World", age: int = 18):
    """Greet someone with their age"""
    return f"Hello, {name}! You are {age} years old."

if __name__ == "__main__":
    app.run()
```

## Core Classes

### FastShell

The main application class that manages commands, subcommands, and the interactive shell.

```python
class FastShell:
    def __init__(
        self,
        name: str = "FastShell",
        description: str = "",
        allow_system_commands: bool = True,
    ):
        """
        Initialize a FastShell application.

        Args:
            name: Application name displayed in prompts
            description: Application description shown in help
            allow_system_commands: Whether to enable system command execution
        """
```

#### Methods

##### `command(name: Optional[str] = None, root: bool = False)`

Decorator to register a command function.

```python
@app.command()
def my_command(arg1: str, arg2: int = 10):
    """Command description"""
    return f"Result: {arg1}, {arg2}"

@app.command("custom-name")
def another_command():
    """Command with custom name"""
    pass

@app.command(root=True)
def root_command():
    """Root command (available in CLI mode without command name)"""
    pass
```

##### `subinstance(name: str, description: str = "") -> FastShell`

Create a subcommand group.

```python
# Create subcommand group
aws = app.subinstance("aws", "AWS CLI-like commands")

@aws.command()
def list_instances():
    """List EC2 instances"""
    pass

# Usage: myapp aws list-instances
```

##### `run(args: Optional[List[str]] = None)`

Run the application in CLI or interactive mode.

```python
# Interactive mode (no arguments)
app.run()

# CLI mode (with arguments)
app.run(["hello", "John", "--age", "25"])
```

##### `run_interactive()`

Start the interactive shell mode.

```python
await app.run_interactive()
```

##### `execute_command(command_line: str, interactive_mode: bool = False)`

Execute a command from a command line string.

```python
result = await app.execute_command("hello John --age 25")
```

## Decorators

### @command()

Register a function as a command. The function signature is automatically analyzed to create argument parsing.

```python
@app.command()
def process_data(
    input_file: str,                    # Required positional argument
    output_file: str = "output.txt",    # Optional with default
    verbose: bool = False,              # Boolean flag
    count: int = 1,                     # Integer argument
    ratio: float = 1.0,                 # Float argument
):
    """Process data from input file to output file"""
    pass
```

## Command Definition

### Function Signatures

FastShell automatically creates argument parsers from function signatures:

```python
@app.command()
def example(
    required_arg: str,              # <required_arg>
    optional_arg: str = "default",  # [--optional-arg=default]
    flag: bool = False,             # [--flag]
    number: int = 42,               # [--number=42]
    decimal: float = 3.14,          # [--decimal=3.14]
):
    """Example command with various argument types"""
    pass
```

### Pydantic Models

You can also use Pydantic models for more complex validation:

```python
from pydantic import BaseModel, Field

class UserData(BaseModel):
    name: str = Field(description="User's name")
    age: int = Field(ge=0, le=150, description="User's age")
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$', description="Valid email")

@app.command()
def create_user(data: UserData):
    """Create a new user"""
    return f"Created user: {data.name} ({data.email})"
```

### Async Commands

FastShell supports async command functions:

```python
@app.command()
async def fetch_data(url: str):
    """Fetch data from URL"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Argument Parsing

### Positional Arguments

Arguments can be provided positionally:

```bash
myapp hello John 25
```

### Flag Arguments

Arguments can be provided as flags:

```bash
myapp hello --name John --age 25
myapp hello -n John -a 25
```

### Mixed Usage

Positional and flag arguments can be mixed:

```bash
myapp hello John --age 25
```

### Boolean Flags

Boolean arguments work as flags:

```bash
myapp process-data input.txt --verbose
myapp process-data input.txt --verbose true
myapp process-data input.txt --verbose false
```

## Interactive Features

### Auto-completion

FastShell provides intelligent auto-completion:

- Command names
- Subcommand names
- Argument names (flags)
- File paths
- Argument values based on type

### Syntax Highlighting

Commands, arguments, strings, and numbers are highlighted with different colors.

### History

Command history is maintained across the session with up/down arrow navigation.

### Help System

Comprehensive help is available:

```bash
help                    # General help
help command-name       # Specific command help
help subcommand         # Subcommand help
help sub cmd            # Nested command help
```

## System Commands

When `allow_system_commands=True`, you can execute system commands directly:

```bash
MyApp> ls -la
MyApp> cd /path/to/directory
MyApp> python script.py
MyApp> exec echo "force system command"
```

### Persistent Context

System commands maintain persistent context:

- Current directory changes persist
- Environment variables persist
- Command history is maintained

### Interactive Commands

Interactive system commands (like `python`, `vim`, `nano`) work with full keyboard support including Ctrl+C handling.

## Subcommands

Create nested command structures:

```python
# Main app
app = FastShell("myapp")

# Create subcommand groups
aws = app.subinstance("aws", "AWS commands")
ec2 = aws.subinstance("ec2", "EC2 commands")

@ec2.command()
def list_instances():
    """List EC2 instances"""
    pass

@ec2.command()
def describe_instances(instance_id: str):
    """Describe specific instance"""
    pass

# Usage:
# myapp aws ec2 list-instances
# myapp aws ec2 describe-instances i-1234567890
```

## Quote Handling

FastShell handles quotes intelligently:

### Outer Quote Removal

Outer wrapping quotes are removed (standard shell behavior):

```bash
MyApp> hello "John"        # → Hello, John
MyApp> echo "Hello World"  # → Hello World
```

### Embedded Quote Preservation

Embedded quotes are preserved:

```bash
MyApp> hello H"embedded"W  # → Hello, H"embedded"W
MyApp> echo H"test"W       # → H"test"W
```

### Escaped Quotes

Escaped quotes are handled correctly:

```bash
MyApp> hello "H\"Bang\"W"  # → Hello, H"Bang"W
MyApp> echo H\"test\"W     # → H"test"W
```

## Error Handling

### Validation Errors

FastShell provides clear validation error messages:

```bash
MyApp> hello --age abc
Error in command 'hello':
  --age: 'abc' is not a valid integer.
  Example: --age 25

Use 'help hello' for detailed usage information.
```

### Missing Arguments

```bash
MyApp> process-data
Error in command 'process-data':
  input-file: This argument is required.
  Provide it as: input-file <str> or --input-file <str>
```

### Command Not Found

```bash
MyApp> unknown-command
Command not found: unknown-command
```

## Advanced Features

### Custom Prompt

The prompt shows current directory when system commands are enabled:

```bash
[/current/directory] MyApp>
```

### Keyboard Shortcuts

- `Tab`: Auto-completion
- `Ctrl+C`: Interrupt current command/return to prompt
- `Up/Down`: Command history navigation
- `Ctrl+D` or `EOF`: Exit shell

### CLI vs Interactive Mode

```python
# CLI mode - single command execution
app.run(["hello", "John"])

# Interactive mode - persistent shell
app.run()  # or app.run([])
```

### Root Commands

Root commands are available in CLI mode without specifying the command name:

```python
@app.command(root=True)
def main_action(file: str):
    """Main application action"""
    pass

# Usage in CLI mode:
# python myapp.py input.txt
# Instead of: python myapp.py main-action input.txt
```

### Custom Styling

Customize syntax highlighting colors:

```python
from prompt_toolkit.styles import Style

app = FastShell("MyApp")
app.style = Style.from_dict({
    'command': '#66aaff',
    'argument': '#66dd66',
    'string': '#ffcc66',
    'number': '#dd66dd',
    'text': '#cccccc',
})
```

### Error Recovery

FastShell gracefully handles:

- Ctrl+C interruptions
- Invalid input
- System command failures
- Network timeouts in async commands

## Best Practices

1. **Use descriptive docstrings** - They appear in help text
2. **Provide sensible defaults** - Makes commands easier to use
3. **Use type hints** - Enables automatic validation
4. **Group related commands** - Use subinstances for organization
5. **Handle errors gracefully** - Provide meaningful error messages
6. **Test both CLI and interactive modes** - Ensure consistent behavior

## Examples

See the `userdocs/EXAMPLES.md` file for comprehensive examples and use cases.
