# Contributing to HelloStockBuy

Thank you for your interest in contributing to HelloStockBuy! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Basic knowledge of Python, JavaScript/TypeScript, and Vue.js
- Understanding of financial markets and trading concepts

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/hellostockbuy.git`
3. Set up the development environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   docker compose up -d
   ```

## 📋 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Provide detailed information about the problem
- Include steps to reproduce the issue
- Attach relevant logs or screenshots

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its benefits
- Consider the impact on existing functionality

### Code Contributions
1. Create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## 🛠️ Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

#### JavaScript/TypeScript (Frontend)
- Use ESLint configuration
- Follow Vue.js style guide
- Use TypeScript for type safety
- Write meaningful variable and function names

### Testing
- Write unit tests for new features
- Test edge cases and error conditions
- Ensure tests are fast and reliable
- Maintain good test coverage

### Documentation
- Update README.md for significant changes
- Add inline comments for complex logic
- Update API documentation for new endpoints
- Include examples in documentation

## 🏗️ Project Structure

```
hellostockbuy/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application
│   ├── models.py     # Database models
│   ├── services/     # Business logic
│   └── tests/        # Backend tests
├── frontend/         # Nuxt.js frontend
│   ├── pages/        # Vue pages
│   ├── components/   # Vue components
│   └── assets/       # Static assets
├── db/               # Database files
├── docker-compose.yml
└── README.md
```

## 🔧 Development Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation updates

### Commit Messages
Use clear, descriptive commit messages:
```
feat: add portfolio analysis dashboard
fix: resolve IBKR connection timeout issue
docs: update API documentation
test: add unit tests for market data service
```

### Pull Request Process
1. Ensure your branch is up to date with `main`
2. Run tests and ensure they pass
3. Update documentation if needed
4. Request review from maintainers
5. Address feedback and make necessary changes
6. Squash commits if requested

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
pnpm test
```

### Integration Testing
```bash
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📊 Performance Considerations

- Optimize database queries
- Use caching where appropriate
- Minimize API calls
- Consider memory usage
- Profile performance-critical code

## 🔒 Security Guidelines

- Never commit sensitive information (API keys, passwords)
- Validate all user inputs
- Use parameterized queries
- Follow OWASP security guidelines
- Keep dependencies updated

## 🌐 Internationalization

- Use translation keys for user-facing text
- Support multiple languages
- Test with different locales
- Consider RTL languages if needed

## 📈 Financial Data Handling

- Ensure data accuracy and integrity
- Handle market hours and holidays
- Implement proper error handling for API failures
- Consider rate limiting and quotas
- Validate financial calculations

## 🤝 Code Review Process

### For Contributors
- Respond to feedback promptly
- Be open to suggestions
- Ask questions if something is unclear
- Test your changes thoroughly

### For Reviewers
- Be constructive and respectful
- Focus on code quality and functionality
- Check for security issues
- Ensure tests are adequate

## 📝 Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release notes
4. Tag the release
5. Deploy to production

## 🆘 Getting Help

- Check existing issues and discussions
- Join our community discussions
- Contact maintainers for urgent issues
- Use the issue tracker for questions

## 📋 Checklist for Contributors

Before submitting a pull request, ensure:

- [ ] Code follows style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] No sensitive information is included
- [ ] Changes are backward compatible
- [ ] Performance impact is considered
- [ ] Security implications are reviewed

## 🎯 Areas for Contribution

### High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Security enhancements
- Test coverage improvements

### Medium Priority
- New features and functionality
- UI/UX improvements
- Documentation updates
- Internationalization

### Low Priority
- Code refactoring
- Developer experience improvements
- Additional integrations
- Advanced analytics features

## 📜 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Respect different perspectives
- Follow community guidelines

## 🏆 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation
- Community acknowledgments

Thank you for contributing to HelloStockBuy! 🚀
