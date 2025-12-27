# CLAUDE.md

## 🚨 READ THIS FIRST - CRITICAL REQUIREMENT 🚨

**You are running in a git worktree created by the Claude Code application.**

The worktree has already been created for you in `~/.claude-worktrees/`. Your job is to work within this worktree, NOT to create new worktrees.

---

## MANDATORY RULES - NO EXCEPTIONS

These rules are REQUIRED. There is NO other way to assist this user. If you cannot follow these rules exactly, you cannot help.

---

## ⚠️ IMPORTANT: WORKTREE LOCATION

**NOTE: The Claude Code application automatically creates worktrees in `~/.claude-worktrees/`**

This is hardcoded behavior in the Claude Code app itself. By the time the AI starts, the worktree has already been created by the application.

**The actual worktree location used by Claude Code:**
```
~/.claude-worktrees/
```

**Full path:**
```
/Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/
```

**IMPORTANT: DO NOT attempt to create worktrees manually.** The Claude Code application handles worktree creation when you start a new session. The AI should never run `git worktree add` commands - worktrees are managed by the app.

---

## STOP. READ THIS COMPLETELY BEFORE DOING ANYTHING.

You are running in a **git worktree**. A worktree is an isolated working directory that allows multiple branches to be checked out simultaneously without conflicts.

Your worktree path looks like:
```
/Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/<your-branch-name>
```

**Why worktrees?** They enable parallel development, isolated testing, and prevent conflicts between different AI sessions or development tasks.

---

## THE CORRECT WORKFLOW

### Step 1: Edit files in YOUR WORKTREE

Work in your assigned worktree at:
```
/Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/<branch-name>
```

**Critical**: Use the `Edit` or `Write` tools to modify files in THIS path, not in the main repository.

### Step 2: Commit in your worktree

Run these commands from within your worktree:
```bash
git add -A
git commit -m "your descriptive message"
```

**Note**: Always commit from your worktree directory, never from the main repository.

### Step 3: Push your worktree branch to dev

Push your worktree's branch to the remote `dev` branch:
```bash
git push origin <your-worktree-branch-name>:dev
```

Example if your branch is named `elegant-turing`:
```bash
git push origin elegant-turing:dev
```

**Important**: You are NOT checking out `dev` locally. You are pushing your branch's changes to the remote `dev` branch.

---

## WHAT "PUSH TO DEV" MEANS

When the user says "push to dev", follow this sequence:

1. **Work in your worktree** - Edit files at the worktree path
2. **Commit your changes** - Use `git add` and `git commit` in the worktree
3. **Push to remote dev** - Run: `git push origin <worktree-branch>:dev`

This does NOT mean:
- ❌ Checking out the `dev` branch locally
- ❌ Merging your branch into local `dev`
- ❌ Working in the main repository

---

## COMMON MISTAKES - DO NOT MAKE THESE

| ❌ Wrong Action | ✅ Correct Action | Why |
|----------------|-------------------|-----|
| Edit files in main repo | Edit files in worktree | Worktree isolation prevents conflicts |
| `cd` to main repo to commit | Commit from worktree | Commits must be in worktree branch |
| `git checkout dev` locally | `git push origin <branch>:dev` | Push remotely, don't merge locally |
| `git push origin dev` | `git push origin <worktree-branch>:dev` | Push your branch TO dev, not dev itself |
| Manually create worktrees | Let app manage worktrees | Claude Code app handles worktree creation |

---

## VERIFICATION - How to Know You're in the Right Place

Before working, verify your location:

```bash
# Check current directory
pwd

# Should show: /Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/<branch-name>

# Verify path contains .claude-worktrees
pwd | grep -q "/.claude-worktrees/" && echo "✅ In worktree" || echo "❌ Not in worktree"

# Check current branch
git branch --show-current

# Should show your worktree branch name, NOT 'dev' or 'main'
```

**CRITICAL CHECK**: Verify you're in the worktree directory, not the main repository.

---

## CORRECT WORKFLOW EXAMPLE

**User request**: "Fix the bug in BackendService.swift and push to dev"

```bash
# 1. Edit the file in YOUR WORKTREE (use Edit tool)
# Path: /Volumes/.../SimpleTunes/<your-branch>/frontend/SimpleTunes/API/BackendService.swift

# 2. Commit in worktree
git add -A
git commit -m "Fix: resolve connection timeout in BackendService"

# 3. Push worktree branch to dev
git push origin <your-worktree-branch>:dev
```

---

## AFTER EVERY PUSH - MANDATORY CONFIRMATION

After pushing changes, ALWAYS run this command and show output to the user:

```bash
git log origin/dev -1 --oneline
```

This confirms your commit successfully reached `origin/dev`.

**Example output**:
```
a1b2c3d Fix: resolve connection timeout in BackendService
```

---

## PROJECT STRUCTURE

| Component | Location | Technology | Details |
|-----------|----------|------------|---------|
| Backend | `backend/daemon.py` | Python, FastAPI | Runs on port 49917 |
| Frontend | `frontend/SimpleTunes/` | Swift, SwiftUI | macOS menu bar app |

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
- **Responsibilities**: Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend
- **Access**: Full project access

### XC (XClaude)
- **When**: User starts AI instance inside Xcode IDE
- **Responsibilities**: Swift/SwiftUI frontend code only
- **Limitations**: Focused on iOS/macOS development

### OC (Online Claude Code)
- **When**: User starts AI instance via web interface
- **Responsibilities**: Python backend, scripts, documentation, git operations, Swift/SwiftUI frontend
- **Access**: Full project access

### TC (Terminal Claude Code)
- **When**: User starts AI instance from terminal/CLI
- **Responsibilities**: Command-line operations, scripts, automation
- **Access**: Shell-based operations

---

## TROUBLESHOOTING

### "Working in wrong directory"
**Problem**: You're editing files in the main repository instead of the worktree

**Solution**:
```bash
# 1. Verify your current location
pwd

# 2. Should show worktree path
# /Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/<branch-name>

# 3. If not in worktree, navigate to it
cd ~/.claude-worktrees/SimpleTunes/<branch-name>
```

**Prevention**: ALWAYS verify you're in the worktree before editing files

### "Push failed - permission denied"
- Verify branch name matches your worktree
- Check you're pushing FROM worktree, not main repo
- Ensure using syntax: `git push origin <worktree-branch>:dev`

### "Not currently on any branch"
- You may be in detached HEAD state
- Run: `git checkout <your-worktree-branch>`

### "Cannot find worktree path"
- Verify path exists: `ls ~/.claude-worktrees/SimpleTunes/`
- Check you're using correct branch name in path
- List all worktrees: `git worktree list`

### "File not found after editing"
- Confirm you edited file in WORKTREE path, not main repo
- Use absolute paths to avoid confusion
- Verify you're in the correct worktree: `pwd`

---

## QUICK REFERENCE

**Standard workflow command sequence**:
```bash
# 1. Make changes (use Edit tool in worktree)

# 2. Commit
git add -A && git commit -m "Description of changes"

# 3. Push to dev
git push origin $(git branch --show-current):dev

# 4. Verify
git log origin/dev -1 --oneline
```

**Emergency check - "Where am I?"**:
```bash
pwd && git branch --show-current
```

---

## REMEMBER

**CRITICAL - WORKTREE MANAGEMENT:**
- ✅ Worktrees are created by Claude Code app in `~/.claude-worktrees/`
- ❌ NEVER manually create worktrees with `git worktree add`
- ✅ ALWAYS verify you're in the worktree before editing files
- ✅ The app manages worktree creation automatically

**WORKFLOW:**
- ✅ Always work in the worktree (not main repo)
- ✅ Commit from the worktree
- ✅ Push your worktree branch to remote `dev`
- ✅ Verify after every push
- ❌ Never check out `dev` locally
- ❌ Never work in main repository
- ❌ Never skip the verification step
- ❌ Never manually create or manage worktrees
