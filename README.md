<!--
 Copyright (c) 2026 github.com/fastshell

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

![](./favicon.png)

# <center> FastShell </center>

A FastAPI-like framework for building interactive shell applications with fish-like features including autocompletion, syntax highlighting, and history-based suggestions.

## Features

- **FastAPI-like syntax** - Familiar decorator-based command registration
- **Pydantic integration** - Type-safe argument parsing with validation
- **Interactive shell** - Fish-like experience with autocompletion and syntax highlighting
- **System command context** - Persistent shell with directory tracking and environment preservation
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
    # Or you can put them directly in argument defintion.

# The root argument made it able to be called directly in CLI mode.
@app.command(name='hello', root=True)
def hello(args: Arguments):
    return f'Hello, {args.name}! You are {args.age} years old.'

if __name__ == "__main__":
    app.run()
```

### Command Usage Examples

The above command can be called in multiple ways:

#### In interactive mode

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

#### In CLI Mode

```bash
# Same with interactive, but
python3 ./main.py hello John
# This also works
python3 ./main.py John
```

## Installation

```bash
pip3 install fastshell==1.0.0a3
```

### Quick Start

```bash
fastshell
```

## Features in Detail

### Autocompletion

- Command name completion
- Argument flag completion with type information
- Context-aware suggestions

### System Command Context

- **Persistent Shell**: Maintains background shell session for context preservation
- **Directory Tracking**: Current directory displayed in prompt and preserved across commands
- **Environment Variables**: Shell environment changes persist between commands
- **Cross-Platform**: Works with cmd.exe on Windows and standard shells on Unix
- **Encoding Support**: Proper GBK encoding support for Chinese characters on Windows
- **Clean Output**: Intelligent filtering removes command echo and control information

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

### System Command Context Example

```bash
# Notice the current directory in the prompt
[/home/user/project] MyApp> pwd
/home/user/project

[/home/user/project] MyApp> cd /tmp
[/tmp] MyApp> echo "test" > file.txt
[/tmp] MyApp> cat file.txt
test

[/tmp] MyApp> cd ~/project
[/home/user/project] MyApp> ls
README.md  src/  tests/
```

## Development

### Using Poetry

```bash
# Install development dependencies
poetry install

# Activate virtualenv
poetry env activate

# Build package
poetry build
```

## Project Structure

```
fastshell/
├── fastshell/          # Core framework package
├── example.py          # Quick start example
└── README.md           # This file
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information.

## License

[MIT License](https://mit-license.org/)
