# Documentation Index

Welcome to the Systematic Trading System documentation! This index will help you find the right documentation for your needs.

## Quick Navigation

### 🚀 Getting Started
Start here if you're new to the project:

1. **[README.md](README.md)** - Project overview and features
2. **[SETUP.md](SETUP.md)** - Installation and setup guide (5 minutes)
3. **Run the demo**: `python main.py`

### 📖 User Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [README.md](README.md) | Complete user documentation | Understanding features, usage examples |
| [SETUP.md](SETUP.md) | Step-by-step setup instructions | First-time setup, troubleshooting |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Code snippets and cheat sheet | Quick lookup, copy-paste examples |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | High-level project overview | Understanding scope and capabilities |

### 👨‍💻 Developer Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) | Complete developer guide | Adding features, best practices |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design | Understanding code structure, extending system |

## Documentation by Use Case

### "I want to use the system"

1. Read: [README.md](README.md) - Overview
2. Follow: [SETUP.md](SETUP.md) - Installation
3. Run: `python main.py` - Demo
4. Reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Code examples

### "I want to add a new strategy"

1. Read: [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) → "Adding New Features" → "Adding a New Strategy"
2. See: [strategy/trend_following.py](strategy/trend_following.py) - Example implementations
3. Test: Write tests following [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) → "Testing Guidelines"

### "I want to understand how it works"

1. Start: [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
2. Deep dive: [ARCHITECTURE.md](ARCHITECTURE.md) → "Component Architecture"
3. Code: Read source files in order:
   - [config/settings.py](config/settings.py)
   - [data/data_manager.py](data/data_manager.py)
   - [strategy/base_strategy.py](strategy/base_strategy.py)
   - [backtesting/backtest_engine.py](backtesting/backtest_engine.py)

### "I want to optimize performance"

1. Read: [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) → "Performance Optimization"
2. Profile: Follow profiling examples in developer's guide
3. Reference: [ARCHITECTURE.md](ARCHITECTURE.md) → "Scalability Considerations"

### "Something is broken"

1. Check: [SETUP.md](SETUP.md) → "Troubleshooting"
2. Review: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → "Quick Troubleshooting"
3. Debug: [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) → "Debugging"

## Documentation Structure

```
Documentation/
│
├── User Documentation (Getting Started)
│   ├── README.md              (436 lines) - Main documentation
│   ├── SETUP.md               (215 lines) - Setup instructions
│   ├── QUICK_REFERENCE.md     (288 lines) - Quick lookup
│   └── PROJECT_SUMMARY.md     (233 lines) - Project overview
│
├── Developer Documentation (Advanced)
│   ├── DEVELOPERS_GUIDE.md    (1010 lines) - Development guide
│   └── ARCHITECTURE.md        (567 lines) - System architecture
│
└── This File
    └── INDEX.md               - Documentation index
```

## File Sizes and Complexity

| Document | Lines | Complexity | Reading Time |
|----------|-------|------------|--------------|
| README.md | 436 | Medium | 15 min |
| SETUP.md | 215 | Easy | 10 min |
| QUICK_REFERENCE.md | 288 | Easy | 5 min |
| PROJECT_SUMMARY.md | 233 | Easy | 8 min |
| DEVELOPERS_GUIDE.md | 1010 | Advanced | 30 min |
| ARCHITECTURE.md | 567 | Advanced | 20 min |

## Learning Paths

### Beginner Path
1. [README.md](README.md) → Overview (15 min)
2. [SETUP.md](SETUP.md) → Setup (10 min)
3. Run `python main.py` → See it work (5 min)
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) → Try examples (30 min)

**Total time**: ~1 hour

### Intermediate Path
1. Complete Beginner Path
2. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) → Understand scope (8 min)
3. [ARCHITECTURE.md](ARCHITECTURE.md) → System design (20 min)
4. Modify `.env` and experiment (30 min)
5. Create custom strategy following [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) (1 hour)

**Total time**: ~3 hours

### Advanced Path
1. Complete Intermediate Path
2. [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) → Full read (30 min)
3. [ARCHITECTURE.md](ARCHITECTURE.md) → Deep dive (30 min)
4. Read all source code (2 hours)
5. Implement advanced features (ongoing)

**Total time**: ~6+ hours

## Common Questions → Documentation

| Question | Document | Section |
|----------|----------|---------|
| How do I install? | [SETUP.md](SETUP.md) | Installation |
| How do I run it? | [SETUP.md](SETUP.md) | Quick Start |
| What stocks can I use? | [README.md](README.md) | Common SGX Stocks |
| How do I add more stocks? | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Configuration |
| How do I create a strategy? | [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) | Adding New Features |
| How does backtesting work? | [ARCHITECTURE.md](ARCHITECTURE.md) | Backtesting Module |
| What is EWMAC? | [README.md](README.md) | Key Concepts |
| How is position sizing done? | [ARCHITECTURE.md](ARCHITECTURE.md) | Risk Management |
| How do I run tests? | [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md) | Testing Guidelines |
| What are the design patterns? | [ARCHITECTURE.md](ARCHITECTURE.md) | Design Patterns |

## Documentation Standards

All documentation in this project follows:

- **Markdown format**: Easy to read, render, and version control
- **Clear headings**: Navigate with table of contents
- **Code examples**: Practical, runnable snippets
- **Cross-references**: Links between related docs
- **Consistent structure**: Similar sections across docs

## Contributing to Documentation

When updating documentation:

1. **User docs** (README, SETUP, QUICK_REF): Keep simple, focused on "how to"
2. **Developer docs** (DEVELOPERS_GUIDE, ARCHITECTURE): Include "why" and design decisions
3. **Code examples**: Test them before including
4. **Cross-reference**: Link to related sections
5. **Update index**: Add to this file if creating new docs

## Quick Links

### External Resources
- **Robert Carver's Blog**: https://qoppac.blogspot.com
- **Book**: "Systematic Trading" by Robert Carver
- **Yahoo Finance**: https://finance.yahoo.com
- **SGX**: https://www.sgx.com

### Internal Code
- [Main Demo](main.py)
- [Tests](tests/)
- [Strategy Examples](strategy/trend_following.py)
- [Backtest Engine](backtesting/backtest_engine.py)

## Version Information

**Documentation Version**: 1.0
**Project Version**: 1.0
**Last Updated**: 2025-11-01

## Next Steps

👉 **New User?** Start with [SETUP.md](SETUP.md)
👉 **Developer?** Read [DEVELOPERS_GUIDE.md](DEVELOPERS_GUIDE.md)
👉 **Quick lookup?** Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
👉 **Understanding architecture?** See [ARCHITECTURE.md](ARCHITECTURE.md)

---

**Ready to start?** Run: `python main.py`
