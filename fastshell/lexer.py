# Copyright (c) 2026 github.com/fastshell
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from prompt_toolkit.lexers import Lexer
import re


class FastShellLexer(Lexer):
    """Syntax highlighter for FastShell commands"""

    def __init__(self, shell=None):
        """Initialize lexer with optional shell reference for command validation"""
        self.shell = shell

    def lex_document(self, document):
        """Tokenize and highlight the document"""

        def get_tokens(line_number):
            line = document.lines[line_number]
            return list(self._tokenize_line(line))

        return get_tokens

    def _normalize_command_name(self, name):
        """Normalize command name for comparison (convert hyphens to underscores)"""
        return name.replace("-", "_")

    def _parse_command_path(self, line):
        """Parse the command line and identify which tokens should be highlighted as commands"""
        if not self.shell or not line.strip():
            return []

        # Extract non-flag tokens (potential command path)
        tokens = []
        try:
            # Simple tokenization to extract words
            import re

            words = re.findall(r"\b[\w-]+\b", line)

            # Filter out flag arguments (starting with -)
            command_tokens = []
            for word in words:
                if not word.startswith("-"):
                    command_tokens.append(word)
                else:
                    break  # Stop at first flag

            if not command_tokens:
                return []

            # Navigate through the shell hierarchy to validate the command path
            current_shell = self.shell
            command_indices = []

            for i, token in enumerate(command_tokens):
                # Check if token is a built-in command (help, exit, etc.)
                # Note: help is available in all contexts, but exit/quit only in main shell
                if token in ["help"]:
                    command_indices.append(i)
                    break  # help command found
                elif i == 0 and token in ["exit", "quit", "exec"]:
                    command_indices.append(i)
                    break  # Main shell built-in commands

                # Check if token is a direct command in current shell
                # Try both original name and normalized name (hyphen <-> underscore)
                normalized_token = self._normalize_command_name(token)
                if (
                    token in current_shell.commands
                    or normalized_token in current_shell.commands
                ):
                    command_indices.append(i)
                    break  # Found the final command

                # Check if token is a subinstance
                elif token in current_shell.subinstances:
                    command_indices.append(i)
                    current_shell = current_shell.subinstances[token]
                    # Continue to check next token in the subinstance

                # For the first token, check system commands
                elif (
                    i == 0
                    and hasattr(current_shell, "allow_system_commands")
                    and current_shell.allow_system_commands
                ):
                    command_indices.append(i)
                    break  # System commands don't have subcommands in our context

                else:
                    # Token not found in current context
                    break

            return command_indices

        except Exception:
            return []

    def _tokenize_line(self, line):
        """Tokenize a single line with syntax highlighting"""
        if not line.strip():
            yield ("", line)
            return

        # Parse the command path to identify which tokens should be highlighted as commands
        command_indices = self._parse_command_path(line)

        try:
            # Simple regex-based tokenization for better control
            patterns = [
                (r'"[^"]*"?', "string"),  # Double quoted strings
                (r"'[^']*'?", "string"),  # Single quoted strings
                (r"--[\w-]+", "argument"),  # Long flag arguments like --first-name
                (
                    r"-[a-zA-Z]+(?=\s|$)",
                    "argument",
                ),  # Short flags like -h, -la, -rf (only if followed by space or end)
                (r"\b\d+\.?\d*\b", "number"),  # Numbers (int or float)
                (r"\b[\w-]+\b", "text"),  # Regular words (including words with hyphens)
                (r"\s+", "whitespace"),  # Whitespace
                (r".", "text"),  # Any other character
            ]

            pos = 0
            word_index = (
                0  # Track which word we're processing (for command path detection)
            )

            while pos < len(line):
                matched = False

                for pattern, token_type in patterns:
                    regex = re.compile(pattern)
                    match = regex.match(line, pos)

                    if match:
                        text = match.group(0)

                        # Determine the style class
                        if token_type == "string":
                            style = "class:string"
                        elif token_type == "argument":
                            style = "class:argument"
                        elif token_type == "number":
                            style = "class:number"
                        elif token_type == "whitespace":
                            style = ""
                        elif token_type == "text":
                            # Check if this word should be highlighted as a command
                            if text.strip() and word_index in command_indices:
                                style = "class:command"
                            else:
                                style = "class:text"

                            # Increment word index for non-whitespace, non-flag tokens
                            if text.strip() and not text.startswith("-"):
                                word_index += 1
                        else:
                            style = "class:text"

                        yield (style, text)
                        pos = match.end()
                        matched = True
                        break

                if not matched:
                    # Fallback: yield single character
                    yield ("class:text", line[pos])
                    pos += 1

        except Exception:
            # Fallback to no highlighting if parsing fails
            yield ("", line)
