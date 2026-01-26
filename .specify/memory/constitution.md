<!--
## Sync Impact Report

Version change: N/A → v1.0.0 (Initial creation)

Modified principles: N/A (Initial creation)

Added sections:
- Core Principles (6 principles)
- Code Quality Standards
- Development Workflow
- Governance

Removed sections: N/A

Templates requiring updates:
- .specify/templates/plan-template.md: ✅ Updated (Constitution Check section populated with principles)
- .specify/templates/spec-template.md: ✅ Compatible (no changes required)
- .specify/templates/tasks-template.md: ✅ Compatible (no changes required)

Follow-up TODOs: None
-->

# destep-py Constitution

## Core Principles

### I. Modern Python Syntax (NON-NEGOTIABLE)

All code MUST use Python 3.12+ features and modern syntax conventions:
- Use `X | Y` for type unions (NOT `Union[X, Y]`)
- Use `list[T]`, `dict[K, V]` for generic types (NOT `List[T]`, `Dict[K, V]`)
- Use `from __future__ import annotations` only when absolutely necessary
- Use Pydantic for data validation with `ConfigDict` pattern

**Rationale**: Modern syntax improves readability, reduces imports, and leverages interpreter optimizations.

### II. No Over-Abstraction (NON-NEGOTIABLE)

Code MUST avoid unnecessary wrappers and abstractions:
- Use standard library and third-party library APIs directly
- Create abstractions ONLY when: logic is complex AND needs reuse, unified interface is required (e.g., Converter base class), or state management is involved
- Each function/class MUST have a single, clear purpose—no organizational-only abstractions

**Rationale**: Over-abstraction hides behavior, increases cognitive load, and makes debugging harder.

### III. SOTA Libraries First (NON-NEGOTIABLE)

Development MUST prioritize established libraries over custom implementations:
- Search Papers with Code, GitHub, Hugging Face Hub before implementing
- Use: `transformers` for NLP, `timm` for vision, `accelerate` for distributed training
- Use: `Pydantic` for validation, `loguru` for logging, `OmegaConf` for config, `Typer` for CLI
- Custom implementation ONLY when no suitable library exists OR specific requirements cannot be met

**Rationale**: Mature libraries are tested, optimized, and maintained by the community.

### IV. Clean Code Without Inline Comments (NON-NEGOTIABLE)

Code MUST be self-documenting:
- NO inline comments (e.g., `# do something`)—code should explain itself through naming
- Docstrings (Google style, English) ONLY for complex functions with non-obvious behavior
- Variable and function names MUST be descriptive and meaningful
- Complex logic MUST be broken into well-named helper functions

**Rationale**: Inline comments become outdated, while descriptive code remains accurate.

### V. Conventional Commits (NON-NEGOTIABLE)

All Git commits MUST follow Conventional Commits format:
- Format: `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `chore`
- Scope: module or component affected (e.g., `converter`, `validator`)
- Description: imperative mood, lowercase, no period

**Rationale**: Consistent commit history enables automated changelogs and semantic versioning.

### VI. Fail-Fast Exception Handling

Code SHOULD throw exceptions early and let callers handle them:
- Validate inputs at function entry points
- Raise specific exceptions with clear error messages
- Avoid silent failures or generic catch-all handlers
- Include context in error messages (file paths, values, expected vs actual)

**Rationale**: Early failures are easier to debug than propagated silent errors.

## Code Quality Standards

### Tooling Requirements

- **Linting/Formatting**: `ruff` with configured rules (E, W, F, I, B, C4, UP, SIM, RUF, N)
- **Line length**: 88 characters maximum
- **Quote style**: double quotes
- **Indent style**: spaces (4 spaces)

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables/Functions | snake_case | `user_name`, `get_data()` |
| Classes | PascalCase | `DataProcessor` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY` |
| Schema classes | PascalCase + Schema suffix | `UserSchema` |

### Type Annotations

All public functions MUST have complete type annotations:
- Return types MUST be specified (use `-> None` for void functions)
- Use modern syntax: `list[str]`, `dict[str, Any]`, `str | None`
- Avoid `Any` except for truly dynamic data

## Development Workflow

### Subagent Usage (Claude Code Environment)

When using AI-assisted development:
- **Context isolation**: Subagents run in isolated contexts, return only summaries
- **Clear delegation**: Provide explicit goals, constraints, and output format requirements
- **Appropriate use**: Tests, large codebase exploration, high-output commands
- **Avoid**: Frequent interactive tasks, quick single modifications

### Pre-Implementation Checklist

Before implementing any feature:
1. Search for existing implementations in the codebase
2. Check if a third-party library can solve the problem
3. Verify the approach aligns with constitution principles
4. Identify files that will be modified

## Governance

This constitution supersedes all other coding practices in the project. All contributions MUST:
- Pass constitution compliance review before merge
- Document any justified exceptions in the PR description
- Receive approval from at least one maintainer familiar with the constitution

### Amendment Process

1. Propose amendment via PR to `.specify/memory/constitution.md`
2. Provide rationale for changes (why current rule is insufficient)
3. Update version according to semantic versioning:
   - MAJOR: Principle removal or fundamental redefinition
   - MINOR: New principle or significant expansion
   - PATCH: Clarifications, wording improvements
4. Update dependent templates if principles change

### Compliance Review

All PRs SHOULD be checked against:
- [ ] Modern Python syntax used throughout
- [ ] No unnecessary abstractions introduced
- [ ] SOTA libraries used where applicable
- [ ] No inline comments (docstrings for complex logic only)
- [ ] Conventional Commit message format
- [ ] Proper exception handling with context

**Version**: 1.0.0 | **Ratified**: 2026-01-26 | **Last Amended**: 2026-01-26
