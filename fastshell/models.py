from pydantic import BaseModel, Field
from typing import Optional


class Arguments(BaseModel):
    """Base class for command arguments - users can inherit from this"""
    pass


# Example argument models for common use cases
class BasicArgs(BaseModel):
    """Basic arguments with common patterns"""
    name: str = Field(..., description="Name argument")
    value: Optional[str] = Field(None, description="Optional value")
    count: int = Field(1, description="Count parameter")
    verbose: bool = Field(False, description="Enable verbose output")


class FileArgs(BaseModel):
    """File operation arguments"""
    input_file: str = Field(..., description="Input file path")
    output_file: Optional[str] = Field(None, description="Output file path")
    overwrite: bool = Field(False, description="Overwrite existing files")


class NetworkArgs(BaseModel):
    """Network operation arguments"""
    host: str = Field("localhost", description="Host address")
    port: int = Field(8080, description="Port number")
    timeout: int = Field(30, description="Timeout in seconds")