# CLAUDE.md Template Usage Guide

This guide explains how to use the `CLAUDE.template.md` file to create custom CLAUDE.md files for your projects.

## Quick Start

```bash
# 1. Copy template to your project
cp CLAUDE.template.md /path/to/your/project/CLAUDE.md

# 2. Replace placeholders with your values
# See "Placeholder Reference" below

# 3. Customize project-specific sections
# - PROJECT STRUCTURE
# - File Size Limits (if needed)
# - ROLES responsibilities
```

## Placeholder Reference

### Required Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{WORKTREE_BASE_PATH}}` | Absolute path to worktree base directory | `/Volumes/User_Smallfavor/Users/Smallfavor/Code` |
| `{{USER_HOME}}` | User's home directory | `/Volumes/User_Smallfavor/Users/Smallfavor` |
| `{{PROJECT_NAME}}` | Repository/project name | `SimpleTunes` |
| `{{TARGET_BRANCH}}` | Default branch for pushes | `dev` |
| `{{WORKTREE_IDENTIFIER}}` | Path component to verify correct location | `/Code/` |

### Example Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{EXAMPLE_TASK}}` | Sample task for workflow demo | `Fix the bug in BackendService.swift and push to dev` |
| `{{EXAMPLE_FILE}}` | Sample file path | `frontend/SimpleTunes/API/BackendService.swift` |
| `{{EXAMPLE_COMMIT_MESSAGE}}` | Sample commit message | `Fix: resolve connection timeout in BackendService` |

### Project Structure Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{COMPONENT_1_NAME}}` | First component name | `Backend` |
| `{{COMPONENT_1_PATH}}` | First component path | `backend/daemon.py` |
| `{{COMPONENT_1_TECH}}` | First component technology | `Python, FastAPI` |
| `{{COMPONENT_1_DETAILS}}` | First component details | `Runs on port 49917` |
| `{{COMPONENT_2_NAME}}` | Second component name | `Frontend` |
| `{{COMPONENT_2_PATH}}` | Second component path | `frontend/SimpleTunes/` |
| `{{COMPONENT_2_TECH}}` | Second component technology | `Swift, SwiftUI` |
| `{{COMPONENT_2_DETAILS}}` | Second component details | `macOS menu bar app` |

### Role Responsibility Placeholders

| Placeholder | Description | Example |
|------------|-------------|---------|
| `{{DC_RESPONSIBILITIES}}` | Desktop Claude Code responsibilities | `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend` |
| `{{XC_RESPONSIBILITIES}}` | XClaude responsibilities | `Swift/SwiftUI frontend code only` |
| `{{OC_RESPONSIBILITIES}}` | Online Claude Code responsibilities | `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend` |

## Step-by-Step Example

Let's create a CLAUDE.md for a project called "MyWebApp":

### 1. Determine Your Values

```bash
WORKTREE_BASE_PATH=/Users/john/Code
USER_HOME=/Users/john
PROJECT_NAME=MyWebApp
TARGET_BRANCH=dev
WORKTREE_IDENTIFIER=/Code/
```

### 2. Replace Placeholders

Using sed (macOS/Linux):
```bash
sed -e 's|{{WORKTREE_BASE_PATH}}|/Users/john/Code|g' \
    -e 's|{{USER_HOME}}|/Users/john|g' \
    -e 's|{{PROJECT_NAME}}|MyWebApp|g' \
    -e 's|{{TARGET_BRANCH}}|dev|g' \
    -e 's|{{WORKTREE_IDENTIFIER}}|/Code/|g' \
    -e 's|{{EXAMPLE_TASK}}|Fix authentication bug and push to dev|g' \
    -e 's|{{EXAMPLE_FILE}}|backend/auth.py|g' \
    -e 's|{{EXAMPLE_COMMIT_MESSAGE}}|Fix: resolve JWT token expiration issue|g' \
    -e 's|{{COMPONENT_1_NAME}}|Backend API|g' \
    -e 's|{{COMPONENT_1_PATH}}|backend/app.py|g' \
    -e 's|{{COMPONENT_1_TECH}}|Python, Flask|g' \
    -e 's|{{COMPONENT_1_DETAILS}}|REST API on port 5000|g' \
    -e 's|{{COMPONENT_2_NAME}}|Frontend|g' \
    -e 's|{{COMPONENT_2_PATH}}|frontend/src/|g' \
    -e 's|{{COMPONENT_2_TECH}}|React, TypeScript|g' \
    -e 's|{{COMPONENT_2_DETAILS}}|SPA with Vite bundler|g' \
    -e 's|{{DC_RESPONSIBILITIES}}|Full-stack development, git operations, documentation|g' \
    -e 's|{{XC_RESPONSIBILITIES}}|N/A for this project|g' \
    -e 's|{{OC_RESPONSIBILITIES}}|Full-stack development, git operations, documentation|g' \
    CLAUDE.template.md > CLAUDE.md
```

### 3. Customize Project-Specific Sections

Edit the generated CLAUDE.md:

**PROJECT STRUCTURE** - Add more components if needed:
```markdown
| Component | Location | Technology | Details |
|-----------|----------|------------|---------|
| Backend API | `backend/app.py` | Python, Flask | REST API on port 5000 |
| Frontend | `frontend/src/` | React, TypeScript | SPA with Vite bundler |
| Database | `database/` | PostgreSQL | Primary data store |
| Cache | - | Redis | Session and query cache |
```

**File Size Limits** - Adjust if your project has different standards:
```markdown
| File Type | Max Lines | Reason |
|-----------|-----------|--------|
| Python (.py) | 300 | Slightly larger due to type hints |
| TypeScript (.ts, .tsx) | 200 | Increase from default 150 |
```

### 4. Remove Template Section

Delete the "TEMPLATE PLACEHOLDERS" section at the bottom of the file.

### 5. Commit to Your Repository

```bash
git add CLAUDE.md
git commit -m "Add: CLAUDE.md workflow documentation"
git push origin main
```

## Automated Replacement Script

Create a helper script `generate-claude-md.sh`:

```bash
#!/bin/bash

# Configuration
WORKTREE_BASE_PATH="/Users/john/Code"
USER_HOME="/Users/john"
PROJECT_NAME="MyWebApp"
TARGET_BRANCH="dev"
WORKTREE_IDENTIFIER="/Code/"

# Component 1
COMPONENT_1_NAME="Backend API"
COMPONENT_1_PATH="backend/app.py"
COMPONENT_1_TECH="Python, Flask"
COMPONENT_1_DETAILS="REST API on port 5000"

# Component 2
COMPONENT_2_NAME="Frontend"
COMPONENT_2_PATH="frontend/src/"
COMPONENT_2_TECH="React, TypeScript"
COMPONENT_2_DETAILS="SPA with Vite bundler"

# Examples
EXAMPLE_TASK="Fix authentication bug and push to dev"
EXAMPLE_FILE="backend/auth.py"
EXAMPLE_COMMIT_MESSAGE="Fix: resolve JWT token expiration issue"

# Responsibilities
DC_RESPONSIBILITIES="Full-stack development, git operations, documentation"
XC_RESPONSIBILITIES="N/A for this project"
OC_RESPONSIBILITIES="Full-stack development, git operations, documentation"

# Generate CLAUDE.md
sed -e "s|{{WORKTREE_BASE_PATH}}|$WORKTREE_BASE_PATH|g" \
    -e "s|{{USER_HOME}}|$USER_HOME|g" \
    -e "s|{{PROJECT_NAME}}|$PROJECT_NAME|g" \
    -e "s|{{TARGET_BRANCH}}|$TARGET_BRANCH|g" \
    -e "s|{{WORKTREE_IDENTIFIER}}|$WORKTREE_IDENTIFIER|g" \
    -e "s|{{EXAMPLE_TASK}}|$EXAMPLE_TASK|g" \
    -e "s|{{EXAMPLE_FILE}}|$EXAMPLE_FILE|g" \
    -e "s|{{EXAMPLE_COMMIT_MESSAGE}}|$EXAMPLE_COMMIT_MESSAGE|g" \
    -e "s|{{COMPONENT_1_NAME}}|$COMPONENT_1_NAME|g" \
    -e "s|{{COMPONENT_1_PATH}}|$COMPONENT_1_PATH|g" \
    -e "s|{{COMPONENT_1_TECH}}|$COMPONENT_1_TECH|g" \
    -e "s|{{COMPONENT_1_DETAILS}}|$COMPONENT_1_DETAILS|g" \
    -e "s|{{COMPONENT_2_NAME}}|$COMPONENT_2_NAME|g" \
    -e "s|{{COMPONENT_2_PATH}}|$COMPONENT_2_PATH|g" \
    -e "s|{{COMPONENT_2_TECH}}|$COMPONENT_2_TECH|g" \
    -e "s|{{COMPONENT_2_DETAILS}}|$COMPONENT_2_DETAILS|g" \
    -e "s|{{DC_RESPONSIBILITIES}}|$DC_RESPONSIBILITIES|g" \
    -e "s|{{XC_RESPONSIBILITIES}}|$XC_RESPONSIBILITIES|g" \
    -e "s|{{OC_RESPONSIBILITIES}}|$OC_RESPONSIBILITIES|g" \
    CLAUDE.template.md > CLAUDE.md

echo "✅ CLAUDE.md generated successfully"
echo "⚠️  Remember to:"
echo "   1. Review and customize PROJECT STRUCTURE section"
echo "   2. Adjust File Size Limits if needed"
echo "   3. Remove TEMPLATE PLACEHOLDERS section at the bottom"
```

Make it executable and run:
```bash
chmod +x generate-claude-md.sh
./generate-claude-md.sh
```

## Common Use Cases

### Monorepo with Multiple Projects

For each sub-project, adjust `PROJECT_NAME` and paths:

```bash
# Project 1: API
PROJECT_NAME="MyMonorepo/api"
COMPONENT_1_PATH="packages/api/src/server.ts"

# Project 2: Web
PROJECT_NAME="MyMonorepo/web"
COMPONENT_1_PATH="packages/web/src/App.tsx"
```

### Different Target Branches

Some projects use `main` instead of `dev`:

```bash
TARGET_BRANCH="main"
```

Or staging environments:

```bash
TARGET_BRANCH="staging"
```

### Windows Paths

For Windows, adjust paths:

```bash
WORKTREE_BASE_PATH="C:/Users/john/Code"
USER_HOME="C:/Users/john"
WORKTREE_IDENTIFIER="/Code/"  # Still works with forward slashes in Git
```

## Validation

After generating your CLAUDE.md, verify:

1. **All placeholders replaced**: `grep -E "{{.*}}" CLAUDE.md` should return nothing (except in examples)
2. **Paths are absolute**: Check that all worktree paths start with `/` or drive letter
3. **Project structure accurate**: Verify component paths exist in your repository
4. **Target branch exists**: `git branch -r | grep origin/TARGET_BRANCH`

## Best Practices

1. **Keep template updated**: When you improve your CLAUDE.md, update the template
2. **Version control**: Commit both CLAUDE.md and CLAUDE.md.template
3. **Document customizations**: Add comments in CLAUDE.md explaining project-specific rules
4. **Share across organization**: Use the same template for consistency across projects
5. **Regular reviews**: Update CLAUDE.md when project structure changes significantly

## Troubleshooting

### Placeholders still showing after replacement

Check for typos in placeholder names or use the script method instead of manual replacement.

### Paths not working on different OS

Use forward slashes `/` even on Windows - Git handles this correctly.

### Multiple components to document

Duplicate the component rows in PROJECT STRUCTURE section, no need for more placeholders.

## Support

For issues or improvements to the template, see the SimpleTunes repository where it originated.
