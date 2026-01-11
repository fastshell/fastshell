<!--
 Copyright (c) 2026 github.com/fastshell

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# FastShell Best Practices

This guide covers best practices for building robust, maintainable, and user-friendly CLI applications with FastShell.

## Table of Contents

- [Project Structure](#project-structure)
- [Command Design](#command-design)
- [Argument Handling](#argument-handling)
- [Error Management](#error-management)
- [User Experience](#user-experience)
- [Performance](#performance)
- [Testing](#testing)
- [Documentation](#documentation)
- [Security](#security)
- [Deployment](#deployment)

## Project Structure

### Recommended Directory Layout

```
my-cli-app/
├── src/
│   ├── my_cli/
│   │   ├── __init__.py
│   │   ├── main.py              # Main application entry point
│   │   ├── commands/            # Command modules
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # Database-related commands
│   │   │   ├── deployment.py    # Deployment commands
│   │   │   └── utils.py         # Utility commands
│   │   ├── models/              # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   └── deployment.py
│   │   ├── services/            # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── database_service.py
│   │   │   └── deployment_service.py
│   │   └── utils/               # Shared utilities
│   │       ├── __init__.py
│   │       ├── config.py
│   │       └── helpers.py
├── tests/
│   ├── test_commands/
│   ├── test_models/
│   └── test_services/
├── docs/
├── pyproject.toml
├── README.md
└── requirements.txt
```

### Modular Command Organization

```python
# main.py
from fastshell import FastShell
from .commands import database, deployment, utils

def create_app():
    app = FastShell("MyCLI", "My awesome CLI application")

    # Register command modules
    database.register_commands(app)
    deployment.register_commands(app)
    utils.register_commands(app)

    return app

def main():
    app = create_app()
    app.run()

if __name__ == "__main__":
    main()
```

```python
# commands/database.py
from fastshell import FastShell
from ..models.database import DatabaseConfig
from ..services.database_service import DatabaseService

def register_commands(app: FastShell):
    db = app.subinstance("db", "Database management")

    @db.command()
    async def migrate(config: DatabaseConfig):
        """Run database migrations"""
        service = DatabaseService(config)
        return await service.migrate()

    @db.command()
    async def seed(config: DatabaseConfig):
        """Seed database with test data"""
        service = DatabaseService(config)
        return await service.seed()
```

## Command Design

### Use Clear, Descriptive Names

```python
# Good
@app.command()
def create_user(name: str, email: str):
    """Create a new user account"""
    pass

@app.command()
def list_active_users():
    """List all active user accounts"""
    pass

# Avoid
@app.command()
def cu(n: str, e: str):  # Unclear abbreviations
    pass

@app.command()
def do_stuff():  # Vague naming
    pass
```

### Follow Consistent Naming Conventions

```python
# Use verb-noun pattern for actions
@app.command()
def create_project(): pass

@app.command()
def delete_project(): pass

@app.command()
def list_projects(): pass

# Use consistent parameter naming
@app.command()
def deploy_app(environment: str, version: str = "latest"):
    pass

@app.command()
def rollback_app(environment: str, version: str):
    pass
```

### Group Related Commands

```python
# Create logical groupings
app = FastShell("DevCLI", "Development tools")

# User management
users = app.subinstance("users", "User management")

@users.command()
def create(name: str, email: str): pass

@users.command()
def delete(user_id: int): pass

@users.command()
def list_all(): pass

# Project management
projects = app.subinstance("projects", "Project management")

@projects.command()
def create(name: str, template: str = "basic"): pass

@projects.command()
def deploy(environment: str): pass
```

## Argument Handling

### Use Pydantic Models for Complex Arguments

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from pathlib import Path

class DeploymentConfig(BaseModel):
    environment: str = Field(description="Target environment")
    version: str = Field(default="latest", description="Version to deploy")
    replicas: int = Field(default=1, ge=1, le=10, description="Number of replicas")
    config_file: Optional[Path] = Field(default=None, description="Custom config file")
    features: List[str] = Field(default_factory=list, description="Feature flags to enable")

    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['dev', 'staging', 'prod']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {", ".join(allowed)}')
        return v

    @validator('config_file')
    def validate_config_file(cls, v):
        if v and not v.exists():
            raise ValueError(f'Config file does not exist: {v}')
        return v

@app.command()
def deploy(config: DeploymentConfig):
    """Deploy application with comprehensive configuration"""
    # Implementation here
    pass
```

### Provide Sensible Defaults

```python
class ServerConfig(BaseModel):
    host: str = Field(default="localhost", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

@app.command()
def start_server(config: ServerConfig):
    """Start the development server"""
    # Users can call with minimal arguments:
    # start_server
    # start_server --port 3000
    # start_server --host 0.0.0.0 --port 3000 --debug
    pass
```

### Use Environment Variables for Configuration

```python
import os
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    url: str = Field(
        default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///app.db"),
        description="Database connection URL"
    )
    pool_size: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "5")),
        description="Connection pool size"
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DB_DEBUG", "false").lower() == "true",
        description="Enable database debugging"
    )
```

## Error Management

### Provide Clear Error Messages

```python
@app.command()
def process_file(file_path: str):
    """Process a data file"""
    try:
        path = Path(file_path)

        if not path.exists():
            return f"❌ Error: File '{file_path}' does not exist"

        if not path.is_file():
            return f"❌ Error: '{file_path}' is not a file"

        if path.suffix not in ['.json', '.yaml', '.yml']:
            return f"❌ Error: Unsupported file type '{path.suffix}'. Supported: .json, .yaml, .yml"

        # Process file
        with path.open() as f:
            data = json.load(f)

        return f"✅ Successfully processed {len(data)} records from {file_path}"

    except json.JSONDecodeError as e:
        return f"❌ Error: Invalid JSON in '{file_path}': {e}"
    except PermissionError:
        return f"❌ Error: Permission denied accessing '{file_path}'"
    except Exception as e:
        return f"❌ Unexpected error processing '{file_path}': {e}"
```

### Use Structured Error Handling

```python
from enum import Enum
from typing import Union

class ErrorCode(Enum):
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_FORMAT = "INVALID_FORMAT"
    NETWORK_ERROR = "NETWORK_ERROR"

class CLIError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: str = ""):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)

def handle_cli_error(error: CLIError) -> str:
    """Convert CLI errors to user-friendly messages"""
    emoji_map = {
        ErrorCode.FILE_NOT_FOUND: "📁",
        ErrorCode.PERMISSION_DENIED: "🔒",
        ErrorCode.INVALID_FORMAT: "📄",
        ErrorCode.NETWORK_ERROR: "🌐"
    }

    emoji = emoji_map.get(error.code, "❌")
    message = f"{emoji} {error.message}"

    if error.details:
        message += f"\n   Details: {error.details}"

    return message

@app.command()
def upload_file(file_path: str, destination: str):
    """Upload file to remote destination"""
    try:
        # Implementation
        pass
    except FileNotFoundError:
        error = CLIError(
            ErrorCode.FILE_NOT_FOUND,
            f"File '{file_path}' not found",
            "Check the file path and try again"
        )
        return handle_cli_error(error)
    except PermissionError:
        error = CLIError(
            ErrorCode.PERMISSION_DENIED,
            f"Permission denied accessing '{file_path}'",
            "Check file permissions or run with appropriate privileges"
        )
        return handle_cli_error(error)
```

### Validate Early and Often

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path

class BackupConfig(BaseModel):
    source_dir: Path = Field(description="Source directory to backup")
    destination: Path = Field(description="Backup destination")
    exclude_patterns: List[str] = Field(default_factory=list, description="Patterns to exclude")

    @validator('source_dir')
    def source_must_exist(cls, v):
        if not v.exists():
            raise ValueError(f"Source directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Source path is not a directory: {v}")
        return v

    @validator('destination')
    def destination_must_be_writable(cls, v):
        if v.exists() and not v.is_dir():
            raise ValueError(f"Destination exists but is not a directory: {v}")

        # Check if parent directory is writable
        parent = v.parent
        if not parent.exists():
            raise ValueError(f"Destination parent directory does not exist: {parent}")
        if not os.access(parent, os.W_OK):
            raise ValueError(f"No write permission for destination parent: {parent}")

        return v

@app.command()
def backup(config: BackupConfig):
    """Create backup with validation"""
    # Validation happens automatically via Pydantic
    # Implementation here
    pass
```

## User Experience

### Provide Rich Help Information

```python
@app.command()
def deploy(
    environment: str = Field(description="Target environment (dev, staging, prod)"),
    version: str = Field(default="latest", description="Version tag to deploy"),
    replicas: int = Field(default=1, description="Number of replicas (1-10)", ge=1, le=10),
    wait: bool = Field(default=True, description="Wait for deployment to complete"),
    timeout: int = Field(default=300, description="Deployment timeout in seconds")
):
    """
    Deploy application to specified environment.

    This command deploys your application to the specified environment
    with configurable scaling and timeout options.

    Examples:
        deploy dev                          # Deploy latest to dev
        deploy prod --version v1.2.3       # Deploy specific version to prod
        deploy staging --replicas 3 --no-wait  # Deploy with scaling, don't wait
    """
    pass
```

### Show Progress for Long Operations

```python
import asyncio
from rich.progress import Progress, TaskID

@app.command()
async def process_large_dataset(file_path: str, batch_size: int = 1000):
    """Process large dataset with progress indication"""
    try:
        # Read file to get total size
        with open(file_path, 'r') as f:
            total_lines = sum(1 for _ in f)

        with Progress() as progress:
            task = progress.add_task("Processing...", total=total_lines)

            with open(file_path, 'r') as f:
                processed = 0
                batch = []

                for line in f:
                    batch.append(line.strip())

                    if len(batch) >= batch_size:
                        # Process batch
                        await process_batch(batch)
                        processed += len(batch)
                        progress.update(task, completed=processed)
                        batch = []

                # Process remaining items
                if batch:
                    await process_batch(batch)
                    processed += len(batch)
                    progress.update(task, completed=processed)

        return f"✅ Processed {processed} records from {file_path}"

    except Exception as e:
        return f"❌ Error processing dataset: {e}"

async def process_batch(batch: List[str]):
    """Process a batch of data"""
    await asyncio.sleep(0.1)  # Simulate processing time
```

### Use Consistent Output Formatting

```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def format_success(message: str) -> str:
    return f"✅ {message}"

def format_error(message: str) -> str:
    return f"❌ {message}"

def format_warning(message: str) -> str:
    return f"⚠️  {message}"

def format_info(message: str) -> str:
    return f"ℹ️  {message}"

@app.command()
def list_services(format: str = "table"):
    """List services with consistent formatting"""
    services = [
        {"name": "web-api", "status": "running", "port": 8000, "uptime": "2d 3h"},
        {"name": "database", "status": "running", "port": 5432, "uptime": "5d 12h"},
        {"name": "cache", "status": "stopped", "port": 6379, "uptime": "0h"}
    ]

    if format == "json":
        return json.dumps(services, indent=2)

    elif format == "table":
        table = Table(title="Services Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Port", style="yellow")
        table.add_column("Uptime", style="blue")

        for service in services:
            status_style = "green" if service["status"] == "running" else "red"
            table.add_row(
                service["name"],
                f"[{status_style}]{service['status']}[/{status_style}]",
                str(service["port"]),
                service["uptime"]
            )

        console.print(table)
        return ""

    else:
        return format_error(f"Unsupported format: {format}")
```

## Performance

### Use Async for I/O Operations

```python
import asyncio
import aiohttp
import aiofiles

@app.command()
async def fetch_multiple_urls(urls: List[str], timeout: int = 30):
    """Fetch multiple URLs concurrently"""
    async def fetch_url(session, url):
        try:
            async with session.get(url, timeout=timeout) as response:
                return {
                    "url": url,
                    "status": response.status,
                    "size": len(await response.text())
                }
        except Exception as e:
            return {"url": url, "error": str(e)}

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    # Format results
    success_count = sum(1 for r in results if "error" not in r)
    return f"Fetched {success_count}/{len(urls)} URLs successfully"

@app.command()
async def process_files_parallel(directory: str, pattern: str = "*.txt"):
    """Process multiple files in parallel"""
    path = Path(directory)
    files = list(path.glob(pattern))

    async def process_file(file_path):
        async with aiofiles.open(file_path, 'r') as f:
            content = await f.read()
            # Process content
            return len(content.split())

    tasks = [process_file(f) for f in files]
    word_counts = await asyncio.gather(*tasks)

    total_words = sum(word_counts)
    return f"Processed {len(files)} files, total words: {total_words}"
```

### Cache Expensive Operations

```python
import functools
import time
from typing import Dict, Any

# Simple in-memory cache
_cache: Dict[str, tuple[Any, float]] = {}
CACHE_TTL = 300  # 5 minutes

def cached(ttl: int = CACHE_TTL):
    """Cache decorator with TTL"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Check cache
            if key in _cache:
                value, timestamp = _cache[key]
                if time.time() - timestamp < ttl:
                    return value

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache[key] = (result, time.time())
            return result

        return wrapper
    return decorator

@cached(ttl=600)  # Cache for 10 minutes
def expensive_computation(data: str) -> str:
    """Simulate expensive computation"""
    time.sleep(2)  # Simulate work
    return f"Processed {len(data)} characters"

@app.command()
def analyze_data(input_data: str):
    """Analyze data with caching"""
    result = expensive_computation(input_data)
    return f"Analysis complete: {result}"
```

## Testing

### Write Comprehensive Tests

```python
# tests/test_commands.py
import pytest
import asyncio
from unittest.mock import patch, mock_open
from my_cli.main import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.mark.asyncio
async def test_deploy_command_success(app):
    """Test successful deployment"""
    result = await app.execute_command("deploy dev --version v1.0.0")
    assert "✅" in result
    assert "v1.0.0" in result

@pytest.mark.asyncio
async def test_deploy_command_invalid_environment(app):
    """Test deployment with invalid environment"""
    result = await app.execute_command("deploy invalid_env")
    assert "❌" in result
    assert "Environment must be one of" in result

@pytest.mark.asyncio
async def test_file_processing_command(app):
    """Test file processing with mocked file"""
    mock_data = '{"records": [{"id": 1}, {"id": 2}]}'

    with patch("builtins.open", mock_open(read_data=mock_data)):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.is_file", return_value=True):
                result = await app.execute_command("process-file test.json")
                assert "✅" in result
                assert "2 records" in result

def test_cli_mode(app):
    """Test CLI mode execution"""
    with patch('sys.argv', ['app.py', 'deploy', 'dev']):
        # Test CLI mode
        pass

def test_interactive_mode(app):
    """Test interactive mode"""
    # Test interactive features
    pass
```

### Test Both CLI and Interactive Modes

```python
@pytest.mark.asyncio
async def test_command_in_both_modes(app):
    """Test command works in both CLI and interactive modes"""
    # Test CLI mode
    cli_result = await app.execute_command("list-users", interactive_mode=False)

    # Test interactive mode
    interactive_result = await app.execute_command("list-users", interactive_mode=True)

    # Results should be similar (accounting for mode differences)
    assert "users" in cli_result.lower()
    assert "users" in interactive_result.lower()
```

## Documentation

### Document Commands Thoroughly

```python
@app.command()
def backup_database(
    database_url: str = Field(description="Database connection URL"),
    output_file: str = Field(description="Backup file path"),
    compress: bool = Field(default=True, description="Compress backup file"),
    exclude_tables: List[str] = Field(default_factory=list, description="Tables to exclude")
):
    """
    Create a backup of the database.

    This command creates a complete backup of the specified database,
    with options for compression and selective table exclusion.

    The backup process:
    1. Connects to the database using the provided URL
    2. Exports all tables (except excluded ones)
    3. Optionally compresses the output
    4. Saves to the specified file

    Examples:
        # Basic backup
        backup-database postgresql://user:pass@host/db backup.sql

        # Compressed backup excluding logs
        backup-database postgresql://user:pass@host/db backup.sql.gz \\
            --compress --exclude-tables logs audit_trail

        # Uncompressed backup
        backup-database postgresql://user:pass@host/db backup.sql --no-compress

    Note:
        Large databases may take significant time to backup.
        Ensure sufficient disk space is available.
    """
    pass
```

### Provide Usage Examples

```python
# Create examples directory with sample commands
examples = {
    "basic_usage": [
        "# List all users",
        "list-users",
        "",
        "# Create a new user",
        "create-user --name 'John Doe' --email john@example.com",
        "",
        "# Deploy to staging",
        "deploy staging --version v1.2.3"
    ],
    "advanced_usage": [
        "# Backup with custom options",
        "backup-database postgresql://localhost/mydb backup.sql \\",
        "    --exclude-tables temp_data logs \\",
        "    --compress",
        "",
        "# Process files in parallel",
        "process-files /data/*.json --workers 4 --batch-size 1000"
    ]
}
```

## Security

### Validate All Inputs

```python
from pydantic import BaseModel, Field, validator
import re

class UserInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(min_length=8)

    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username must contain only letters, numbers, hyphens, and underscores')
        return v

    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

### Handle Sensitive Data Carefully

```python
import os
import getpass
from pathlib import Path

@app.command()
def login(username: str, password_file: str = ""):
    """Login with secure password handling"""
    if password_file:
        # Read password from file
        try:
            password = Path(password_file).read_text().strip()
        except Exception as e:
            return f"❌ Error reading password file: {e}"
    else:
        # Prompt for password (doesn't echo to terminal)
        password = getpass.getpass("Password: ")

    # Don't log or print the password
    # Use it only for authentication
    success = authenticate(username, password)

    # Clear password from memory
    password = None

    if success:
        return "✅ Login successful"
    else:
        return "❌ Login failed"

def authenticate(username: str, password: str) -> bool:
    """Authenticate user (implementation depends on your auth system)"""
    # Implementation here
    pass
```

### Sanitize File Paths

```python
import os
from pathlib import Path

def safe_path(base_dir: Path, user_path: str) -> Path:
    """Create safe path within base directory"""
    # Resolve the path and ensure it's within base_dir
    full_path = (base_dir / user_path).resolve()

    # Check if the resolved path is within base_dir
    try:
        full_path.relative_to(base_dir.resolve())
        return full_path
    except ValueError:
        raise ValueError(f"Path '{user_path}' is outside allowed directory")

@app.command()
def read_config_file(filename: str):
    """Read configuration file safely"""
    try:
        config_dir = Path("/etc/myapp/configs")
        safe_file_path = safe_path(config_dir, filename)

        if not safe_file_path.exists():
            return f"❌ Config file not found: {filename}"

        content = safe_file_path.read_text()
        return f"✅ Read {len(content)} characters from {filename}"

    except ValueError as e:
        return f"❌ Security error: {e}"
    except Exception as e:
        return f"❌ Error reading file: {e}"
```

## Deployment

### Create Proper Package Structure

```python
# pyproject.toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "my-cli-app"
description = "My awesome CLI application"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "fastshell>=1.0.0",
    "pydantic>=1.10.0",
    "rich>=12.0.0",
    "aiohttp>=3.8.0",
]
dynamic = ["version"]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=22.0.0",
    "isort>=5.10.0",
    "flake8>=4.0.0",
    "mypy>=0.991",
]

[project.scripts]
my-cli = "my_cli.main:main"

[tool.setuptools_scm]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Add Configuration Management

```python
# config.py
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    """Application configuration"""

    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".my-cli")
    log_file: Path = Field(default_factory=lambda: Path.home() / ".my-cli" / "app.log")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # API settings
    api_base_url: str = Field(default="https://api.example.com")
    api_timeout: int = Field(default=30)

    # Feature flags
    enable_analytics: bool = Field(default=False)
    enable_auto_update: bool = Field(default=True)

    @classmethod
    def load(cls) -> 'AppConfig':
        """Load configuration from environment and config file"""
        config_file = Path.home() / ".my-cli" / "config.json"

        if config_file.exists():
            import json
            with config_file.open() as f:
                file_config = json.load(f)
        else:
            file_config = {}

        # Environment variables override file config
        env_config = {
            'log_level': os.getenv('MY_CLI_LOG_LEVEL'),
            'api_base_url': os.getenv('MY_CLI_API_URL'),
            'enable_analytics': os.getenv('MY_CLI_ANALYTICS', '').lower() == 'true',
        }

        # Remove None values
        env_config = {k: v for k, v in env_config.items() if v is not None}

        # Merge configurations (env > file > defaults)
        merged_config = {**file_config, **env_config}

        return cls(**merged_config)

    def save(self):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.config_dir / "config.json"

        with config_file.open('w') as f:
            json.dump(self.dict(), f, indent=2, default=str)

# Usage in main app
config = AppConfig.load()
app = FastShell("MyCLI", "My CLI application")

@app.command()
def configure(
    log_level: str = "INFO",
    api_url: str = "",
    analytics: bool = False
):
    """Configure application settings"""
    if log_level:
        config.log_level = log_level
    if api_url:
        config.api_base_url = api_url
    config.enable_analytics = analytics

    config.save()
    return "✅ Configuration saved"
```

### Add Logging

```python
import logging
import sys
from pathlib import Path

def setup_logging(config: AppConfig):
    """Setup application logging"""
    # Create log directory
    config.log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=config.log_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set third-party loggers to WARNING
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

# Usage
logger = logging.getLogger(__name__)

@app.command()
async def deploy(environment: str):
    """Deploy with logging"""
    logger.info(f"Starting deployment to {environment}")

    try:
        # Deployment logic
        result = await perform_deployment(environment)
        logger.info(f"Deployment to {environment} completed successfully")
        return f"✅ Deployed to {environment}"

    except Exception as e:
        logger.error(f"Deployment to {environment} failed: {e}")
        return f"❌ Deployment failed: {e}"
```

Following these best practices will help you build robust, maintainable, and user-friendly CLI applications with FastShell. Remember to adapt these patterns to your specific use case and requirements.
