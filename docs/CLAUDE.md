# CLAUDE.md

## Testing
- **Command**: `source venv/bin/activate && pytest`
- **Directory**: `tests/`
- **Philosophy**: 100% test coverage is the goal.
- **Conventions**: 
  - Refer to [TESTING.md](TESTING.md) for detailed guidelines.
  - When writing new functions, write a corresponding test.
  - When fixing a bug, write a regression test.
  - Never commit code that makes existing tests fail.
