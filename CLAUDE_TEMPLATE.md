# Claude Code Guidelines Template

This document defines coding standards and architectural guidelines for AI-assisted development.

> **Usage**: Copy this file to your repository as `CLAUDE.md` and customize the language-specific sections and examples for your project.

## Code Organization Standards

### File Size Limits

**All source files must not exceed 250 lines.**

**Rationale**:
- Files remain focused and maintainable
- Code is easier to review and understand
- Enforces logical separation of concerns
- Improves testability and modularity
- Reduces cognitive load

### Enforcement Strategy

When a file approaches or exceeds 250 lines:

1. **Route/Controller files** - Split by domain or resource
2. **Model/Entity files** - Split by domain or bounded context
3. **Service/Business Logic files** - Split by responsibility or data source
4. **Utility/Helper modules** - Extract specialized logic

### Typical Project Structure

```
project/
├── main.*                 # Application entry point (<100 lines)
├── config/                # Configuration and settings
├── models/                # Data models split by domain
│   ├── core.*            # Core business entities
│   ├── auth.*            # Authentication models
│   └── integrations.*    # Third-party integration models
├── routes/                # API endpoints/controllers split by resource
│   ├── users.*           # User management endpoints
│   ├── products.*        # Product endpoints
│   └── orders.*          # Order endpoints
├── services/              # Business logic split by feature
│   ├── user_auth.*       # Authentication logic
│   ├── order_processing.*# Order processing
│   └── helpers/          # Shared utility modules
│       ├── email.*       # Email utilities
│       ├── payment.*     # Payment processing
│       └── validators.*  # Validation helpers
└── utils/                 # Cross-cutting utilities
```

## Splitting Patterns

### Pattern 1: Route/Controller Extraction
```
# Split by resource or domain
routes/
  ├── user_routes.*       # All /users/* endpoints
  ├── product_routes.*    # All /products/* endpoints
  └── order_routes.*      # All /orders/* endpoints

# Each file should handle ONE resource type
```

### Pattern 2: Service Layer Splitting
```
# Option A: Split by responsibility
services/
  ├── user_queries.*      # Read operations
  └── user_commands.*     # Write operations

# Option B: Split by data source
services/
  ├── database_service.*  # Database operations
  └── api_service.*       # External API calls

# Option C: Split by algorithm
services/
  ├── search_indexer.*    # Indexing logic
  └── search_query.*      # Query logic
```

### Pattern 3: Helper Module Extraction
```
# Extract specialized logic to helpers/
helpers/
  ├── format_converters.*  # Format-specific conversions
  ├── data_validators.*    # Validation logic
  └── api_clients.*        # Third-party API clients

# Each helper should serve ONE specific purpose
```

### Pattern 4: Model/Entity Splitting
```
# Group by domain or bounded context
models/
  ├── core.*              # Core business models
  ├── reporting.*         # Reporting models
  └── analytics.*         # Analytics models

# Keep related models together
```

## Module Design Principles

### 1. Single Responsibility Principle
Each file should have **one clear, well-defined purpose**:

- **Controllers/Routes**: HTTP/request handling only
- **Services**: Business logic only
- **Repositories/DAOs**: Data access only
- **Models**: Data structure definitions only
- **Helpers**: Specific utility or algorithm

### 2. Backward Compatibility
When splitting modules, maintain compatibility where possible:

```
# Old import still works (facade pattern)
from services import OrderService

# New granular imports available
from services import OrderQueryService, OrderCommandService
```

### 3. DRY (Don't Repeat Yourself)
- Extract common logic to shared helpers
- Avoid duplicating code across split files
- Create base classes for shared behavior

### 4. Clear Dependencies
- Keep dependencies unidirectional
- Avoid circular imports
- Use dependency injection where appropriate

## Language-Specific Guidelines

### Python

**Import Organization**:
```python
# Standard library imports
from datetime import datetime
from typing import Optional, List

# Third-party imports
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

# Local imports
from .database import get_db
from .models import User, Order
from .services import OrderService
```

**Naming Conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### JavaScript/TypeScript

**Import Organization**:
```typescript
// Node/built-in imports
import { readFile } from 'fs/promises';
import path from 'path';

// Third-party imports
import express from 'express';
import { v4 as uuidv4 } from 'uuid';

// Local imports
import { UserService } from './services/userService';
import type { User } from './models/user';
```

**Naming Conventions**:
- Files: `camelCase.ts` or `kebab-case.ts`
- Classes: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

### Java

**Package Structure**:
```
com.example.project/
  ├── controller/         # HTTP controllers (<250 lines each)
  ├── service/           # Business logic
  ├── repository/        # Data access
  ├── model/            # Domain models
  └── util/             # Utilities
```

**Naming Conventions**:
- Files: Match class name (`UserController.java`)
- Classes: `PascalCase`
- Methods: `camelCase`
- Constants: `UPPER_SNAKE_CASE`

## Quality Requirements

### Before Committing

1. **Line count verification**
   - Verify no files exceed 250 lines
   - Use automated checks if possible

2. **Syntax validation**
   - Ensure all files compile/parse correctly
   - Run linter if available

3. **Import verification**
   - Test that all imports resolve
   - Check for circular dependencies

4. **Test coverage**
   - Ensure split modules have tests
   - Don't break existing tests

### Commit Message Format

For refactoring commits:
```
Refactor: split {module} to meet 250-line limit

- Extract {feature} from {original_file}
- Create {new_file_1} for {purpose}
- Create {new_file_2} for {purpose}
- Update imports in {affected_files}
- Maintain backward compatibility via {method}

Files affected: N files
Lines reorganized: ~X lines
```

For feature commits:
```
Add: {feature description}

- Implement {component} in {file}
- Add {functionality}
- Update {related files}

All files comply with 250-line limit.
```

## Common Refactoring Scenarios

### Scenario 1: Oversized Service File
**Problem**: Service file has multiple responsibilities
**Solution**: Split by responsibility or data source

**Example**:
```
user_service.* (400 lines) →
  - user_auth_service.*      # Authentication logic
  - user_profile_service.*   # Profile management
  - user_notification_service.* # Notifications
```

### Scenario 2: Monolithic Controller
**Problem**: Single controller handles many resources
**Solution**: Extract to resource-specific controllers

**Example**:
```
api_controller.* (600 lines) →
  - user_controller.*        # /users endpoints
  - product_controller.*     # /products endpoints
  - order_controller.*       # /orders endpoints
```

### Scenario 3: Large Model File
**Problem**: All models in one file
**Solution**: Group by domain or bounded context

**Example**:
```
models.* (500 lines) →
  - user_models.*            # User-related models
  - commerce_models.*        # Products, Orders, Payments
  - analytics_models.*       # Analytics and reporting
```

### Scenario 4: Format/Protocol Handlers
**Problem**: Service handles multiple formats/protocols
**Solution**: Extract format-specific handlers

**Example**:
```
data_processor.* (450 lines) →
  - data_processor.*         # Coordination (150 lines)
  - processors/json_processor.*
  - processors/xml_processor.*
  - processors/csv_processor.*
```

## Best Practices

### ✅ DO

- **Split along natural boundaries** (domain, responsibility, protocol)
- **Extract shared logic** to helper modules
- **Maintain backward compatibility** when possible
- **Write clear commit messages** explaining the split
- **Keep related code together** (don't split prematurely)
- **Test after splitting** to ensure functionality preserved

### ❌ DON'T

- **Create artificial splits** that break cohesion
- **Duplicate code** across split files
- **Break APIs** without migration path
- **Split mechanically** (e.g., first 250 lines → file A, rest → file B)
- **Over-optimize** files just under the limit
- **Ignore the principle** - focus on maintainability, not just line counts

## Measuring Success

Good splits should result in:

- ✅ Each file has a clear, single purpose
- ✅ File/module names clearly describe contents
- ✅ Related functionality is grouped together
- ✅ No circular dependencies
- ✅ Easier to find and modify specific features
- ✅ Improved code review experience
- ✅ Better test organization

## Automation and Tools

### Line Count Check Script

**Bash**:
```bash
#!/bin/bash
# check-line-limits.sh
find . -name "*.{your_extension}" -type f | while read file; do
  lines=$(wc -l < "$file")
  if [ "$lines" -gt 250 ]; then
    echo "❌ $lines lines: $file"
  fi
done
```

**Python**:
```python
#!/usr/bin/env python3
# check_line_limits.py
import os
import sys

def check_line_limits(directory, extensions, limit=250):
    violations = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                with open(filepath) as f:
                    lines = len(f.readlines())
                if lines > limit:
                    violations.append((filepath, lines))

    if violations:
        print("❌ Files exceeding 250-line limit:")
        for path, lines in sorted(violations, key=lambda x: x[1], reverse=True):
            print(f"  {lines:4d} lines: {path}")
        sys.exit(1)
    else:
        print("✅ All files comply with 250-line limit")

if __name__ == "__main__":
    check_line_limits(".", [".py", ".js", ".ts", ".java"])
```

### Pre-commit Hook Example

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run line count check
./scripts/check-line-limits.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Commit rejected: Files exceed 250-line limit"
    echo "Please split oversized files before committing"
    exit 1
fi
```

### CI/CD Integration

**GitHub Actions**:
```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  check-line-limits:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check file line limits
        run: |
          ./scripts/check-line-limits.sh
```

## Project-Specific Customization

When adapting this template:

1. **Adjust file extensions** for your language
2. **Customize directory structure** to match your framework
3. **Add language-specific patterns** and idioms
4. **Define project-specific naming conventions**
5. **Set up automation** appropriate for your toolchain
6. **Document exceptions** if any files need to exceed the limit
7. **Add examples** from your actual codebase

## Philosophy

The 250-line limit is not arbitrary—it's a **forcing function for good design**:

- **Forces modular thinking**: You must think about separation of concerns
- **Prevents feature creep**: Limits scope of individual modules
- **Improves comprehension**: Humans can hold ~250 lines in working memory
- **Encourages refactoring**: Regular refactoring becomes a habit
- **Facilitates collaboration**: Smaller files = fewer merge conflicts

**Remember**: The goal is **clean, maintainable, well-organized code**. The line limit is a tool to achieve that goal, not an end in itself.

## Getting Help

When refactoring large files:

1. **Understand the code** thoroughly before splitting
2. **Identify responsibilities** - what does this file do?
3. **Find natural boundaries** - where can it split logically?
4. **Extract shared logic** first to reduce duplication
5. **Split incrementally** and test after each change
6. **Update documentation** to reflect new structure
7. **Get code review** before merging large refactorings

---

## Appendix: Line Count Considerations

### What Counts as a Line?

- Blank lines: **Count** (they affect readability)
- Comments: **Count** (they're part of the file)
- Imports: **Count** (suggests too many dependencies)
- Closing braces: **Count** (it's still a line)

### Healthy Line Counts by File Type

- Entry points (main.*): **50-100 lines**
- Controllers/Routes: **100-200 lines**
- Services: **150-250 lines**
- Models: **50-150 lines**
- Helpers/Utils: **100-200 lines**
- Tests: **150-250 lines**

### When to Split Earlier

Consider splitting before 250 lines if:
- File has multiple distinct responsibilities
- Team velocity is slowing due to merge conflicts
- Code reviews are taking longer than usual
- New developers struggle to understand the file

### Rare Exceptions

Files that might reasonably exceed 250 lines:
- Generated code (mark clearly as generated)
- Configuration files with extensive settings
- Large constant definitions (consider extracting to data files)
- Integration tests with many test cases (consider splitting test suites)

**Document any exceptions** in your project's CLAUDE.md file.
