from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import FormattedText
import re
import shlex


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
    
    def _is_valid_command(self, command_text):
        """Check if the command text matches a real command in the shell"""
        if not self.shell:
            return True  # If no shell reference, highlight all first tokens as commands
        
        # Check direct commands
        if command_text in self.shell.commands:
            return True
        
        # Check subinstances
        if command_text in self.shell.subinstances:
            return True
        
        # Check built-in commands
        builtin_commands = ['help', 'exit', 'quit']
        if command_text in builtin_commands:
            return True
        
        # For root commands, we need to be more careful
        # A root command means the command can be called without prefix,
        # but we should still validate if the specific command exists
        # We don't want to highlight ALL first tokens just because a root command exists
        
        return False
    
    def _tokenize_line(self, line):
        """Tokenize a single line with syntax highlighting"""
        if not line.strip():
            yield ('', line)
            return
        
        # Try to parse with shlex to handle quotes properly
        try:
            # Simple regex-based tokenization for better control
            patterns = [
                (r'"[^"]*"?', 'string'),           # Double quoted strings
                (r"'[^']*'?", 'string'),           # Single quoted strings
                (r'--[\w-]+', 'argument'),         # Flag arguments like --first-name
                (r'-\w', 'argument'),              # Short flags like -h
                (r'\b\d+\.?\d*\b', 'number'),      # Numbers (int or float)
                (r'\b\w+\b', 'text'),              # Regular words
                (r'\s+', 'whitespace'),            # Whitespace
                (r'.', 'text'),                    # Any other character
            ]
            
            pos = 0
            first_token = True
            
            while pos < len(line):
                matched = False
                
                for pattern, token_type in patterns:
                    regex = re.compile(pattern)
                    match = regex.match(line, pos)
                    
                    if match:
                        text = match.group(0)
                        
                        # Determine the style class
                        if token_type == 'string':
                            style = 'class:string'
                        elif token_type == 'argument':
                            style = 'class:argument'
                        elif token_type == 'number':
                            style = 'class:number'
                        elif token_type == 'whitespace':
                            style = ''
                        elif token_type == 'text' and first_token and text.strip():
                            # First non-whitespace token - check if it's a valid command
                            if self._is_valid_command(text.strip()):
                                style = 'class:command'
                            else:
                                style = 'class:text'  # Invalid command, use normal text style
                            first_token = False
                        else:
                            style = 'class:text'
                        
                        yield (style, text)
                        pos = match.end()
                        matched = True
                        
                        # Mark that we've seen the first token
                        if text.strip():
                            first_token = False
                        break
                
                if not matched:
                    # Fallback: yield single character
                    yield ('class:text', line[pos])
                    pos += 1
                    
        except Exception:
            # Fallback to no highlighting if parsing fails
            yield ('', line)