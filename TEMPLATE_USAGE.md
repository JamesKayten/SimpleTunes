# CLAUDE.md Template Usage Guide

## Quick Start

1. Copy `CLAUDE.template.md` to your project root as `CLAUDE.md`
2. Replace all `{{PLACEHOLDERS}}` with project-specific values
3. Commit to your repository

## Placeholders to Replace

### Required Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{PROJECT_NAME}}` | Your project/repository name | `SimpleTunes` |
| `{{EXAMPLE_FILE}}` | A representative file name for examples | `BackendService.swift` |
| `{{EXAMPLE_PATH}}` | Relative path to the example file | `frontend/SimpleTunes/API/BackendService.swift` |
| `{{EXAMPLE_COMMIT_MESSAGE}}` | Sample commit message | `resolve connection timeout in BackendService` |
| `{{PROJECT_STRUCTURE_DESCRIPTION}}` | Table describing your project components | See example below |
| `{{DC_RESPONSIBILITIES}}` | Desktop Claude responsibilities | `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend` |
| `{{XC_RESPONSIBILITIES}}` | XClaude responsibilities | `Swift/SwiftUI frontend code only` |
| `{{OC_RESPONSIBILITIES}}` | Online Claude responsibilities | `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend` |

## Example Replacements

### For SimpleTunes Project:

```markdown
{{PROJECT_NAME}} → SimpleTunes

{{EXAMPLE_FILE}} → BackendService.swift

{{EXAMPLE_PATH}} → frontend/SimpleTunes/API/BackendService.swift

{{EXAMPLE_COMMIT_MESSAGE}} → resolve connection timeout in BackendService

{{PROJECT_STRUCTURE_DESCRIPTION}} →
| Component | Location | Technology | Details |
|-----------|----------|------------|---------|
| Backend | `backend/daemon.py` | Python, FastAPI | Runs on port 49917 |
| Frontend | `frontend/SimpleTunes/` | Swift, SwiftUI | macOS menu bar app |

{{DC_RESPONSIBILITIES}} → Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend

{{XC_RESPONSIBILITIES}} → Swift/SwiftUI frontend code only

{{OC_RESPONSIBILITIES}} → Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend
```

## Using sed for Quick Replacement

Create a file `replacements.txt` with your values:
```
PROJECT_NAME=YourProject
EXAMPLE_FILE=YourFile.ext
EXAMPLE_PATH=path/to/YourFile.ext
EXAMPLE_COMMIT_MESSAGE=your example message
```

Then run:
```bash
sed -e 's/{{PROJECT_NAME}}/YourProject/g' \
    -e 's/{{EXAMPLE_FILE}}/YourFile.ext/g' \
    -e 's/{{EXAMPLE_PATH}}/path\/to\/YourFile.ext/g' \
    -e 's/{{EXAMPLE_COMMIT_MESSAGE}}/your example message/g' \
    CLAUDE.template.md > CLAUDE.md
```

## Manual Replacement (Recommended for Complex Sections)

For `{{PROJECT_STRUCTURE_DESCRIPTION}}` and responsibilities, manually edit the file to provide accurate project-specific information.

## Verification

After creating your CLAUDE.md:

1. Search for any remaining `{{` to ensure all placeholders are replaced
2. Verify paths match your project structure
3. Test the verification commands in the document
4. Commit to your repository

```bash
# Check for unreplaced placeholders
grep -n "{{" CLAUDE.md

# If output is empty, all placeholders are replaced
```

## Optional Customizations

You may want to customize:
- File size limits table (adjust for your languages)
- AI role responsibilities (based on your workflow)
- Troubleshooting section (add project-specific issues)
- Project structure details

## Template Maintenance

When updating the template:
1. Make changes to `CLAUDE.template.md`
2. Update this usage guide if new placeholders are added
3. Re-generate CLAUDE.md for affected projects
4. Test in a worktree before committing
