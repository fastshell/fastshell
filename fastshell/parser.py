from typing import Any
from pydantic import BaseModel, ValidationError
from .exceptions import MultiplePossibleMatchError


class ArgumentParser:
    """Parse command line arguments into Pydantic models"""
    
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
            field_name = flag_name.replace('-', '_')
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
            raise MultiplePossibleMatchError(f"Arguments specified both positionally and as flags: {conflicts}")
        
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
    
    def _separate_flags_and_positional(self, args: list[str]) -> tuple[dict[str, str], list[str]]:
        """Separate flag arguments from positional arguments"""
        flags: dict[str, str] = {}
        positional: list[str] = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--'):
                # Long flag
                flag_name = arg[2:]
                if '=' in flag_name:
                    # --flag=value format
                    flag_name, flag_value = flag_name.split('=', 1)
                    flags[flag_name] = flag_value
                else:
                    # --flag value format
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        flags[flag_name] = args[i + 1]
                        i += 1
                    else:
                        flags[flag_name] = "true"  # Boolean flag
            elif arg.startswith('-') and len(arg) > 1:
                # Short flag (convert to long format)
                flag_name = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    flags[flag_name] = args[i + 1]
                    i += 1
                else:
                    flags[flag_name] = "true"
            else:
                # Positional argument
                positional.append(arg)
            
            i += 1
        
        return flags, positional