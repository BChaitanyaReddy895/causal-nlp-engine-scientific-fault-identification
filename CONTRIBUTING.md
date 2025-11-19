# Contributing to Causal-NLP Engine

Thank you for your interest in contributing to the Causal-NLP Engine project! We welcome contributions from researchers, engineers, and enthusiasts.

## Code of Conduct

This project adheres to the Contributor Covenant Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs
- **Use the issue tracker** to report bugs
- Include a clear description of the problem
- Provide examples to demonstrate the issue
- Include screenshots if applicable
- Note your OS and Python version

### Suggesting Enhancements
- Use the issue tracker for enhancement suggestions
- Provide a clear description of the feature
- Explain why this enhancement would be useful
- List some alternative implementations you've considered

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`make test`)
6. Commit with clear messages (`git commit -m 'Add amazing feature'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request describing your changes

## Development Setup

```bash
git clone https://github.com/yourusername/causal-nlp-claim-verifier.git
cd causal-nlp-claim-verifier
make setup
make dev
```

## Coding Standards

- Follow PEP 8 for Python code
- Use type hints where applicable
- Write docstrings for all functions and classes
- Keep functions focused and modular
- Write tests for all new features

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_extractor.py

# Run with coverage
pytest --cov=backend tests/
```

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Refactor, etc.)
- Reference issues when applicable: "Fix #123"
- Keep messages concise but informative

Example:
```
Add UMLS entity canonicalization to KG manager

- Implement mapping of medical entity terms to UMLS IDs
- Add unit tests for canonicalization function
- Fixes #42
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions
- Update docs/ for architectural changes
- Include examples in docstrings

## Questions?

Feel free to open an issue with the label `question` if you're unsure about anything.

Thank you for contributing! 🙏
