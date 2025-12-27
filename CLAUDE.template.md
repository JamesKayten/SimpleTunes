# CLAUDE.md Template

<!--
To use this template:
1. Copy to your project root as CLAUDE.md
2. Replace all {{PLACEHOLDERS}} with your actual values
3. Update PROJECT STRUCTURE section with your project details
4. Customize FILE SIZE LIMITS if needed
5. Remove this comment block
-->

# CLAUDE.md

## MANDATORY RULES - NO EXCEPTIONS

These rules are REQUIRED. There is NO other way to assist this user. If you cannot follow these rules exactly, you cannot help.

---

## ⚠️ CRITICAL: WORKTREE LOCATION - ABSOLUTE REQUIREMENT

**WORKTREES MUST BE CREATED IN THE CODE FOLDER ONLY**

```
✅ CORRECT: {{WORKTREE_BASE_PATH}}/.claude-worktrees/
❌ WRONG:   {{USER_HOME}}/.claude-worktrees/
❌ WRONG:   ~/Code/.claude-worktrees/
❌ WRONG:   ~/.claude-worktrees/
```

**The ONLY acceptable base path for worktrees is:**
```
{{WORKTREE_BASE_PATH}}
```

**NEVER create worktrees in:**
- The user's home directory root
- Any location outside the Code folder
- Any abbreviated or relative path

**If you need to create a worktree, the command MUST be:**
```bash
git worktree add {{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>
```

**Before creating any worktree, verify the path contains `{{WORKTREE_IDENTIFIER}}` in it.**

---

## STOP. READ THIS COMPLETELY BEFORE DOING ANYTHING.

You are running in a **git worktree**. A worktree is an isolated working directory that allows multiple branches to be checked out simultaneously without conflicts.

Your worktree path looks like:
```
{{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<your-branch-name>
```

**Why worktrees?** They enable parallel development, isolated testing, and prevent conflicts between different AI sessions or development tasks.

---

## THE CORRECT WORKFLOW

### Step 1: Edit files in YOUR WORKTREE

Work in your assigned worktree at:
```
{{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>
```

**Critical**: Use the `Edit` or `Write` tools to modify files in THIS path, not in the main repository.

### Step 2: Commit in your worktree

Run these commands from within your worktree:
```bash
git add -A
git commit -m "your descriptive message"
```

**Note**: Always commit from your worktree directory, never from the main repository.

### Step 3: Push your worktree branch to {{TARGET_BRANCH}}

Push your worktree's branch to the remote `{{TARGET_BRANCH}}` branch:
```bash
git push origin <your-worktree-branch-name>:{{TARGET_BRANCH}}
```

Example if your branch is named `elegant-turing`:
```bash
git push origin elegant-turing:{{TARGET_BRANCH}}
```

**Important**: You are NOT checking out `{{TARGET_BRANCH}}` locally. You are pushing your branch's changes to the remote `{{TARGET_BRANCH}}` branch.

---

## WHAT "PUSH TO {{TARGET_BRANCH}}" MEANS

When the user says "push to {{TARGET_BRANCH}}", follow this sequence:

1. **Work in your worktree** - Edit files at the worktree path
2. **Commit your changes** - Use `git add` and `git commit` in the worktree
3. **Push to remote {{TARGET_BRANCH}}** - Run: `git push origin <worktree-branch>:{{TARGET_BRANCH}}`

This does NOT mean:
- ❌ Checking out the `{{TARGET_BRANCH}}` branch locally
- ❌ Merging your branch into local `{{TARGET_BRANCH}}`
- ❌ Working in the main repository

---

## COMMON MISTAKES - DO NOT MAKE THESE

| ❌ Wrong Action | ✅ Correct Action | Why |
|----------------|-------------------|-----|
| Create worktree in `~/` | Create worktree in `{{WORKTREE_IDENTIFIER}}` folder | Worktrees MUST be in Code folder only |
| Use `~/.claude-worktrees/` | Use `{{WORKTREE_BASE_PATH}}/.claude-worktrees/` | Full absolute path required in Code folder |
| Edit files in main repo | Edit files in worktree | Worktree isolation prevents conflicts |
| `cd` to main repo to commit | Commit from worktree | Commits must be in worktree branch |
| `git checkout {{TARGET_BRANCH}}` locally | `git push origin <branch>:{{TARGET_BRANCH}}` | Push remotely, don't merge locally |
| `git push origin {{TARGET_BRANCH}}` | `git push origin <worktree-branch>:{{TARGET_BRANCH}}` | Push your branch TO {{TARGET_BRANCH}}, not {{TARGET_BRANCH}} itself |

---

## VERIFICATION - How to Know You're in the Right Place

Before working, verify your location:

```bash
# Check current directory
pwd

# MUST show path containing {{WORKTREE_IDENTIFIER}}/.claude-worktrees/
# ✅ CORRECT: {{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>
# ❌ WRONG:   {{USER_HOME}}/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>

# Verify path contains {{WORKTREE_IDENTIFIER}}
pwd | grep -q "{{WORKTREE_IDENTIFIER}}" && echo "✅ Correct location" || echo "❌ WRONG LOCATION - MUST BE IN CODE FOLDER"

# Check current branch
git branch --show-current

# Should show your worktree branch name, NOT '{{TARGET_BRANCH}}' or 'main'
```

**CRITICAL CHECK**: If your path does NOT contain `{{WORKTREE_IDENTIFIER}}`, you are in the WRONG location. Stop immediately and navigate to the correct worktree in the Code folder.

---

## CORRECT WORKFLOW EXAMPLE

**User request**: "{{EXAMPLE_TASK}}"

```bash
# 1. Edit the file in YOUR WORKTREE (use Edit tool)
# Path: {{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<your-branch>/{{EXAMPLE_FILE}}

# 2. Commit in worktree
git add -A
git commit -m "{{EXAMPLE_COMMIT_MESSAGE}}"

# 3. Push worktree branch to {{TARGET_BRANCH}}
git push origin <your-worktree-branch>:{{TARGET_BRANCH}}
```

---

## AFTER EVERY PUSH - MANDATORY CONFIRMATION

After pushing changes, ALWAYS run this command and show output to the user:

```bash
git log origin/{{TARGET_BRANCH}} -1 --oneline
```

This confirms your commit successfully reached `origin/{{TARGET_BRANCH}}`.

**Example output**:
```
a1b2c3d {{EXAMPLE_COMMIT_MESSAGE}}
```

---

## PROJECT STRUCTURE

<!-- CUSTOMIZE THIS SECTION FOR YOUR PROJECT -->

| Component | Location | Technology | Details |
|-----------|----------|------------|---------|
| {{COMPONENT_1_NAME}} | `{{COMPONENT_1_PATH}}` | {{COMPONENT_1_TECH}} | {{COMPONENT_1_DETAILS}} |
| {{COMPONENT_2_NAME}} | `{{COMPONENT_2_PATH}}` | {{COMPONENT_2_TECH}} | {{COMPONENT_2_DETAILS}} |

### File Size Limits

All source files must comply with maximum line counts to ensure maintainability, reviewability, and modularity.

| File Type | Max Lines | Reason |
|-----------|-----------|--------|
| Python (.py) | 250 | Single responsibility, easy review |
| JavaScript/TypeScript (.js, .ts, .jsx, .tsx) | 150 | Smaller modules, faster comprehension |
| Java (.java) | 400 | Accounts for verbosity |
| Swift (.swift) | 300 | Balance between protocol conformance and clarity |
| Shell (.sh) | 200 | Scripts should be focused |

**Enforcement**: Files exceeding limits should be split using patterns from the project's refactoring guidelines.

---

## ROLES - AI Instance Responsibilities

Different Claude instances handle specific tasks based on their context:

### DC (Desktop Claude Code)
- **When**: User initiates from desktop Claude Code app
- **Responsibilities**: {{DC_RESPONSIBILITIES}}
- **Access**: Full project access

### XC (XClaude)
- **When**: User starts AI instance inside Xcode IDE
- **Responsibilities**: {{XC_RESPONSIBILITIES}}
- **Limitations**: Focused on iOS/macOS development

### OC (Online Claude Code)
- **When**: User starts AI instance via web interface
- **Responsibilities**: {{OC_RESPONSIBILITIES}}
- **Access**: Full project access

### TC (Terminal Claude Code)
- **When**: User starts AI instance from terminal/CLI
- **Responsibilities**: Command-line operations, scripts, automation
- **Access**: Shell-based operations

---

## TROUBLESHOOTING

### "Worktree created in wrong location" ⚠️ CRITICAL
**Problem**: Worktree was created in `~/.claude-worktrees/` instead of `{{WORKTREE_IDENTIFIER}}/.claude-worktrees/`

**Solution**:
```bash
# 1. Remove the incorrectly placed worktree
git worktree remove ~/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>

# 2. Create it in the CORRECT location
git worktree add {{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/<branch-name>

# 3. Verify location
pwd | grep -q "{{WORKTREE_IDENTIFIER}}" && echo "✅ Correct" || echo "❌ Still wrong"
```

**Prevention**: ALWAYS verify path contains `{{WORKTREE_IDENTIFIER}}` before creating worktrees

### "Push failed - permission denied"
- Verify branch name matches your worktree
- Check you're pushing FROM worktree, not main repo
- Ensure using syntax: `git push origin <worktree-branch>:{{TARGET_BRANCH}}`

### "Not currently on any branch"
- You may be in detached HEAD state
- Run: `git checkout <your-worktree-branch>`

### "Cannot find worktree path"
- Verify path exists: `ls {{WORKTREE_BASE_PATH}}/.claude-worktrees/{{PROJECT_NAME}}/`
- Check you're using correct branch name in path
- Ensure you're looking in `{{WORKTREE_IDENTIFIER}}` not `~/`

### "File not found after editing"
- Confirm you edited file in WORKTREE path, not main repo
- Verify worktree is in `{{WORKTREE_IDENTIFIER}}/.claude-worktrees/` not `~/.claude-worktrees/`
- Use absolute paths to avoid confusion

---

## QUICK REFERENCE

**Standard workflow command sequence**:
```bash
# 1. Make changes (use Edit tool in worktree)

# 2. Commit
git add -A && git commit -m "Description of changes"

# 3. Push to {{TARGET_BRANCH}}
git push origin $(git branch --show-current):{{TARGET_BRANCH}}

# 4. Verify
git log origin/{{TARGET_BRANCH}} -1 --oneline
```

**Emergency check - "Where am I?"**:
```bash
pwd && git branch --show-current
```

---

## REMEMBER

**CRITICAL - WORKTREE LOCATION:**
- ✅ Worktrees MUST be in `{{WORKTREE_IDENTIFIER}}/.claude-worktrees/` ONLY
- ❌ NEVER create worktrees in `~/.claude-worktrees/` or home directory
- ✅ ALWAYS verify path contains `{{WORKTREE_IDENTIFIER}}` before working

**WORKFLOW:**
- ✅ Always work in the worktree
- ✅ Commit from the worktree
- ✅ Push your worktree branch to remote `{{TARGET_BRANCH}}`
- ✅ Verify after every push
- ❌ Never check out `{{TARGET_BRANCH}}` locally
- ❌ Never work in main repository
- ❌ Never skip the verification step

---

## TEMPLATE PLACEHOLDERS

Replace these before using:

- `{{WORKTREE_BASE_PATH}}` - Base path for worktrees (e.g., `/Volumes/User_Smallfavor/Users/Smallfavor/Code`)
- `{{USER_HOME}}` - User's home directory (e.g., `/Volumes/User_Smallfavor/Users/Smallfavor`)
- `{{PROJECT_NAME}}` - Project repository name (e.g., `SimpleTunes`)
- `{{TARGET_BRANCH}}` - Default target branch for pushes (e.g., `dev`)
- `{{WORKTREE_IDENTIFIER}}` - Unique path component to verify (e.g., `/Code/`)
- `{{EXAMPLE_TASK}}` - Example task for workflow demo (e.g., "Fix the bug in BackendService.swift and push to dev")
- `{{EXAMPLE_FILE}}` - Example file path (e.g., `frontend/SimpleTunes/API/BackendService.swift`)
- `{{EXAMPLE_COMMIT_MESSAGE}}` - Example commit message (e.g., "Fix: resolve connection timeout in BackendService")
- `{{COMPONENT_1_NAME}}` - First component name (e.g., `Backend`)
- `{{COMPONENT_1_PATH}}` - First component path (e.g., `backend/daemon.py`)
- `{{COMPONENT_1_TECH}}` - First component tech (e.g., `Python, FastAPI`)
- `{{COMPONENT_1_DETAILS}}` - First component details (e.g., `Runs on port 49917`)
- `{{COMPONENT_2_NAME}}` - Second component name (e.g., `Frontend`)
- `{{COMPONENT_2_PATH}}` - Second component path (e.g., `frontend/SimpleTunes/`)
- `{{COMPONENT_2_TECH}}` - Second component tech (e.g., `Swift, SwiftUI`)
- `{{COMPONENT_2_DETAILS}}` - Second component details (e.g., `macOS menu bar app`)
- `{{DC_RESPONSIBILITIES}}` - Desktop Claude responsibilities (e.g., `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend`)
- `{{XC_RESPONSIBILITIES}}` - XClaude responsibilities (e.g., `Swift/SwiftUI frontend code only`)
- `{{OC_RESPONSIBILITIES}}` - Online Claude responsibilities (e.g., `Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend`)
