# Contributing to System Monitor

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/system-monitor.git`
3. Create a branch: `git checkout -b feature-name`
4. Make your changes
5. Run tests: `python -m pytest test_monitor.py`
6. Submit a pull request

## Development Setup

Install dependencies:
```bash
pip install -r requirements.txt
pip install ruff pytest coverage
```

## Code Style

- Follow PEP 8 guidelines
- Use Ruff for linting: `ruff check .`
- Write tests for new features
- Handle errors gracefully

## Testing

```bash
# Run all tests
python -m pytest test_monitor.py -v

# Test functionality
python system_monitor.py --test

# Check coverage
coverage run -m pytest test_monitor.py
coverage report -m
```

## Security Considerations

- Never commit sensitive system information
- Validate configuration inputs
- Handle subprocess calls safely
- Test with different permission levels

## Pull Request Guidelines

- Include a clear description of changes
- Add tests for new functionality
- Update documentation if needed
- Ensure all tests pass

## Questions?

Open an issue or contact: wcloutman@hotmail.com