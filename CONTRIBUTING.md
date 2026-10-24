# Contributing to mcp-scotty

Thank you for your interest in contributing to mcp-scotty! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/mcp-scotty.git
   cd mcp-scotty
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Write clear, readable code
- Follow the existing code style
- Add comments where necessary
- Update documentation as needed

### 3. Code Formatting

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black src/

# Check linting
ruff check src/

# Auto-fix linting issues
ruff check --fix src/
```

### 4. Testing

Run tests to ensure your changes don't break existing functionality:

```bash
pytest
```

If you add new features, please include tests for them.

### 5. Commit Your Changes

Write clear commit messages following these guidelines:

```bash
git add .
git commit -m "feat: add support for real-time delay information"
# or
git commit -m "fix: correct station search for special characters"
# or
git commit -m "docs: update installation instructions"
```

Commit message prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### 6. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference any related issues
- Explain what changes you made and why

## What to Contribute

### Bug Reports

If you find a bug:
1. Check if it's already reported in Issues
2. If not, create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, etc.)
   - Error messages or logs

### Feature Requests

For new features:
1. Open an issue to discuss the feature first
2. Explain the use case and benefits
3. Wait for feedback before implementing

### Code Contributions

Areas where contributions are especially welcome:

- **ÖBB-specific HAFAS profile**: Currently using DB profile; help create a proper ÖBB profile
- **Additional tools**: Trip tracking, fare information, station facilities
- **Error handling**: Improve error messages and handling
- **Tests**: Add comprehensive test coverage
- **Documentation**: Examples, tutorials, translations
- **Performance**: Optimize API calls and response formatting

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Example:

```python
async def search_stations(arguments: dict) -> list[TextContent]:
    """Search for train stations.

    Args:
        arguments: Dictionary containing search parameters

    Returns:
        List of TextContent objects with search results
    """
    query = arguments["query"]
    max_results = arguments.get("max_results", 10)

    # Implementation...
```

### Documentation

- Add docstrings to all functions and classes
- Update README.md for user-facing changes
- Add comments for complex logic
- Keep documentation in sync with code

## MCP Protocol Considerations

When adding new tools:

1. **Define the tool** in `list_tools()`:
   ```python
   Tool(
       name="tool_name",
       description="Clear description of what the tool does",
       inputSchema={...}
   )
   ```

2. **Implement the handler** in `call_tool()`:
   ```python
   elif name == "tool_name":
       return await handle_tool_name(arguments)
   ```

3. **Create the async function**:
   ```python
   async def handle_tool_name(arguments: dict) -> list[TextContent]:
       # Implementation
       pass
   ```

4. **Format responses clearly**:
   - Use Markdown for structure
   - Include all relevant information
   - Handle errors gracefully

## Testing Guidelines

### Writing Tests

Create test files in a `tests/` directory:

```python
import pytest
from scottymcp.server import search_stations

@pytest.mark.asyncio
async def test_search_stations():
    arguments = {"query": "Wien", "max_results": 5}
    result = await search_stations(arguments)
    assert len(result) > 0
    assert result[0].type == "text"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_server.py

# Run with coverage
pytest --cov=scottymcp
```

## Documentation

### README Updates

Update the README when adding:
- New features or tools
- Configuration options
- Usage examples

### Code Comments

Add comments for:
- Complex algorithms
- Non-obvious behavior
- Workarounds
- TODO items

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Review the MCP documentation at https://modelcontextprotocol.io/

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Recognition

Contributors will be recognized in the README and release notes. Thank you for helping make mcp-scotty better!
