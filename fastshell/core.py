import asyncio
import inspect
import shlex
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .parser import ArgumentParser
from .completer import FastShellCompleter
from .lexer import FastShellLexer
from .exceptions import MultiplePossibleMatchError


class CommandInfo:
    def __init__(self, func: Callable, name: str, root: bool = False, model: Optional[Type[BaseModel]] = None):
        self.func = func
        self.name = name
        self.root = root
        self.model = model
        self.is_async = asyncio.iscoroutinefunction(func)
        self.doc = inspect.getdoc(func) or ""


class FastShell:
    def __init__(self, name: str = "FastShell", description: str = "", allow_system_commands: bool = True):
        self.name = name
        self.description = description
        self.allow_system_commands = allow_system_commands
        self.commands: Dict[str, CommandInfo] = {}
        self.subinstances: Dict[str, 'FastShell'] = {}
        self.parent: Optional['FastShell'] = None
        self.parser = ArgumentParser()
        
        # Setup prompt toolkit components
        self.history = InMemoryHistory()
        self.completer = FastShellCompleter(self)
        self.lexer = FastShellLexer(self)
        self.style = Style.from_dict({
            'command': '#ansiblue bold',
            'argument': '#ansigreen',
            'string': '#ansiyellow',
            'number': '#ansimagenta',
            'text': '#ansiwhite',
        })
        
    def set_interactive_mode(self, interactive: bool):
        """Set whether the shell is in interactive mode"""
        self.completer.interactive_mode = interactive
    
    def command(self, name: Optional[str] = None, root: bool = False):
        """Decorator to register a command"""
        def decorator(func: Callable):
            cmd_name = name or func.__name__
            
            # Extract model from function signature
            sig = inspect.signature(func)
            model = None
            
            for param_name, param in sig.parameters.items():
                if param.annotation and issubclass(param.annotation, BaseModel):
                    model = param.annotation
                    break
            
            # If no model found, create one from function parameters
            if not model:
                model = self._create_model_from_signature(func)
            
            cmd_info = CommandInfo(func, cmd_name, root, model)
            self.commands[cmd_name] = cmd_info
            return func
        return decorator
    
    def subinstance(self, name: str, description: str = "") -> 'FastShell':
        """Create a subinstance (subcommand group)"""
        if name not in self.subinstances:
            # Subinstances should not have system commands or exit functionality
            sub = FastShell(name, description=description, allow_system_commands=False)
            sub.parent = self
            self.subinstances[name] = sub
        return self.subinstances[name]
    
    def print(self, text: Any):
        """Safe print method that handles various data types"""
        if isinstance(text, (list, dict)):
            import json
            print(json.dumps(text, indent=2, ensure_ascii=False))
        else:
            print(str(text))
    
    def _create_model_from_signature(self, func: Callable) -> Type[BaseModel]:
        """Create a Pydantic model from function signature"""
        sig = inspect.signature(func)
        annotations = {}
        defaults = {}
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            annotation = param.annotation if param.annotation != inspect.Parameter.empty else str
            annotations[param_name] = annotation
            
            if param.default != inspect.Parameter.empty:
                defaults[param_name] = param.default
        
        # Create the model class dynamically
        model_name = f"{func.__name__}Args"
        
        # Create class attributes
        class_attrs = {'__annotations__': annotations}
        class_attrs.update(defaults)
        
        model_class = type(model_name, (BaseModel,), class_attrs)
        
        return model_class
    
    async def execute_command(self, command_line: str, interactive_mode: bool = False) -> Any:
        """Execute a command from command line string"""
        if not command_line.strip():
            return
            
        try:
            tokens = shlex.split(command_line)
        except ValueError as e:
            self.print(f"Error parsing command: {e}")
            return
        
        if not tokens:
            return
        
        # Check for subinstance
        if tokens[0] in self.subinstances:
            sub_command = " ".join(tokens[1:])
            return await self.subinstances[tokens[0]].execute_command(sub_command, interactive_mode)
        
        # Check for built-in commands
        command_name = tokens[0]
        if command_name.lower() == 'help':
            # Help command can take an optional command name as argument
            if len(tokens) > 1:
                # Handle nested help commands (e.g., "help aws ec2 instances create")
                self._handle_nested_help(tokens[1:])
            else:
                self._show_help()
            return
        elif command_name.lower() == 'exec':
            # Exec command to force system command execution (only in main shell)
            if self.parent:
                self.print("Exec command is not available in subinstances.")
                return
            if not self.allow_system_commands:
                self.print("System commands are not allowed in this shell.")
                return
            if len(tokens) < 2:
                self.print("Usage: exec <system_command> [args...]")
                return
            
            # Execute the system command with remaining tokens
            system_tokens = tokens[1:]
            return await self._execute_system_command(system_tokens)
        elif command_name.lower() in ['exit', 'quit']:
            if not self.parent:
                # For main shell, we can't actually exit from execute_command
                # This is handled in run_interactive
                self.print("Use Ctrl+C or the interactive shell to exit.")
            else:
                self.print("Exit commands are not available in subinstances.")
            return
        
        # Check for registered command
        if command_name in self.commands:
            return await self._execute_registered_command(command_name, tokens[1:])
        
        # In CLI mode, check for root commands after direct commands
        if not interactive_mode:
            # Check for root commands (only in CLI mode)
            for cmd_name, cmd_info in self.commands.items():
                if cmd_info.root:
                    return await self._execute_registered_command(cmd_name, tokens)
        
        # Try system command if allowed (only in interactive mode)
        if self.allow_system_commands and interactive_mode:
            return await self._execute_system_command(tokens)
        
        self.print(f"Command not found: {command_name}")
    
    def _print_validation_error(self, error: ValidationError, command_name: str, args: list[str]):
        """Print user-friendly validation error messages"""
        self.print(f"Error in command '{command_name}':")
        
        for err in error.errors():
            field_name = err['loc'][0] if err['loc'] else 'unknown'
            error_type = err['type']
            input_value = err['input']
            
            # Convert field name back to display format
            display_field = field_name.replace('_', '-')
            
            # Handle specific error types with clearer messages
            if error_type == 'int_parsing':
                if input_value == 'true':
                    self.print(f"  --{display_field}: Missing value. This flag requires an integer value.")
                    self.print(f"  Example: --{display_field} 25")
                else:
                    self.print(f"  --{display_field}: '{input_value}' is not a valid integer.")
                    self.print(f"  Example: --{display_field} 25")
            
            elif error_type == 'float_parsing':
                if input_value == 'true':
                    self.print(f"  --{display_field}: Missing value. This flag requires a decimal number.")
                    self.print(f"  Example: --{display_field} 3.14")
                else:
                    self.print(f"  --{display_field}: '{input_value}' is not a valid decimal number.")
                    self.print(f"  Example: --{display_field} 3.14")
            
            elif error_type == 'bool_parsing':
                if input_value == 'true':
                    # This is actually correct for boolean flags
                    continue
                else:
                    self.print(f"  --{display_field}: '{input_value}' is not a valid boolean value.")
                    self.print(f"  Use: --{display_field} (for true) or omit the flag (for false)")
            
            elif error_type == 'missing':
                self.print(f"  {display_field}: This argument is required.")
                # Try to suggest the correct usage
                cmd_info = self.commands.get(command_name)
                if cmd_info and cmd_info.model:
                    field_info = cmd_info.model.model_fields.get(field_name)
                    if field_info:
                        type_name = getattr(field_info.annotation, '__name__', 'value')
                        self.print(f"  Provide it as: {display_field} <{type_name}> or --{display_field} <{type_name}>")
            
            elif error_type == 'string_type':
                self.print(f"  --{display_field}: Expected text value, got {type(input_value).__name__}.")
            
            else:
                # Generic error message for other types
                msg = err.get('msg', 'Invalid value')
                self.print(f"  --{display_field}: {msg}")
                if input_value == 'true':
                    self.print(f"  This flag appears to be missing its value.")
        
        # Provide general help
        self.print(f"\nUse 'help {command_name}' for detailed usage information.")

    async def _execute_registered_command(self, command_name: str, args: List[str]) -> Any:
        """Execute a registered command"""
        cmd_info = self.commands[command_name]
        
        try:
            # Parse arguments using the command's model
            parsed_args = self.parser.parse_args(args, cmd_info.model)
            
            # Check if function expects a model or individual parameters
            sig = inspect.signature(cmd_info.func)
            params = list(sig.parameters.values())
            
            # Filter out 'self' parameter
            params = [p for p in params if p.name != 'self']
            
            if (len(params) == 1 and 
                params[0].annotation != inspect.Parameter.empty and 
                hasattr(params[0].annotation, '__bases__') and
                BaseModel in params[0].annotation.__bases__):
                # Function expects a model
                if cmd_info.is_async:
                    result = await cmd_info.func(parsed_args)
                else:
                    result = cmd_info.func(parsed_args)
            else:
                # Function expects individual parameters
                kwargs = parsed_args.model_dump()
                if cmd_info.is_async:
                    result = await cmd_info.func(**kwargs)
                else:
                    result = cmd_info.func(**kwargs)
            
            # Handle return value
            if result is not None:
                self.print(result)
            
            return result
            
        except ValidationError as e:
            self._print_validation_error(e, command_name, args)
        except MultiplePossibleMatchError as e:
            self.print(f"Ambiguous arguments: {e}")
        except Exception as e:
            self.print(f"Error executing command: {e}")
    
    async def _execute_system_command(self, tokens: List[str]) -> Any:
        """Execute a system command with interactive support"""
        try:
            import platform
            
            # On Windows, we need to use cmd.exe for built-in commands
            if platform.system() == "Windows":
                # Use cmd.exe to execute the command
                cmd_args = ["cmd", "/c"] + tokens
            else:
                # On Unix-like systems, use sh
                cmd_args = ["sh", "-c", " ".join(tokens)]
            
            # For interactive mode, allow stdin/stdout passthrough
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=None,  # Use current stdin
                stdout=None,  # Use current stdout
                stderr=None   # Use current stderr
            )
            
            # Wait for the process to complete
            returncode = await process.wait()
            return returncode
            
        except FileNotFoundError:
            self.print(f"Command not found: {tokens[0]}")
            return 1
        except Exception as e:
            self.print(f"Error executing system command: {e}")
            return 1
    
    async def run_interactive(self):
        """Run the interactive shell"""
        # Set interactive mode for completer
        self.set_interactive_mode(True)
        
        session = PromptSession(
            history=self.history,
            completer=self.completer,
            lexer=self.lexer,
            style=self.style,
            auto_suggest=AutoSuggestFromHistory(),
        )
        
        self.print(f"Welcome to {self.name}")
        if self.description:
            self.print(self.description)
        
        # Only show exit instructions for main shell, not subinstances
        if not self.parent:
            self.print("Type 'exit' or 'quit' to exit, 'help' for help.")
        else:
            self.print("Type 'help' for help.")
        
        while True:
            try:
                prompt_text = f"{self.name}> "
                if self.parent:
                    prompt_text = f"{self.parent.name}:{self.name}> "
                
                command_line = await session.prompt_async(prompt_text)
                
                # Only allow exit/quit for main shell, not subinstances
                if command_line.strip().lower() in ['exit', 'quit']:
                    if not self.parent:
                        break
                    else:
                        self.print("Exit commands are not available in subinstances. Use Ctrl+C to return to main shell.")
                else:
                    # Use execute_command for all other commands, including help
                    await self.execute_command(command_line, interactive_mode=True)
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
        
        self.print("Goodbye!")
    
    def _show_help(self):
        """Show help information"""
        self.print(f"\n{self.name} - {self.description}\n")
        
        # Show built-in commands first
        builtin_commands = [
            ("help", "Show help information"),
        ]
        
        # Add exit/quit commands for main shell only
        if not self.parent:
            builtin_commands.extend([
                ("exit", "Exit the shell"),
                ("quit", "Exit the shell"),
            ])
            
            # Add exec command if system commands are allowed
            if self.allow_system_commands:
                builtin_commands.append(("exec", "Force execution of system commands"))
        
        if builtin_commands:
            self.print("Built-in commands:")
            for name, desc in builtin_commands:
                self.print(f"  {name} - {desc}")
        
        if self.commands:
            self.print("\nAvailable commands:")
            for name, cmd_info in self.commands.items():
                root_indicator = " (root)" if cmd_info.root else ""
                self.print(f"  {name}{root_indicator} - {cmd_info.doc}")
        
        if self.subinstances:
            self.print("\nSubcommands:")
            for name, sub in self.subinstances.items():
                self.print(f"  {name} - {sub.description}")
        
        if self.allow_system_commands:
            self.print("\nSystem commands are also available.")
        
        self.print("\nUse 'help <command>' for detailed information about a specific command.")
    
    def _handle_nested_help(self, tokens: list):
        """Handle nested help commands (e.g., help aws ec2 instances create)"""
        if not tokens:
            self._show_help()
            return
        
        # Navigate through the nested structure
        current_shell = self
        path = []
        
        # Navigate as deep as possible through subinstances
        for i, token in enumerate(tokens):
            if token in current_shell.subinstances:
                current_shell = current_shell.subinstances[token]
                path.append(token)
            else:
                # This token is not a subinstance, it might be a command
                remaining_tokens = tokens[i:]
                if len(remaining_tokens) == 1:
                    cmd_name = remaining_tokens[0]
                    
                    # Check if it's a registered command
                    if cmd_name in current_shell.commands:
                        cmd_info = current_shell.commands[cmd_name]
                        
                        # Generate the full command path for display
                        full_path = " ".join(path + [cmd_name])
                        self.print(f"\n{full_path}")
                        self.print("=" * len(full_path))
                        current_shell._generate_command_manual(cmd_name, cmd_info)
                        return
                    
                    # Check if it's a built-in command (only for main shell)
                    elif cmd_name.lower() in ['help', 'exit', 'quit'] or (cmd_name.lower() == 'exec' and not current_shell.parent):
                        current_shell._show_builtin_help(cmd_name.lower())
                        return
                    
                    # Special case for exec in subinstance
                    elif cmd_name.lower() == 'exec' and current_shell.parent:
                        self.print("Exec command is not available in subinstances.")
                        return
                
                # Command not found
                if remaining_tokens:
                    path_str = " ".join(path) if path else "root"
                    self.print(f"Command '{remaining_tokens[0]}' not found in subcommand '{path_str}'.")
                    if path:
                        self.print(f"Use 'help {' '.join(path)}' to see available commands.")
                    else:
                        self.print("Use 'help' to see available commands.")
                else:
                    # Show help for the current subinstance
                    current_shell._show_help()
                return
        
        # If we've navigated through all tokens and they were all subinstances,
        # show help for the final subinstance
        current_shell._show_help()
    
    def _show_command_help(self, command_name: str):
        """Show detailed help for a specific command"""
        # Check if it's a subinstance
        if command_name in self.subinstances:
            sub = self.subinstances[command_name]
            self.print(f"\n{command_name} - {sub.description}")
            self.print("=" * (len(command_name) + len(sub.description) + 3))
            self.print("")
            
            if sub.commands:
                self.print("Available commands:")
                for name, cmd_info in sub.commands.items():
                    self.print(f"  {name} - {cmd_info.doc}")
                self.print("")
                self.print(f"Use '{command_name} <command>' to execute subcommands.")
                self.print(f"Use 'help {command_name} <command>' for detailed command information.")
            else:
                self.print("No commands available in this subcommand.")
            return
        
        # Check if it's a registered command
        if command_name in self.commands:
            cmd_info = self.commands[command_name]
            self._generate_command_manual(command_name, cmd_info)
            return
        
        # Check if it's a built-in command
        if command_name.lower() in ['help', 'exit', 'quit']:
            self._show_builtin_help(command_name.lower())
            return
        
        # Command not found
        self.print(f"Command '{command_name}' not found.")
        self.print("Use 'help' to see all available commands.")
    
    def _generate_command_manual(self, command_name: str, cmd_info):
        """Generate detailed manual page for a command"""
        self.print(f"\n{command_name.upper()}")
        self.print("=" * len(command_name))
        self.print("")
        
        # Command description
        if cmd_info.doc:
            self.print("DESCRIPTION")
            self.print(f"    {cmd_info.doc}")
            self.print("")
        
        # Usage syntax
        self.print("USAGE")
        if cmd_info.model:
            usage_parts = [command_name]
            
            # Get field information
            fields = cmd_info.model.model_fields
            required_fields = []
            optional_fields = []
            
            for field_name, field_info in fields.items():
                is_required = field_info.is_required()
                field_display = field_name.replace('_', '-')
                
                if is_required:
                    required_fields.append(f"<{field_display}>")
                else:
                    default_val = field_info.default
                    if default_val is not None and default_val != "":
                        optional_fields.append(f"[--{field_display}={default_val}]")
                    else:
                        optional_fields.append(f"[--{field_display}=<value>]")
            
            # Build usage string
            usage_parts.extend(required_fields)
            usage_parts.extend(optional_fields)
            
            self.print(f"    {' '.join(usage_parts)}")
            self.print("")
            
            # Arguments section
            if fields:
                self.print("ARGUMENTS")
                
                # Required arguments
                if required_fields:
                    self.print("  Required:")
                    for field_name, field_info in fields.items():
                        if field_info.is_required():
                            field_display = field_name.replace('_', '-')
                            type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                            description = getattr(field_info, 'description', '') or f"{field_name} value"
                            self.print(f"    <{field_display}>")
                            self.print(f"        Type: {type_name}")
                            self.print(f"        Description: {description}")
                            self.print("")
                
                # Optional arguments
                optional_count = sum(1 for f in fields.values() if not f.is_required())
                if optional_count > 0:
                    self.print("  Optional:")
                    for field_name, field_info in fields.items():
                        if not field_info.is_required():
                            field_display = field_name.replace('_', '-')
                            type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                            description = getattr(field_info, 'description', '') or f"{field_name} value"
                            default_val = field_info.default
                            
                            self.print(f"    --{field_display}")
                            self.print(f"        Type: {type_name}")
                            self.print(f"        Description: {description}")
                            if default_val is not None:
                                self.print(f"        Default: {default_val}")
                            self.print("")
        else:
            self.print(f"    {command_name}")
            self.print("")
        
        # Examples section
        self.print("EXAMPLES")
        if cmd_info.model and cmd_info.model.model_fields:
            fields = cmd_info.model.model_fields
            
            # Example 1: Using positional arguments
            required_fields = [name for name, field in fields.items() if field.is_required()]
            if required_fields:
                example_values = []
                for field_name in required_fields:
                    field_info = fields[field_name]
                    type_name = getattr(field_info.annotation, '__name__', 'str')
                    if type_name == 'str':
                        example_values.append(f'"{field_name}_example"')
                    elif type_name == 'int':
                        example_values.append('42')
                    elif type_name == 'float':
                        example_values.append('3.14')
                    elif type_name == 'bool':
                        example_values.append('true')
                    else:
                        example_values.append(f'<{field_name}>')
                
                self.print(f"    {command_name} {' '.join(example_values)}")
            
            # Example 2: Using flag arguments
            if fields:
                flag_parts = [command_name]
                for field_name, field_info in fields.items():
                    field_display = field_name.replace('_', '-')
                    type_name = getattr(field_info.annotation, '__name__', 'str')
                    
                    if type_name == 'str':
                        flag_parts.append(f'--{field_display} "example"')
                    elif type_name == 'int':
                        flag_parts.append(f'--{field_display} 42')
                    elif type_name == 'float':
                        flag_parts.append(f'--{field_display} 3.14')
                    elif type_name == 'bool':
                        flag_parts.append(f'--{field_display}')
                    else:
                        flag_parts.append(f'--{field_display} <value>')
                
                self.print(f"    {' '.join(flag_parts)}")
        else:
            self.print(f"    {command_name}")
        
        self.print("")
    
    def _show_builtin_help(self, command_name: str):
        """Show help for built-in commands"""
        builtin_help = {
            'help': {
                'description': 'Display help information',
                'usage': 'help [command]',
                'examples': [
                    'help                 # Show general help',
                    'help <command>       # Show detailed help for a command',
                    'help <subcommand>    # Show help for a subcommand'
                ]
            },
            'exec': {
                'description': 'Force execution of system commands',
                'usage': 'exec <system_command> [args...]',
                'examples': [
                    'exec ls -la          # Force execute ls command',
                    'exec python --version # Force execute python command',
                    'exec echo "hello"    # Force execute echo command'
                ]
            },
            'exit': {
                'description': 'Exit the shell',
                'usage': 'exit',
                'examples': ['exit']
            },
            'quit': {
                'description': 'Exit the shell (alias for exit)',
                'usage': 'quit', 
                'examples': ['quit']
            }
        }
        
        if command_name in builtin_help:
            info = builtin_help[command_name]
            self.print(f"\n{command_name.upper()}")
            self.print("=" * len(command_name))
            self.print("")
            self.print("DESCRIPTION")
            self.print(f"    {info['description']}")
            self.print("")
            self.print("USAGE")
            self.print(f"    {info['usage']}")
            self.print("")
            self.print("EXAMPLES")
            for example in info['examples']:
                self.print(f"    {example}")
            self.print("")
    
    def run(self, args: Optional[List[str]] = None):
        """Run the shell - CLI mode if args provided, interactive mode otherwise"""
        import sys
        
        # If no args provided, use sys.argv
        if args is None:
            args = sys.argv[1:]  # Skip script name
        
        if args:
            # CLI mode - execute single command and exit
            asyncio.run(self._run_cli_mode(args))
        else:
            # Interactive mode - start interactive shell
            asyncio.run(self.run_interactive())
    
    async def _run_cli_mode(self, args: List[str]):
        """Run in CLI mode - execute single command without interactive features"""
        # Set non-interactive mode
        self.set_interactive_mode(False)
        
        # Join args back into command line
        command_line = " ".join(args)
        
        # Execute the command
        await self.execute_command(command_line, interactive_mode=False)