# FastShell Documentation

Welcome to the FastShell documentation! FastShell is a modern Python framework for building interactive command-line applications with FastAPI-like syntax.

## 📚 Documentation Overview

### [Getting Started](GETTING_STARTED.md)
New to FastShell? Start here! This guide covers:
- Installation and setup
- Your first FastShell application
- Basic concepts and features
- Running in CLI vs Interactive mode
- Common patterns and next steps

### [API Documentation](API_DOCUMENTATION.md)
Complete reference for all FastShell features:
- Core classes and methods
- Decorators and command registration
- Argument parsing and validation
- Interactive features (syntax highlighting, completion, history)
- System command integration
- Subinstances and nested commands
- Error handling and best practices

### [Examples](EXAMPLES.md)
Real-world examples and use cases:
- Basic utilities (calculator, text processing)
- File management tools
- Development workflow automation
- Cloud management CLI
- Database administration
- API testing tools
- System monitoring utilities

### [Best Practices](BEST_PRACTICES.md)
Production-ready development guidelines:
- Project structure and organization
- Command design principles
- Argument handling patterns
- Error management strategies
- User experience optimization
- Performance considerations
- Testing approaches
- Security practices
- Deployment strategies

## 🚀 Quick Start

```python
from fastshell import FastShell
from pydantic import BaseModel

# Create your application
app = FastShell("MyApp", "My awesome CLI tool")

# Define a command with automatic argument parsing
class UserArgs(BaseModel):
    name: str
    age: int = 25
    active: bool = True

@app.command()
def create_user(args: UserArgs):
    """Create a new user"""
    return f"Created user {args.name}, age {args.age}, active: {args.active}"

# Run the application
if __name__ == "__main__":
    app.run()
```

## ✨ Key Features

- **FastAPI-like Syntax**: Familiar decorator-based command registration
- **Automatic Argument Parsing**: Pydantic integration for type validation
- **Interactive Shell**: Rich terminal experience with syntax highlighting
- **Tab Completion**: Context-aware command and argument completion
- **System Commands**: Seamless integration with system commands
- **Nested Commands**: Organize commands into logical groups
- **Async Support**: Built-in support for async/await operations
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 🎯 Use Cases

FastShell is perfect for:

- **Development Tools**: Build custom CLI tools for your development workflow
- **System Administration**: Create powerful system management utilities
- **Cloud Management**: Build multi-cloud management interfaces
- **Data Processing**: Create interactive data analysis tools
- **API Testing**: Build custom API testing and debugging tools
- **Deployment Automation**: Create deployment and CI/CD tools

## 📖 Learning Path

1. **Start with [Getting Started](GETTING_STARTED.md)** - Learn the basics and create your first application
2. **Explore [Examples](EXAMPLES.md)** - See real-world applications and patterns
3. **Reference [API Documentation](API_DOCUMENTATION.md)** - Deep dive into specific features
4. **Follow [Best Practices](BEST_PRACTICES.md)** - Build production-ready applications

## 🔧 Advanced Topics

### Interactive Features
- Syntax highlighting with customizable colors
- Tab completion for commands, arguments, and file paths
- Command history with search
- Built-in help system with automatic documentation

### System Integration
- Persistent shell context for system commands
- Cross-platform command execution
- Interactive command support (vim, python, etc.)
- Directory and environment variable persistence

### Extensibility
- Plugin architecture through subinstances
- Custom validators and type converters
- Configurable output formatting
- Integration with external APIs and services

## 🤝 Contributing

FastShell is designed to be extensible and community-friendly. Whether you're:
- Building applications with FastShell
- Contributing to the framework
- Creating plugins and extensions
- Improving documentation

We welcome your contributions and feedback!

## 📝 License

FastShell is released under the MIT License. See the LICENSE file for details.

## 🆘 Support

- **Documentation**: You're reading it! Check the guides above
- **Examples**: See the [Examples](EXAMPLES.md) section for real-world use cases
- **Best Practices**: Follow the [Best Practices](BEST_PRACTICES.md) guide for production apps

---

**Happy coding with FastShell!** 🚀

Build powerful, interactive command-line applications with the simplicity of FastAPI and the richness of modern terminal interfaces.