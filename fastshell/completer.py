from typing import Iterable, List
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
import shlex


class FastShellCompleter(Completer):
    """Autocompleter for FastShell commands and arguments"""
    
    def __init__(self, shell):
        self.shell = shell
        self.interactive_mode = True  # Default to interactive mode
    
    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Generate completions for the current input"""
        text = document.text_before_cursor
        
        try:
            tokens = shlex.split(text) if text else []
        except ValueError:
            # Handle incomplete quotes
            tokens = text.split()
        
        # If we're at the beginning or after whitespace with no tokens, complete commands
        if not tokens:
            yield from self._complete_commands("")
            return
        
        # If we have one token and cursor is not after whitespace, complete command names
        if len(tokens) == 1 and not text.endswith(' '):
            yield from self._complete_commands(tokens[0])
            return
        
        # If we have tokens and are after whitespace, or have multiple tokens, complete arguments
        if len(tokens) >= 1 and (text.endswith(' ') or len(tokens) > 1):
            # Check if first token is a valid command or subinstance
            command_name = tokens[0]
            
            # Check if it's a subinstance
            if command_name in self.shell.subinstances:
                yield from self._complete_arguments(tokens, text.endswith(' '))
                return
            
            # Check if it's a direct command
            if command_name in self.shell.commands:
                cmd_info = self.shell.commands[command_name]
                # In interactive mode, root commands still support completion with explicit command name
                # We don't skip completion here - root commands can still be called explicitly
                yield from self._complete_arguments(tokens, text.endswith(' '))
                return
            
            # Check if it's a root command (only in non-interactive mode)
            if not self.interactive_mode:
                for name, cmd_info in self.shell.commands.items():
                    if cmd_info.root:
                        # For root commands, all tokens are arguments
                        yield from self._complete_arguments(['root_command'] + tokens, text.endswith(' '))
                        return
        
        # Fallback to command completion (only if we're completing the first token)
        if len(tokens) == 1 and not text.endswith(' '):
            yield from self._complete_commands(tokens[-1] if tokens else "")
    
    def _complete_commands(self, prefix: str) -> Iterable[Completion]:
        """Complete command names and subinstances"""
        # Complete built-in commands first
        built_in_commands = [
            ("help", "Show help information"),
        ]
        
        # Only add exit/quit commands for main shell (not subinstances)
        if not self.shell.parent:
            built_in_commands.extend([
                ("exit", "Exit the shell"),
                ("quit", "Exit the shell"),
            ])
        
        for cmd_name, cmd_desc in built_in_commands:
            if cmd_name.startswith(prefix):
                yield Completion(
                    cmd_name,
                    start_position=-len(prefix),
                    display_meta=f"built-in - {cmd_desc}",
                    display=cmd_name,
                    style="class:command"
                )
        
        # Complete subinstances
        for name in self.shell.subinstances:
            if name.startswith(prefix):
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display_meta="subcommand",
                    style="class:command"
                )
        
        # Complete commands
        for name, cmd_info in self.shell.commands.items():
            if name.startswith(prefix):
                cmd_desc = cmd_info.doc[:50] + "..." if cmd_info.doc and len(cmd_info.doc) > 50 else (cmd_info.doc or "User command")
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display_meta=f"command - {cmd_desc}",
                    display=name,
                    style="class:command"
                )
    
    def _complete_arguments(self, tokens: List[str], after_space: bool = True) -> Iterable[Completion]:
        """Complete arguments for a specific command"""
        if not tokens:
            return
        
        command_name = tokens[0]
        
        # Handle subinstance commands
        if command_name in self.shell.subinstances:
            if len(tokens) > 1:
                # Delegate to subinstance completer
                sub_shell = self.shell.subinstances[command_name]
                sub_completer = FastShellCompleter(sub_shell)
                sub_completer.interactive_mode = self.interactive_mode  # 传递模式
                sub_text = " ".join(tokens[1:])
                
                # Preserve the trailing space if the original input had it
                if after_space:
                    sub_text += " "
                
                sub_doc = Document(sub_text, len(sub_text))
                yield from sub_completer.get_completions(sub_doc, None)
            elif after_space:
                # Show subinstance commands when after space
                sub_shell = self.shell.subinstances[command_name]
                sub_completer = FastShellCompleter(sub_shell)
                sub_completer.interactive_mode = self.interactive_mode  # 传递模式
                sub_doc = Document("", 0)
                yield from sub_completer.get_completions(sub_doc, None)
            return
        
        # Find the command
        cmd_info = None
        args_tokens = tokens[1:]  # Arguments after command name
        
        if command_name in self.shell.commands:
            cmd_info = self.shell.commands[command_name]
        elif command_name == 'root_command':
            # This is a root command, find the first root command
            for name, info in self.shell.commands.items():
                if info.root:
                    cmd_info = info
                    args_tokens = tokens[1:]  # All tokens are arguments for root command
                    break
        
        if not cmd_info or not cmd_info.model:
            return
        
        # Get model fields
        fields = cmd_info.model.model_fields
        
        # Check if we're expecting a flag value
        if len(args_tokens) >= 1 and args_tokens[-1].startswith('--'):
            # Previous token was a flag, we're expecting its value
            flag_name = args_tokens[-1][2:].replace('-', '_')
            if flag_name in fields:
                field_info = fields[flag_name]
                type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                description = getattr(field_info, 'description', '') or f"{flag_name} value"
                
                # Show placeholder for the expected value
                placeholder = f"<{flag_name.replace('_', ' ')}>"
                yield Completion(
                    placeholder,
                    start_position=0,
                    display_meta=f"{type_name} - {description}",
                    display=placeholder,
                    style="class:string"
                )
                return
        
        # Check if the previous token was a flag and we need its value
        if len(args_tokens) >= 2 and args_tokens[-2].startswith('--'):
            # We're providing a value for the previous flag, show remaining flags
            pass
        
        # Determine what we're completing
        current_token = args_tokens[-1] if args_tokens else ""
        
        if current_token.startswith('--'):
            # Complete flag names, but first analyze what's already provided
            # Analyze what arguments have been provided
            provided_flags = set()
            positional_count = 0
            i = 0
            while i < len(args_tokens[:-1]):  # Exclude current token being typed
                if args_tokens[i].startswith('--'):
                    flag_name = args_tokens[i][2:].replace('-', '_')
                    provided_flags.add(flag_name)
                    i += 2  # Skip flag and its value
                else:
                    positional_count += 1
                    i += 1
            
            # Get field names in order for positional arguments
            field_names = list(fields.keys())
            
            # Mark positional arguments as provided
            provided_positional = set()
            for i in range(min(positional_count, len(field_names))):
                provided_positional.add(field_names[i])
            
            # Combine both flag-provided and positional-provided arguments
            all_provided = provided_flags | provided_positional
            
            # Complete flag names only for fields not already provided
            flag_prefix = current_token[2:]
            for field_name, field_info in fields.items():
                if field_name not in all_provided:  # Only show flags for unprovided fields
                    flag_name = field_name.replace('_', '-')
                    if flag_name.startswith(flag_prefix):
                        type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                        description = getattr(field_info, 'description', '') or f"{field_name} argument"
                        
                        yield Completion(
                            f"--{flag_name}",
                            start_position=-len(current_token),
                            display_meta=f"{type_name} - {description}",
                            display=f"--{flag_name}",
                            style="class:argument"
                        )
        else:
            # Analyze what arguments have been provided
            provided_flags = set()
            positional_count = 0
            i = 0
            while i < len(args_tokens):
                if args_tokens[i].startswith('--'):
                    flag_name = args_tokens[i][2:].replace('-', '_')
                    provided_flags.add(flag_name)
                    i += 2  # Skip flag and its value
                else:
                    positional_count += 1
                    i += 1
            
            # If we're not after a space and have args, the last token is being typed
            # Don't count it as completed yet
            if not after_space and args_tokens and not args_tokens[-1].startswith('--'):
                positional_count -= 1
            
            # Get field names in order for positional arguments
            field_names = list(fields.keys())
            
            # Mark positional arguments as provided (only completed ones)
            provided_positional = set()
            for i in range(min(max(0, positional_count), len(field_names))):
                provided_positional.add(field_names[i])
            
            # Combine both flag-provided and positional-provided arguments
            all_provided = provided_flags | provided_positional
            
            # Show positional argument placeholder for the next unprovided field
            if positional_count < len(field_names):
                # Find the next field that hasn't been provided by either method
                next_positional_field = None
                for i in range(positional_count, len(field_names)):
                    field_name = field_names[i]
                    if field_name not in provided_flags:
                        next_positional_field = field_name
                        break
                
                if next_positional_field:
                    field_info = fields[next_positional_field]
                    placeholder = f"<{next_positional_field.replace('_', ' ')}>"
                    type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                    description = getattr(field_info, 'description', '') or f"{next_positional_field} value"
                    
                    yield Completion(
                        placeholder,
                        start_position=0,
                        display_meta=f"{type_name} - {description}",
                        display=placeholder,
                        style="class:string"
                    )
            
            # Show remaining flags (only for fields not provided via either method)
            remaining_fields = [name for name in fields.keys() if name not in all_provided]
            
            if remaining_fields:
                # Show available flags for remaining fields
                for field_name in remaining_fields:
                    field_info = fields[field_name]
                    flag_name = field_name.replace('_', '-')
                    type_name = getattr(field_info.annotation, '__name__', str(field_info.annotation))
                    description = getattr(field_info, 'description', '') or f"{field_name} argument"
                    
                    yield Completion(
                        f"--{flag_name}",
                        start_position=0,
                        display_meta=f"{type_name} - {description}",
                        display=f"--{flag_name}",
                        style="class:argument"
                    )