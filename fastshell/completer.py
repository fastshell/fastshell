# Copyright (c) 2026 github.com/fastshell
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import Iterable, List
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
import shlex
import os


class FastShellCompleter(Completer):
    """Autocompleter for FastShell commands and arguments"""

    def __init__(self, shell):
        self.shell = shell
        self.interactive_mode = True  # Default to interactive mode

    def get_completions(
        self, document: Document, complete_event: CompleteEvent | None
    ) -> Iterable[Completion]:
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
        if len(tokens) == 1 and not text.endswith(" "):
            # First try FastShell commands
            fastshell_completions = list(self._complete_commands(tokens[0]))

            # If system commands are enabled and no FastShell commands match, try system completion
            if (
                not fastshell_completions
                and self.shell.allow_system_commands
                and self.interactive_mode
            ):
                # Get system command completions asynchronously
                yield from self._get_system_command_completions(text, len(text))
            else:
                yield from fastshell_completions
            return

        # If we have tokens and are after whitespace, or have multiple tokens, complete arguments
        if len(tokens) >= 1 and (text.endswith(" ") or len(tokens) > 1):
            # Check if first token is a valid command or subinstance
            command_name = tokens[0]

            # Check if it's a built-in command that needs special argument handling
            if command_name in ["help", "exec"]:
                yield from self._complete_arguments(tokens, text.endswith(" "))
                return

            # Check if it's a subinstance
            if command_name in self.shell.subinstances:
                yield from self._complete_arguments(tokens, text.endswith(" "))
                return

            # Check if it's a direct command
            if command_name in self.shell.commands:
                cmd_info = self.shell.commands[command_name]
                # In interactive mode, root commands still support completion with explicit command name
                # We don't skip completion here - root commands can still be called explicitly
                yield from self._complete_arguments(tokens, text.endswith(" "))
                return

            # If it's not a FastShell command and system commands are enabled, try system completion
            if (
                self.shell.allow_system_commands
                and self.interactive_mode
                and command_name not in ["help", "exit", "quit", "exec"]
            ):
                yield from self._get_system_file_completions(text, len(text))
                return

            # Check if it's a root command (only in non-interactive mode)
            if not self.interactive_mode:
                for name, cmd_info in self.shell.commands.items():
                    if cmd_info.root:
                        # For root commands, all tokens are arguments
                        yield from self._complete_arguments(
                            ["root_command"] + tokens, text.endswith(" ")
                        )
                        return

        # Fallback to command completion (only if we're completing the first token)
        if len(tokens) == 1 and not text.endswith(" "):
            yield from self._complete_commands(tokens[-1] if tokens else "")

    def _get_system_command_completions(
        self, text: str, cursor_pos: int
    ) -> Iterable[Completion]:
        """Get system command completions (synchronous wrapper for async call)"""
        try:
            # This is a simplified approach - in a real implementation,
            # we'd need to handle async completion properly
            # For now, we'll provide basic file completion for system commands

            # Extract the current word being completed
            words = text.split()
            if words:
                current_word = words[-1]

                # Basic file/directory completion
                completions = self._get_basic_file_completions(current_word)
                for completion in completions:
                    yield Completion(
                        completion,
                        start_position=-len(current_word),
                        display_meta="file",
                        style="class:argument",
                    )
        except Exception:
            pass

    def _get_system_file_completions(
        self, text: str, cursor_pos: int
    ) -> Iterable[Completion]:
        """Get file completions for system commands"""
        try:
            # Extract the last word (potential file path)
            words = text.split()
            if not words:
                return

            # Get the word being completed
            if text.endswith(" "):
                current_word = ""
                start_pos = 0
            else:
                current_word = words[-1]
                start_pos = -len(current_word)

            # Get file completions
            completions = self._get_basic_file_completions(current_word)
            for completion in completions:
                yield Completion(
                    completion,
                    start_position=start_pos,
                    display_meta="file",
                    style="class:argument",
                )
        except Exception:
            pass

    def get_basic_file_completions(self, partial_path: str) -> List[str]:
        """Get basic file/directory completions synchronously (public method)"""
        return self._get_basic_file_completions(partial_path)

    def _get_basic_file_completions(self, partial_path: str) -> List[str]:
        """Get basic file/directory completions synchronously"""
        try:
            # Get current directory from persistent shell if available
            if self.shell.persistent_shell:
                base_dir = self.shell.persistent_shell.get_current_dir()
            else:
                base_dir = os.getcwd()

            # Handle path components
            if os.sep in partial_path or ("/" in partial_path and os.sep != "/"):
                # Normalize separators
                partial_path = partial_path.replace("/", os.sep)
                dir_part = os.path.dirname(partial_path)
                file_part = os.path.basename(partial_path)

                if os.path.isabs(dir_part):
                    search_dir = dir_part
                else:
                    search_dir = (
                        os.path.join(base_dir, dir_part) if dir_part else base_dir
                    )
            else:
                search_dir = base_dir
                file_part = partial_path
                dir_part = ""

            if not os.path.exists(search_dir):
                return []

            # Get matching files/directories
            completions = []
            try:
                for item in os.listdir(search_dir):
                    if item.lower().startswith(file_part.lower()):
                        if dir_part:
                            full_path = os.path.join(dir_part, item)
                        else:
                            full_path = item

                        # Add separator for directories
                        if os.path.isdir(os.path.join(search_dir, item)):
                            full_path += os.sep

                        completions.append(full_path)

                        # Limit completions to avoid overwhelming the user
                        if len(completions) >= 20:
                            break
            except PermissionError:
                pass

            return completions

        except Exception:
            return []

    def _complete_commands(self, prefix: str) -> Iterable[Completion]:
        """Complete command names and subinstances"""
        # Complete built-in commands first
        built_in_commands = [
            ("help", "Show help information"),
        ]

        # Only add exit/quit/exec commands for main shell (not subinstances)
        if not self.shell.parent:
            built_in_commands.extend(
                [
                    ("exit", "Exit the shell"),
                    ("quit", "Exit the shell"),
                ]
            )
            
            # Add exec command only if system commands are allowed
            if self.shell.allow_system_commands:
                built_in_commands.append(("exec", "Force execution of system commands"))

        for cmd_name, cmd_desc in built_in_commands:
            if cmd_name.startswith(prefix):
                yield Completion(
                    cmd_name,
                    start_position=-len(prefix),
                    display_meta=f"built-in - {cmd_desc}",
                    display=cmd_name,
                    style="class:command",
                )

        # Complete subinstances
        for name in self.shell.subinstances:
            if name.startswith(prefix):
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display_meta="subcommand",
                    style="class:command",
                )

        # Complete commands
        for name, cmd_info in self.shell.commands.items():
            if name.startswith(prefix):
                cmd_desc = (
                    cmd_info.doc[:50] + "..."
                    if cmd_info.doc and len(cmd_info.doc) > 50
                    else (cmd_info.doc or "User command")
                )
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display_meta=f"command - {cmd_desc}",
                    display=name,
                    style="class:command",
                )

    def _complete_arguments(
        self, tokens: List[str], after_space: bool = True
    ) -> Iterable[Completion]:
        """Complete arguments for a specific command"""
        if not tokens:
            return

        command_name = tokens[0]

        # Handle built-in exec command specially
        if command_name == "exec":
            # For exec command, only provide file/path completions
            # Don't suggest predefined system commands - let users type what they need
            if len(tokens) >= 1:
                # Provide file and directory completions for any position after "exec"
                yield from self._get_system_file_completions(" ".join(tokens), len(" ".join(tokens)))
            return

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
        elif command_name == "root_command":
            # This is a root command, find the first root command
            for name, info in self.shell.commands.items():
                if info.root:
                    cmd_info = info
                    args_tokens = tokens[
                        1:
                    ]  # All tokens are arguments for root command
                    break

        if not cmd_info or not cmd_info.model:
            return

        # Get model fields
        fields = cmd_info.model.model_fields

        # Check if we're expecting a flag value
        if len(args_tokens) >= 1 and args_tokens[-1].startswith("--"):
            # Previous token was a flag, we're expecting its value
            flag_name = args_tokens[-1][2:].replace("-", "_")
            if flag_name in fields:
                field_info = fields[flag_name]
                type_name = getattr(
                    field_info.annotation, "__name__", str(field_info.annotation)
                )
                description = (
                    getattr(field_info, "description", "") or f"{flag_name} value"
                )

                # Show placeholder for the expected value
                placeholder = f"<{flag_name.replace('_', ' ')}>"
                yield Completion(
                    placeholder,
                    start_position=0,
                    display_meta=f"{type_name} - {description}",
                    display=placeholder,
                    style="class:string",
                )
                return

        # Check if the previous token was a flag and we need its value
        if len(args_tokens) >= 2 and args_tokens[-2].startswith("--"):
            # We're providing a value for the previous flag, show remaining flags
            pass

        # Determine what we're completing
        current_token = args_tokens[-1] if args_tokens else ""

        if current_token.startswith("--"):
            # Complete flag names, but first analyze what's already provided
            # Analyze what arguments have been provided
            provided_flags = set()
            positional_count = 0
            i = 0
            while i < len(args_tokens[:-1]):  # Exclude current token being typed
                if args_tokens[i].startswith("--"):
                    flag_name = args_tokens[i][2:].replace("-", "_")
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
                if (
                    field_name not in all_provided
                ):  # Only show flags for unprovided fields
                    flag_name = field_name.replace("_", "-")
                    if flag_name.startswith(flag_prefix):
                        type_name = getattr(
                            field_info.annotation,
                            "__name__",
                            str(field_info.annotation),
                        )
                        description = (
                            getattr(field_info, "description", "")
                            or f"{field_name} argument"
                        )

                        yield Completion(
                            f"--{flag_name}",
                            start_position=-len(current_token),
                            display_meta=f"{type_name} - {description}",
                            display=f"--{flag_name}",
                            style="class:argument",
                        )
        else:
            # Analyze what arguments have been provided
            provided_flags = set()
            positional_count = 0
            i = 0
            while i < len(args_tokens):
                if args_tokens[i].startswith("--"):
                    flag_name = args_tokens[i][2:].replace("-", "_")
                    provided_flags.add(flag_name)
                    i += 2  # Skip flag and its value
                else:
                    positional_count += 1
                    i += 1

            # If we're not after a space and have args, the last token is being typed
            # Don't count it as completed yet
            if not after_space and args_tokens and not args_tokens[-1].startswith("--"):
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
                    type_name = getattr(
                        field_info.annotation, "__name__", str(field_info.annotation)
                    )
                    description = (
                        getattr(field_info, "description", "")
                        or f"{next_positional_field} value"
                    )

                    yield Completion(
                        placeholder,
                        start_position=0,
                        display_meta=f"{type_name} - {description}",
                        display=placeholder,
                        style="class:string",
                    )

            # Show remaining flags (only for fields not provided via either method)
            remaining_fields = [
                name for name in fields.keys() if name not in all_provided
            ]

            if remaining_fields:
                # Show available flags for remaining fields
                for field_name in remaining_fields:
                    field_info = fields[field_name]
                    flag_name = field_name.replace("_", "-")
                    type_name = getattr(
                        field_info.annotation, "__name__", str(field_info.annotation)
                    )
                    description = (
                        getattr(field_info, "description", "")
                        or f"{field_name} argument"
                    )

                    yield Completion(
                        f"--{flag_name}",
                        start_position=0,
                        display_meta=f"{type_name} - {description}",
                        display=f"--{flag_name}",
                        style="class:argument",
                    )
