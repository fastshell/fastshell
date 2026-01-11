# Copyright (c) 2026 github.com/fastshell
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import shlex
from pydantic import BaseModel, ValidationError
from .exceptions import MultiplePossibleMatchError


class ArgumentParser:
    """Parse command line arguments into Pydantic models"""

    def parse_args_from_string(self, args_string: str, model: type[BaseModel]) -> BaseModel:
        """Parse arguments from string while handling quotes properly"""
        if not args_string.strip():
            return model()

        # For registered commands, we want standard shell behavior:
        # - Remove outer wrapping quotes: "Hello" -> Hello  
        # - Preserve embedded quotes: H"embedded"W -> H"embedded"W
        
        # First, try to detect if we have embedded quotes that shlex might mishandle
        has_embedded_quotes = self._has_embedded_quotes(args_string)
        
        if has_embedded_quotes:
            # Use our smart parsing for embedded quotes
            try:
                tokens = self._smart_split_preserving_quotes(args_string)
                return self.parse_args(tokens, model)
            except Exception:
                # If smart parsing fails, fall back to shlex
                pass
        
        try:
            # Use shlex for standard shell quote handling
            tokens = shlex.split(args_string)
            return self.parse_args(tokens, model)
        except ValueError:
            # If shlex fails due to unmatched quotes, try smart parsing
            try:
                tokens = self._smart_split_preserving_quotes(args_string)
                return self.parse_args(tokens, model)
            except Exception:
                pass
        except Exception:
            # If model validation fails, re-raise the validation error
            raise
        
        # Final fallback: simple split (should rarely be needed)
        tokens = args_string.split()
        return self.parse_args(tokens, model)
    
    def _has_embedded_quotes(self, text: str) -> bool:
        """Check if text has embedded quotes (quotes not at start/end of tokens)"""
        import re
        # Look for patterns like: word"quote"word or word'quote'word
        embedded_pattern = r'\w+["\'][^"\']*["\'][^\s]*|\w*["\'][^"\']*["\']\w+'
        return bool(re.search(embedded_pattern, text))
    
    def _smart_split_preserving_quotes(self, text: str) -> list[str]:
        """Split text while preserving embedded quotes"""
        import re
        
        # This regex finds words that may contain embedded quotes
        # It matches sequences of non-whitespace characters, including quoted sections
        pattern = r'(?:[^\s"\']+|"[^"]*"|\'[^\']*\')+|\S+'
        
        tokens = []
        for match in re.finditer(pattern, text):
            token = match.group(0)
            
            # Check if this looks like a flag
            if token.startswith('--'):
                tokens.append(token)
            elif token.startswith('-') and len(token) > 1:
                tokens.append(token)
            else:
                # For non-flag tokens, we need to handle quotes carefully
                # If the token is completely wrapped in quotes, remove outer quotes
                # But preserve embedded quotes
                processed_token = self._process_token_quotes(token)
                tokens.append(processed_token)
        
        return tokens
    
    def _process_token_quotes(self, token: str) -> str:
        """Process quotes in a single token, removing outer quotes but preserving embedded ones"""
        # If the token is completely wrapped in quotes, remove them
        if ((token.startswith('"') and token.endswith('"') and len(token) > 1) or
            (token.startswith("'") and token.endswith("'") and len(token) > 1)):
            # Check if it's truly wrapped (no unescaped quotes inside)
            inner = token[1:-1]
            quote_char = token[0]
            
            # Simple check: if there are no unescaped quotes of the same type inside, it's wrapped
            if quote_char == '"':
                # Check for unescaped quotes
                escaped_quotes = inner.count('\\"')
                total_quotes = inner.count('"')
                if total_quotes == escaped_quotes:  # All quotes are escaped
                    return inner
            else:  # single quote
                # Check for unescaped quotes  
                escaped_quotes = inner.count("\\'")
                total_quotes = inner.count("'")
                if total_quotes == escaped_quotes:  # All quotes are escaped
                    return inner
        
        # Otherwise, return as-is (preserves embedded quotes)
        return token

    def parse_args(self, args: list[str], model: type[BaseModel]) -> BaseModel:
        """Parse arguments list into model instance"""
        if not args:
            return model()

        # Get model fields and their types
        fields = model.model_fields
        field_names = list(fields.keys())

        # Separate flags and positional arguments
        flags, positional = self._separate_flags_and_positional(args)

        # Build kwargs for model - let Pydantic handle all type conversion
        kwargs = {}

        # Process flags first (keep as strings, let Pydantic convert)
        for flag_name, flag_value in flags.items():
            # Convert flag name (--first-name -> first_name)
            field_name = flag_name.replace("-", "_")
            if field_name in fields:
                kwargs[field_name] = flag_value

        # Process positional arguments
        available_fields = [name for name in field_names if name not in kwargs]

        # Check for conflicts before assigning positional arguments
        if len(positional) > len(available_fields):
            raise MultiplePossibleMatchError(f"Too many positional arguments provided")

        # Check if any positional argument would conflict with flags
        conflicts = []
        for i, pos_arg in enumerate(positional):
            if i < len(field_names):
                field_name = field_names[i]
                if field_name in kwargs:
                    conflicts.append(field_name)

        if conflicts:
            raise MultiplePossibleMatchError(
                f"Arguments specified both positionally and as flags: {conflicts}"
            )

        # Assign positional arguments to available fields (keep as strings)
        for i, pos_arg in enumerate(positional):
            if i < len(field_names):
                field_name = field_names[i]
                if field_name not in kwargs:  # Only assign if not already set by flag
                    kwargs[field_name] = pos_arg

        # Let Pydantic handle all validation and type conversion
        try:
            return model(**kwargs)
        except ValidationError as e:
            # Re-raise the original ValidationError without wrapping
            raise e

    def _separate_flags_and_positional(
        self, args: list[str]
    ) -> tuple[dict[str, str], list[str]]:
        """Separate flag arguments from positional arguments"""
        flags: dict[str, str] = {}
        positional: list[str] = []
        i = 0

        while i < len(args):
            arg = args[i]

            if arg.startswith("--"):
                # Long flag
                flag_name = arg[2:]
                if "=" in flag_name:
                    # --flag=value format
                    flag_name, flag_value = flag_name.split("=", 1)
                    flags[flag_name] = flag_value
                else:
                    # --flag value format
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
                        flags[flag_name] = args[i + 1]
                        i += 1
                    else:
                        flags[flag_name] = "true"  # Boolean flag
            elif arg.startswith("-") and len(arg) > 1:
                # Short flag (convert to long format)
                flag_name = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    flags[flag_name] = args[i + 1]
                    i += 1
                else:
                    flags[flag_name] = "true"
            else:
                # Positional argument
                positional.append(arg)

            i += 1

        return flags, positional
