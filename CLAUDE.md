# Claude Code Guidelines for SimpleTunes

This document defines coding standards and architectural guidelines for AI-assisted development of the SimpleTunes project.

## Code Organization Standards

### File Size Limits

**All Python files must not exceed 250 lines.**

This limit ensures:
- Files remain focused and maintainable
- Code is easier to review and understand
- Logical separation of concerns
- Improved testability

### Enforcement Strategy

When a file approaches or exceeds 250 lines:

1. **Route files** - Split by domain/resource
2. **Model files** - Split by domain (core, media, features)
3. **Service files** - Split by responsibility or data source
4. **Helper modules** - Extract format-specific or utility logic

### Project Structure

```
backend/
├── main.py                 # App setup and router registration only (<100 lines)
├── response_helpers.py     # Shared response formatting functions
├── models/                 # Database models split by domain
│   ├── __init__.py        # Re-exports all models for compatibility
│   ├── core.py            # Core entities (Track, Album, Artist, Playlist)
│   ├── media.py           # Media-related (Artwork, Lyrics, Analysis)
│   └── features.py        # Feature models (Queue, Scrobble, Watch, Duplicates)
├── routes/                 # API endpoints split by resource
│   ├── __init__.py        # Exports all routers
│   ├── stats_routes.py    # Statistics endpoints
│   ├── library_routes.py  # Library scanning/import
│   ├── track_routes.py    # Track management
│   ├── album_routes.py    # Album browsing
│   ├── artist_routes.py   # Artist browsing
│   └── ...                # One file per major resource
├── services/               # Business logic split by feature
│   ├── __init__.py        # Exports all services
│   ├── library_queries.py # Query operations
│   ├── library_stats.py   # Statistics
│   ├── scanner_files.py   # File scanning
│   ├── scanner_metadata.py# Metadata extraction
│   └── helpers/           # Shared utility modules
│       ├── audio_analysis.py
│       ├── tag_writers_mp3_mp4.py
│       └── ...
└── schemas.py             # Pydantic models
```

## Splitting Patterns

### Pattern 1: Route Extraction
```python
# Create routes/{domain}_routes.py
from fastapi import APIRouter
from response_helpers import {domain}_to_response

router = APIRouter(prefix="/{domain}", tags=["{Domain}"])

# Move all /{domain}/* endpoints here
```

### Pattern 2: Service Splitting
```python
# Split by responsibility:
# services/{name}_base.py - Core logic (~200 lines)
# services/{name}_helper.py - Helper functions (~150 lines)

# OR split by feature area or data source
```

### Pattern 3: Helper Module Extraction
```python
# services/helpers/{feature}.py
# Extract format-specific, data-source-specific, or
# algorithm-specific logic

# Example:
# - Format writers (MP3, FLAC, OGG)
# - API clients (iTunes, Deezer, Last.fm)
# - Algorithm implementations (fingerprinting, similarity)
```

## Module Design Principles

### 1. Backward Compatibility
When splitting modules, maintain backward compatibility:

```python
# Old import should still work
from services import LibraryService

# New granular imports available
from services import LibraryQueryService, LibraryStatsService
```

### 2. Single Responsibility
Each file should have one clear purpose:
- Route files: HTTP concerns only
- Service files: Business logic only
- Helper files: Specific algorithm or integration
- Model files: Data structure definitions

### 3. Import Organization
```python
# Standard library imports
from datetime import datetime
from typing import Optional

# Third-party imports
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

# Local imports (relative)
from database import get_db
from models import Track, Album
from services import LibraryService
from response_helpers import track_to_response
```

## Quality Requirements

### Before Committing

1. **Line count check**:
   ```bash
   find backend -name "*.py" -exec wc -l {} + | sort -rn | head -20
   ```

2. **Syntax validation**:
   ```bash
   python -m py_compile backend/main.py
   for f in backend/**/*.py; do python -m py_compile "$f"; done
   ```

3. **Import verification**:
   ```bash
   cd backend
   python -c "import main; print('✓ Main imports work')"
   python -c "from services import *; print('✓ Services import')"
   python -c "from routes import *; print('✓ Routes import')"
   ```

### Commit Message Format

For major refactorings:
```
Refactor: split {module} files to meet 250-line limit

- Extract {feature} from {original_file}
- Create {new_file_1} for {purpose}
- Create {new_file_2} for {purpose}
- Update imports in {affected_files}

Files affected: N files
Lines reorganized: ~X lines
```

## Common Refactoring Scenarios

### Scenario 1: Large Service File
**Problem**: Service file exceeds 250 lines
**Solution**: Split by responsibility or data source

Example:
```
artwork.py (431 lines) →
  - artwork_fetcher.py (remote APIs)
  - artwork_local.py (local cache/extraction)
```

### Scenario 2: Main.py with Many Routes
**Problem**: main.py has all route definitions
**Solution**: Extract routes to domain-specific files

Example:
```
main.py (749 lines) →
  - main.py (84 lines) - app setup only
  - routes/track_routes.py
  - routes/album_routes.py
  - routes/artist_routes.py
  - ... (11 route modules)
```

### Scenario 3: Monolithic Models File
**Problem**: models.py contains all model definitions
**Solution**: Group by domain

Example:
```
models.py (361 lines) →
  - models/core.py (core entities)
  - models/media.py (media features)
  - models/features.py (app features)
  - models/__init__.py (re-exports)
```

### Scenario 4: Format-Specific Operations
**Problem**: Service has many format handlers (MP3, FLAC, OGG, etc.)
**Solution**: Extract to helper modules

Example:
```
tag_writer.py (436 lines) →
  - tag_writer.py (249 lines) - coordination
  - helpers/tag_writers_mp3_mp4.py
  - helpers/tag_writers_flac_ogg.py
```

## Anti-Patterns to Avoid

❌ **Don't**: Create artificial splits that break cohesion
✅ **Do**: Split along natural boundaries (responsibility, domain, format)

❌ **Don't**: Break backward compatibility without migration path
✅ **Do**: Provide unified interface that delegates to split modules

❌ **Don't**: Duplicate code across split files
✅ **Do**: Extract shared logic to helper modules

❌ **Don't**: Split a 260-line file into 130+130 just to meet limit
✅ **Do**: Consider if the file can be optimized first (remove comments, consolidate)

## Tools and Automation

### Quick Line Count
```bash
# Show files over limit
find backend -name "*.py" -exec sh -c 'lines=$(wc -l < "$1"); if [ "$lines" -gt 250 ]; then echo "$lines $1"; fi' _ {} \; | sort -rn

# Count total Python files
find backend -name "*.py" | wc -l

# Show largest files
find backend -name "*.py" -exec wc -l {} + | sort -rn | head -10
```

### Pre-commit Hook (Optional)
```bash
#!/bin/bash
# Check for files over 250 lines
oversized=$(find backend -name "*.py" -exec sh -c 'lines=$(wc -l < "$1"); if [ "$lines" -gt 250 ]; then echo "$1"; fi' _ {} \;)

if [ -n "$oversized" ]; then
    echo "❌ Files exceed 250-line limit:"
    echo "$oversized"
    exit 1
fi
```

## Benefits Observed

After implementing these standards:

- **Maintainability**: Easier to locate and modify specific functionality
- **Code Review**: Smaller files are easier to review thoroughly
- **Testing**: Focused modules are easier to unit test
- **Collaboration**: Reduced merge conflicts with smaller, focused files
- **Onboarding**: New developers can understand modules in isolation
- **Refactoring**: Easier to identify and extract reusable components

## Getting Help

When refactoring:
1. Read the existing code thoroughly
2. Identify natural split points (responsibilities, domains, formats)
3. Extract shared logic first
4. Split along identified boundaries
5. Update imports incrementally
6. Test after each major change
7. Verify all files are under limit before committing

Remember: The goal is **maintainable, well-organized code**, not just meeting a number. The 250-line limit is a forcing function for good design.
