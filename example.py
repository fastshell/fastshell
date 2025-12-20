#!/usr/bin/env python3
"""
Example FastShell application demonstrating the framework usage
"""

from fastshell import FastShell
from pydantic import BaseModel, Field
from time import sleep
import asyncio


# Create the main app
app = FastShell(
    name="Demo App",
    description="A test application demonstrating FastShell framework"
)


# Approach A: Using Pydantic models
class Arguments(BaseModel):
    first_name: str = Field(..., description="First name of the person")
    last_name: str = Field('', description="Last name of the person")
    age: int = Field(18, description="Age of the person")


@app.command(name='hello', root=True)
def hello(args: Arguments):
    """Greet a person with their name and age"""
    app.print(f'Hello, {args.first_name} {args.last_name}. Your age is {args.age}')


# Approach B: Simple function parameters
@app.command('echo')
def echo(text: str):
    """Echo the provided text"""
    return text


@app.command('add')
def add_numbers(a: int, b: int):
    """Add two numbers together"""
    return f"{a} + {b} = {a + b}"


# Async command example
@app.command('async-hello')
async def async_hello(name: str = "World"):
    """Async greeting command"""
    await asyncio.sleep(0.1)  # Simulate async work
    return f"Hello, {name}! (async)"


# Subinstance example
sleep_cmd = app.subinstance('sleep', description="Sleeping")


@sleep_cmd.command('hrs')
def sleep_hrs(hrs: int):
    """Sleep for specified hours"""
    sleep_cmd.print('Started sleep!')
    sleep(hrs * 1)  # Use seconds instead of hours for demo
    return 'Sleep finished!'


@sleep_cmd.command('mins')
def sleep_mins(mins: int):
    """Sleep for specified minutes"""
    sleep_cmd.print(f'Sleeping for {mins} minutes...')
    sleep(mins * 1)  # Use seconds instead of minutes for demo
    return 'Sleep finished!'


# File operations subinstance
file_ops = app.subinstance('file')


class FileArgs(BaseModel):
    path: str = Field(..., description="File path")
    content: str = Field("", description="File content")
    append: bool = Field(False, description="Append to file instead of overwriting")


@file_ops.command('write')
def write_file(args: FileArgs):
    """Write content to a file"""
    mode = 'a' if args.append else 'w'
    try:
        with open(args.path, mode) as f:
            f.write(args.content)
        return f"Content written to {args.path}"
    except Exception as e:
        return f"Error writing file: {e}"


@file_ops.command('read')
def read_file(path: str):
    """Read content from a file"""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        command_line = " ".join(sys.argv[1:])
        asyncio.run(app.execute_command(command_line))
    else:
        # Interactive mode
        app.run()