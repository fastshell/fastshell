<!--
 Copyright (c) 2026 github.com/fastshell

 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
-->

# FastShell Examples

This document provides comprehensive examples of FastShell applications, from simple utilities to complex multi-command tools.

## Table of Contents

- [Basic Examples](#basic-examples)
- [File Management Tool](#file-management-tool)
- [Development Tools CLI](#development-tools-cli)
- [Cloud Management CLI](#cloud-management-cli)
- [Database Administration Tool](#database-administration-tool)
- [API Testing Tool](#api-testing-tool)
- [System Monitoring Tool](#system-monitoring-tool)
- [Git Workflow Helper](#git-workflow-helper)

## Basic Examples

### Simple Calculator

```python
from fastshell import FastShell
from pydantic import BaseModel

app = FastShell("Calculator", "Simple command-line calculator")

class MathArgs(BaseModel):
    a: float
    b: float

@app.command()
def add(args: MathArgs):
    """Add two numbers"""
    return f"{args.a} + {args.b} = {args.a + args.b}"

@app.command()
def subtract(args: MathArgs):
    """Subtract two numbers"""
    return f"{args.a} - {args.b} = {args.a - args.b}"

@app.command()
def multiply(args: MathArgs):
    """Multiply two numbers"""
    return f"{args.a} × {args.b} = {args.a * args.b}"

@app.command()
def divide(args: MathArgs):
    """Divide two numbers"""
    if args.b == 0:
        return "Error: Division by zero"
    return f"{args.a} ÷ {args.b} = {args.a / args.b}"

if __name__ == "__main__":
    app.run()
```

Usage:

```bash
python calculator.py add 5.5 3.2
python calculator.py multiply --a 4 --b 7
```

### Text Processing Tool

```python
import re
from pathlib import Path
from fastshell import FastShell
from pydantic import BaseModel, Field

app = FastShell("TextTool", "Text processing utilities")

class FileArgs(BaseModel):
    file_path: str = Field(description="Path to the text file")

class SearchArgs(BaseModel):
    pattern: str = Field(description="Search pattern (regex)")
    file_path: str = Field(description="Path to the text file")
    ignore_case: bool = Field(default=False, description="Ignore case in search")

@app.command()
def count_words(args: FileArgs):
    """Count words in a text file"""
    try:
        content = Path(args.file_path).read_text(encoding='utf-8')
        word_count = len(content.split())
        line_count = len(content.splitlines())
        char_count = len(content)

        return f"""File: {args.file_path}
Words: {word_count}
Lines: {line_count}
Characters: {char_count}"""
    except FileNotFoundError:
        return f"Error: File '{args.file_path}' not found"
    except Exception as e:
        return f"Error reading file: {e}"

@app.command()
def search(args: SearchArgs):
    """Search for pattern in text file"""
    try:
        content = Path(args.file_path).read_text(encoding='utf-8')
        flags = re.IGNORECASE if args.ignore_case else 0
        matches = re.finditer(args.pattern, content, flags)

        results = []
        for i, match in enumerate(matches, 1):
            line_num = content[:match.start()].count('\n') + 1
            results.append(f"Match {i}: Line {line_num}, Position {match.start()}")
            results.append(f"  Text: {match.group()}")

        if results:
            return "\n".join(results)
        else:
            return f"No matches found for pattern '{args.pattern}'"

    except re.error as e:
        return f"Invalid regex pattern: {e}"
    except FileNotFoundError:
        return f"Error: File '{args.file_path}' not found"
    except Exception as e:
        return f"Error: {e}"

@app.command()
def replace_text(file_path: str, find: str, replace: str, backup: bool = True):
    """Replace text in a file"""
    try:
        file_obj = Path(file_path)
        content = file_obj.read_text(encoding='utf-8')

        if backup:
            backup_path = file_obj.with_suffix(file_obj.suffix + '.bak')
            backup_path.write_text(content, encoding='utf-8')

        new_content = content.replace(find, replace)
        count = content.count(find)

        file_obj.write_text(new_content, encoding='utf-8')

        result = f"Replaced {count} occurrences of '{find}' with '{replace}'"
        if backup:
            result += f"\nBackup saved as: {backup_path}"
        return result

    except FileNotFoundError:
        return f"Error: File '{file_path}' not found"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    app.run()
```

## File Management Tool

```python
import shutil
import os
from pathlib import Path
from datetime import datetime
from fastshell import FastShell
from pydantic import BaseModel, Field

app = FastShell("FileManager", "Advanced file management tool")

class CopyArgs(BaseModel):
    source: str = Field(description="Source file or directory")
    destination: str = Field(description="Destination path")
    recursive: bool = Field(default=False, description="Copy directories recursively")
    preserve_metadata: bool = Field(default=True, description="Preserve file metadata")

class FindArgs(BaseModel):
    directory: str = Field(default=".", description="Directory to search in")
    name_pattern: str = Field(default="*", description="File name pattern")
    min_size: int = Field(default=0, description="Minimum file size in bytes")
    max_size: int = Field(default=0, description="Maximum file size in bytes (0 = no limit)")
    modified_days: int = Field(default=0, description="Files modified within N days (0 = any)")

@app.command()
def copy(args: CopyArgs):
    """Copy files or directories with advanced options"""
    try:
        source_path = Path(args.source)
        dest_path = Path(args.destination)

        if not source_path.exists():
            return f"Error: Source '{args.source}' does not exist"

        if source_path.is_file():
            if args.preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            return f"File copied: {args.source} → {args.destination}"

        elif source_path.is_dir():
            if not args.recursive:
                return "Error: Use --recursive flag to copy directories"

            if args.preserve_metadata:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            else:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True, copy_function=shutil.copy)
            return f"Directory copied: {args.source} → {args.destination}"

    except Exception as e:
        return f"Error copying: {e}"

@app.command()
def find_files(args: FindArgs):
    """Find files with advanced filtering"""
    try:
        search_path = Path(args.directory)
        if not search_path.exists():
            return f"Error: Directory '{args.directory}' does not exist"

        results = []
        now = datetime.now()

        for file_path in search_path.rglob(args.name_pattern):
            if not file_path.is_file():
                continue

            # Size filtering
            file_size = file_path.stat().st_size
            if args.min_size > 0 and file_size < args.min_size:
                continue
            if args.max_size > 0 and file_size > args.max_size:
                continue

            # Modified time filtering
            if args.modified_days > 0:
                modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                days_diff = (now - modified_time).days
                if days_diff > args.modified_days:
                    continue

            # Format file info
            size_mb = file_size / (1024 * 1024)
            modified = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            results.append(f"{file_path} ({size_mb:.2f} MB, modified: {modified})")

        if results:
            return f"Found {len(results)} files:\n" + "\n".join(results)
        else:
            return "No files found matching criteria"

    except Exception as e:
        return f"Error searching: {e}"

@app.command()
def disk_usage(directory: str = ".", depth: int = 1):
    """Show disk usage for directories"""
    try:
        path = Path(directory)
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"

        def get_size(path):
            if path.is_file():
                return path.stat().st_size
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} PB"

        results = []
        total_size = 0

        if depth == 0:
            size = get_size(path)
            return f"{directory}: {format_size(size)}"

        for item in sorted(path.iterdir()):
            if item.is_dir():
                size = get_size(item)
                total_size += size
                results.append(f"{item.name}/: {format_size(size)}")
            elif depth == 1:  # Include files at depth 1
                size = item.stat().st_size
                total_size += size
                results.append(f"{item.name}: {format_size(size)}")

        results.insert(0, f"Total in {directory}: {format_size(total_size)}")
        results.insert(1, "-" * 40)

        return "\n".join(results)

    except Exception as e:
        return f"Error calculating disk usage: {e}"

@app.command()
def cleanup(directory: str = ".", dry_run: bool = True):
    """Clean up temporary and cache files"""
    try:
        path = Path(directory)
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"

        # Patterns for files to clean up
        cleanup_patterns = [
            "*.tmp", "*.temp", "*.log", "*.cache",
            "*.pyc", "__pycache__", ".DS_Store",
            "Thumbs.db", "*.bak", "*.swp", "*.swo"
        ]

        files_to_delete = []
        total_size = 0

        for pattern in cleanup_patterns:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    files_to_delete.append((file_path, size))
                    total_size += size
                elif file_path.is_dir() and pattern == "__pycache__":
                    # Calculate directory size
                    dir_size = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
                    files_to_delete.append((file_path, dir_size))
                    total_size += dir_size

        if not files_to_delete:
            return "No temporary files found to clean up"

        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"

        result = f"Found {len(files_to_delete)} items to clean up ({format_size(total_size)} total)\n"

        if dry_run:
            result += "\nDry run - files that would be deleted:\n"
            for file_path, size in files_to_delete[:10]:  # Show first 10
                result += f"  {file_path} ({format_size(size)})\n"
            if len(files_to_delete) > 10:
                result += f"  ... and {len(files_to_delete) - 10} more\n"
            result += "\nUse --dry-run false to actually delete these files"
        else:
            deleted_count = 0
            for file_path, size in files_to_delete:
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                    deleted_count += 1
                except Exception as e:
                    result += f"Error deleting {file_path}: {e}\n"

            result += f"\nDeleted {deleted_count} items, freed {format_size(total_size)}"

        return result

    except Exception as e:
        return f"Error during cleanup: {e}"

if __name__ == "__main__":
    app.run()
```

## Development Tools CLI

```python
import subprocess
import json
import asyncio
from pathlib import Path
from fastshell import FastShell
from pydantic import BaseModel, Field

app = FastShell("DevTools", "Development workflow automation")

# Git subinstance
git = app.subinstance("git", "Git workflow helpers")

class CommitArgs(BaseModel):
    message: str = Field(description="Commit message")
    add_all: bool = Field(default=False, description="Add all changes before commit")
    push: bool = Field(default=False, description="Push after commit")

@git.command()
async def smart_commit(args: CommitArgs):
    """Smart commit with automatic checks"""
    try:
        # Add files if requested
        if args.add_all:
            result = await asyncio.create_subprocess_exec(
                "git", "add", ".",
                capture_output=True, text=True
            )
            await result.wait()

        # Check for staged changes
        result = await asyncio.create_subprocess_exec(
            "git", "diff", "--cached", "--quiet",
            capture_output=True
        )
        await result.wait()

        if result.returncode != 0:  # There are staged changes
            # Commit
            commit_result = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", args.message,
                capture_output=True, text=True
            )
            await commit_result.wait()

            if commit_result.returncode == 0:
                output = "✓ Commit successful"

                # Push if requested
                if args.push:
                    push_result = await asyncio.create_subprocess_exec(
                        "git", "push",
                        capture_output=True, text=True
                    )
                    await push_result.wait()

                    if push_result.returncode == 0:
                        output += "\n✓ Push successful"
                    else:
                        output += f"\n✗ Push failed: {push_result.stderr}"

                return output
            else:
                return f"✗ Commit failed: {commit_result.stderr}"
        else:
            return "No staged changes to commit"

    except Exception as e:
        return f"Error: {e}"

@git.command()
async def status():
    """Enhanced git status with branch info"""
    try:
        # Get current branch
        branch_result = await asyncio.create_subprocess_exec(
            "git", "branch", "--show-current",
            capture_output=True, text=True
        )
        await branch_result.wait()
        current_branch = branch_result.stdout.strip()

        # Get status
        status_result = await asyncio.create_subprocess_exec(
            "git", "status", "--porcelain",
            capture_output=True, text=True
        )
        await status_result.wait()

        output = f"Branch: {current_branch}\n"

        if status_result.stdout:
            output += "Changes:\n"
            for line in status_result.stdout.strip().split('\n'):
                status_code = line[:2]
                filename = line[3:]

                if status_code == "??":
                    output += f"  🆕 {filename} (untracked)\n"
                elif status_code[0] == "M":
                    output += f"  📝 {filename} (modified)\n"
                elif status_code[0] == "A":
                    output += f"  ➕ {filename} (added)\n"
                elif status_code[0] == "D":
                    output += f"  ❌ {filename} (deleted)\n"
                else:
                    output += f"  📄 {filename} ({status_code})\n"
        else:
            output += "✓ Working directory clean"

        return output

    except Exception as e:
        return f"Error: {e}"

# Docker subinstance
docker = app.subinstance("docker", "Docker development helpers")

class BuildArgs(BaseModel):
    tag: str = Field(description="Image tag")
    dockerfile: str = Field(default="Dockerfile", description="Dockerfile path")
    context: str = Field(default=".", description="Build context")
    no_cache: bool = Field(default=False, description="Don't use cache")

@docker.command()
async def build(args: BuildArgs):
    """Build Docker image with progress"""
    try:
        cmd = ["docker", "build", "-t", args.tag, "-f", args.dockerfile]

        if args.no_cache:
            cmd.append("--no-cache")

        cmd.append(args.context)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            text=True
        )

        output_lines = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line:
                output_lines.append(line)
                # Show progress for key steps
                if any(keyword in line.lower() for keyword in ["step", "successfully built", "error"]):
                    print(f"🐳 {line}")

        await process.wait()

        if process.returncode == 0:
            return f"✓ Successfully built image: {args.tag}"
        else:
            return f"✗ Build failed\n" + "\n".join(output_lines[-10:])  # Last 10 lines

    except Exception as e:
        return f"Error: {e}"

@docker.command()
async def run_dev(image: str, port: int = 8000, volume: str = ""):
    """Run container in development mode"""
    try:
        cmd = ["docker", "run", "--rm", "-it", "-p", f"{port}:8000"]

        if volume:
            cmd.extend(["-v", f"{volume}:/app"])

        cmd.append(image)

        # This will run interactively
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()

        return f"Container {image} finished"

    except Exception as e:
        return f"Error: {e}"

# Testing subinstance
test = app.subinstance("test", "Testing utilities")

class TestArgs(BaseModel):
    pattern: str = Field(default="test_*.py", description="Test file pattern")
    verbose: bool = Field(default=False, description="Verbose output")
    coverage: bool = Field(default=False, description="Run with coverage")
    parallel: bool = Field(default=False, description="Run tests in parallel")

@test.command()
async def run(args: TestArgs):
    """Run tests with various options"""
    try:
        if args.coverage:
            cmd = ["python", "-m", "pytest", "--cov=.", "--cov-report=term-missing"]
        else:
            cmd = ["python", "-m", "pytest"]

        if args.verbose:
            cmd.append("-v")

        if args.parallel:
            cmd.extend(["-n", "auto"])

        cmd.append(args.pattern)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            text=True
        )

        output = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if line:
                output.append(line)
                # Show real-time progress
                if any(keyword in line for keyword in ["PASSED", "FAILED", "ERROR", "collected"]):
                    print(f"🧪 {line}")

        await process.wait()

        # Summary
        if process.returncode == 0:
            return "✓ All tests passed!"
        else:
            failed_lines = [line for line in output if "FAILED" in line]
            return f"✗ Tests failed\n" + "\n".join(failed_lines)

    except Exception as e:
        return f"Error running tests: {e}"

@test.command()
def lint(fix: bool = False):
    """Run code linting"""
    try:
        tools = [
            ("black", ["black", "." if not fix else "--check", "."]),
            ("isort", ["isort", "." if not fix else "--check-only", "."]),
            ("flake8", ["flake8", "."]),
        ]

        results = []
        for tool_name, cmd in tools:
            try:
                if not fix and tool_name in ["black", "isort"]:
                    cmd = [cmd[0], "--check", "."]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    results.append(f"✓ {tool_name}: OK")
                else:
                    results.append(f"✗ {tool_name}: Issues found")
                    if result.stdout:
                        results.append(f"  {result.stdout[:200]}...")

            except FileNotFoundError:
                results.append(f"⚠ {tool_name}: Not installed")

        return "\n".join(results)

    except Exception as e:
        return f"Error running linting: {e}"

if __name__ == "__main__":
    app.run()
```

## Cloud Management CLI

```python
import json
import asyncio
from datetime import datetime
from fastshell import FastShell
from pydantic import BaseModel, Field

app = FastShell("CloudCLI", "Multi-cloud management tool")

# AWS subinstance
aws = app.subinstance("aws", "Amazon Web Services")
ec2 = aws.subinstance("ec2", "EC2 instance management")
s3 = aws.subinstance("s3", "S3 bucket management")

class EC2ListArgs(BaseModel):
    region: str = Field(default="us-east-1", description="AWS region")
    state: str = Field(default="all", description="Instance state filter")
    tag_filter: str = Field(default="", description="Tag filter (key=value)")

@ec2.command()
async def list_instances(args: EC2ListArgs):
    """List EC2 instances with filtering"""
    # Simulate AWS API call
    await asyncio.sleep(0.5)

    instances = [
        {
            "id": "i-1234567890abcdef0",
            "name": "web-server-1",
            "type": "t3.medium",
            "state": "running",
            "ip": "54.123.45.67",
            "launch_time": "2023-12-01T10:30:00Z"
        },
        {
            "id": "i-0987654321fedcba0",
            "name": "database-server",
            "type": "r5.large",
            "state": "stopped",
            "ip": "54.123.45.68",
            "launch_time": "2023-11-28T14:15:00Z"
        }
    ]

    # Apply state filter
    if args.state != "all":
        instances = [i for i in instances if i["state"] == args.state]

    if not instances:
        return f"No instances found in {args.region} with state '{args.state}'"

    # Format output
    output = [f"EC2 Instances in {args.region}:"]
    output.append("-" * 60)

    for instance in instances:
        status_emoji = "🟢" if instance["state"] == "running" else "🔴"
        output.append(f"{status_emoji} {instance['name']} ({instance['id']})")
        output.append(f"   Type: {instance['type']}, IP: {instance['ip']}")
        output.append(f"   State: {instance['state']}, Launched: {instance['launch_time']}")
        output.append("")

    return "\n".join(output)

class EC2ActionArgs(BaseModel):
    instance_id: str = Field(description="Instance ID")
    region: str = Field(default="us-east-1", description="AWS region")

@ec2.command()
async def start_instance(args: EC2ActionArgs):
    """Start an EC2 instance"""
    await asyncio.sleep(1)  # Simulate API call
    return f"✓ Starting instance {args.instance_id} in {args.region}"

@ec2.command()
async def stop_instance(args: EC2ActionArgs):
    """Stop an EC2 instance"""
    await asyncio.sleep(1)  # Simulate API call
    return f"✓ Stopping instance {args.instance_id} in {args.region}"

class S3ListArgs(BaseModel):
    prefix: str = Field(default="", description="Object prefix filter")
    max_keys: int = Field(default=100, description="Maximum number of objects")

@s3.command()
async def list_buckets():
    """List all S3 buckets"""
    await asyncio.sleep(0.3)

    buckets = [
        {"name": "my-app-assets", "created": "2023-10-15", "region": "us-east-1"},
        {"name": "backup-storage", "created": "2023-09-20", "region": "us-west-2"},
        {"name": "logs-archive", "created": "2023-11-01", "region": "eu-west-1"}
    ]

    output = ["S3 Buckets:"]
    output.append("-" * 40)

    for bucket in buckets:
        output.append(f"📦 {bucket['name']}")
        output.append(f"   Created: {bucket['created']}, Region: {bucket['region']}")

    return "\n".join(output)

@s3.command()
async def list_objects(bucket: str, args: S3ListArgs):
    """List objects in an S3 bucket"""
    await asyncio.sleep(0.5)

    # Simulate objects
    objects = [
        {"key": "images/logo.png", "size": 15420, "modified": "2023-12-01T09:30:00Z"},
        {"key": "css/styles.css", "size": 8932, "modified": "2023-12-01T10:15:00Z"},
        {"key": "js/app.js", "size": 45678, "modified": "2023-12-01T11:00:00Z"}
    ]

    # Apply prefix filter
    if args.prefix:
        objects = [obj for obj in objects if obj["key"].startswith(args.prefix)]

    # Apply max_keys limit
    objects = objects[:args.max_keys]

    if not objects:
        return f"No objects found in bucket '{bucket}' with prefix '{args.prefix}'"

    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    output = [f"Objects in bucket '{bucket}':"]
    output.append("-" * 50)

    total_size = 0
    for obj in objects:
        size_str = format_size(obj["size"])
        total_size += obj["size"]
        output.append(f"📄 {obj['key']}")
        output.append(f"   Size: {size_str}, Modified: {obj['modified']}")

    output.append("-" * 50)
    output.append(f"Total: {len(objects)} objects, {format_size(total_size)}")

    return "\n".join(output)

# Azure subinstance
azure = app.subinstance("azure", "Microsoft Azure")
vm = azure.subinstance("vm", "Virtual Machine management")

@vm.command()
async def list_vms(resource_group: str, subscription: str = "default"):
    """List Azure Virtual Machines"""
    await asyncio.sleep(0.7)

    vms = [
        {
            "name": "web-vm-01",
            "size": "Standard_B2s",
            "state": "running",
            "location": "East US",
            "os": "Ubuntu 20.04"
        },
        {
            "name": "db-vm-01",
            "size": "Standard_D4s_v3",
            "state": "stopped",
            "location": "West US 2",
            "os": "Windows Server 2019"
        }
    ]

    output = [f"Virtual Machines in resource group '{resource_group}':"]
    output.append("-" * 60)

    for vm_info in vms:
        status_emoji = "🟢" if vm_info["state"] == "running" else "🔴"
        os_emoji = "🐧" if "Ubuntu" in vm_info["os"] else "🪟"

        output.append(f"{status_emoji} {vm_info['name']} ({vm_info['size']})")
        output.append(f"   {os_emoji} {vm_info['os']}")
        output.append(f"   Location: {vm_info['location']}, State: {vm_info['state']}")
        output.append("")

    return "\n".join(output)

# Multi-cloud commands
@app.command()
async def cost_summary(cloud: str = "all", period: str = "month"):
    """Get cost summary across cloud providers"""
    await asyncio.sleep(1)

    costs = {
        "aws": {"compute": 245.67, "storage": 89.23, "network": 34.12},
        "azure": {"compute": 189.45, "storage": 67.89, "network": 28.76},
        "gcp": {"compute": 156.78, "storage": 45.67, "network": 23.45}
    }

    output = [f"Cloud Cost Summary ({period}):"]
    output.append("=" * 40)

    total_cost = 0

    for provider, categories in costs.items():
        if cloud != "all" and cloud != provider:
            continue

        provider_total = sum(categories.values())
        total_cost += provider_total

        output.append(f"\n{provider.upper()}:")
        output.append(f"  Compute: ${categories['compute']:.2f}")
        output.append(f"  Storage: ${categories['storage']:.2f}")
        output.append(f"  Network: ${categories['network']:.2f}")
        output.append(f"  Total:   ${provider_total:.2f}")

    output.append("-" * 40)
    output.append(f"Grand Total: ${total_cost:.2f}")

    return "\n".join(output)

if __name__ == "__main__":
    app.run()
```

These examples demonstrate the power and flexibility of FastShell for building complex command-line applications. Each example shows different patterns:

1. **Basic Examples**: Simple utilities with straightforward commands
2. **File Management**: Complex file operations with validation and error handling
3. **Development Tools**: Async operations, subprocess management, and workflow automation
4. **Cloud Management**: Nested subinstances, API simulation, and structured output

The examples progress from simple to complex, showing how FastShell scales from basic scripts to enterprise-level CLI tools. Each demonstrates best practices for argument handling, error management, and user experience.
