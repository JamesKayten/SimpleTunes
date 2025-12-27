# CLAUDE.md

## 🚨 READ THIS FIRST - CRITICAL REQUIREMENT 🚨

**BEFORE DOING ANYTHING, READ THE WORKTREE LOCATION RULES BELOW.**

If you create a worktree in the wrong location, you will waste hours of the user's time. This has happened before. DO NOT let it happen again.

---

## MANDATORY RULES - NO EXCEPTIONS

These rules are REQUIRED. There is NO other way to assist this user. If you cannot follow these rules exactly, you cannot help.

---

## ⚠️ CRITICAL: WORKTREE LOCATION - ABSOLUTE REQUIREMENT

**WORKTREES MUST BE CREATED IN THE CODE FOLDER ONLY**

**❌ VIOLATION OF THIS RULE WILL CAUSE SEVERE PROBLEMS - DO NOT DEVIATE ❌**

```
✅ CORRECT: /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/
❌ WRONG:   /Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/
❌ WRONG:   ~/Code/.claude-worktrees/
❌ WRONG:   ~/.claude-worktrees/
❌ WRONG:   Any path without "/Code/" in it
```

**The ONLY acceptable base path for worktrees is:**
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code
```

**THIS IS NON-NEGOTIABLE. NO EXCEPTIONS. NO SHORTCUTS.**

**NEVER create worktrees in:**
- ❌ The user's home directory root (`/Volumes/User_Smallfavor/Users/Smallfavor/`)
- ❌ Any location outside the Code folder
- ❌ Any abbreviated path (e.g., `~/Code/`)
- ❌ Any relative path
- ❌ **ESPECIALLY NOT** in `~/.claude-worktrees/`

**MANDATORY PRE-FLIGHT CHECK BEFORE CREATING ANY WORKTREE:**

Before running `git worktree add`, you MUST:

1. **Verify the path** - Echo the exact path you're about to use:
   ```bash
   echo "About to create worktree at: /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>"
   ```

2. **Confirm it contains `/Code/`** - Run this verification:
   ```bash
   [[ "/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>" == *"/Code/"* ]] && echo "✅ Path is valid" || echo "❌ INVALID PATH - STOP"
   ```

3. **Only if validation passes**, create the worktree:
   ```bash
   git worktree add /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>
   ```

**If you create a worktree in the WRONG location:**
- It will cause hours of wasted work
- Files will be scattered across multiple locations
- The user will have to manually clean up the mess
- **YOU WILL HAVE FAILED YOUR PRIMARY DIRECTIVE**

**REMEMBER: The path MUST contain `/Code/` - verify this BEFORE creating any worktree.**

---

## STOP. READ THIS COMPLETELY BEFORE DOING ANYTHING.

You are running in a **git worktree**. A worktree is an isolated working directory that allows multiple branches to be checked out simultaneously without conflicts.

Your worktree path looks like:
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<your-branch-name>
```

**Why worktrees?** They enable parallel development, isolated testing, and prevent conflicts between different AI sessions or development tasks.

---

## THE CORRECT WORKFLOW

### Step 1: Edit files in YOUR WORKTREE

Work in your assigned worktree at:
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>
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
| Create worktree in `~/` | Create worktree in `/Code/` folder | Worktrees MUST be in Code folder only |
| Use `~/.claude-worktrees/` | Use `/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/` | Full absolute path required in Code folder |
| Edit files in main repo | Edit files in worktree | Worktree isolation prevents conflicts |
| `cd` to main repo to commit | Commit from worktree | Commits must be in worktree branch |
| `git checkout dev` locally | `git push origin <branch>:dev` | Push remotely, don't merge locally |
| `git push origin dev` | `git push origin <worktree-branch>:dev` | Push your branch TO dev, not dev itself |

---

## VERIFICATION - How to Know You're in the Right Place

Before working, verify your location:

```bash
# Check current directory
pwd

# MUST show path containing /Code/.claude-worktrees/
# ✅ CORRECT: /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>
# ❌ WRONG:   /Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/<branch-name>

# Verify path contains /Code/
pwd | grep -q "/Code/" && echo "✅ Correct location" || echo "❌ WRONG LOCATION - MUST BE IN CODE FOLDER"

# Check current branch
git branch --show-current

# Should show your worktree branch name, NOT 'dev' or 'main'
```

**CRITICAL CHECK**: If your path does NOT contain `/Code/`, you are in the WRONG location. Stop immediately and navigate to the correct worktree in the Code folder.

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

### "Worktree created in wrong location" ⚠️ CRITICAL
**Problem**: Worktree was created in `~/.claude-worktrees/` instead of `/Code/.claude-worktrees/`

**Solution**:
```bash
# 1. Remove the incorrectly placed worktree
git worktree remove ~/.claude-worktrees/SimpleTunes/<branch-name>

# 2. Create it in the CORRECT location
git worktree add /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>

# 3. Verify location
pwd | grep -q "/Code/" && echo "✅ Correct" || echo "❌ Still wrong"
```

**Prevention**: ALWAYS verify path contains `/Code/` before creating worktrees

### "Push failed - permission denied"
- Verify branch name matches your worktree
- Check you're pushing FROM worktree, not main repo
- Ensure using syntax: `git push origin <worktree-branch>:dev`

### "Not currently on any branch"
- You may be in detached HEAD state
- Run: `git checkout <your-worktree-branch>`

### "Cannot find worktree path"
- Verify path exists: `ls /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/`
- Check you're using correct branch name in path
- Ensure you're looking in `/Code/` not `~/`

### "File not found after editing"
- Confirm you edited file in WORKTREE path, not main repo
- Verify worktree is in `/Code/.claude-worktrees/` not `~/.claude-worktrees/`
- Use absolute paths to avoid confusion

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

**CRITICAL - WORKTREE LOCATION:**
- ✅ Worktrees MUST be in `/Code/.claude-worktrees/` ONLY
- ❌ NEVER create worktrees in `~/.claude-worktrees/` or home directory
- ✅ ALWAYS verify path contains `/Code/` before working
- 🚨 **IF UNSURE, ASK THE USER BEFORE CREATING A WORKTREE**

**WORKFLOW:**
- ✅ Always work in the worktree
- ✅ Commit from the worktree
- ✅ Push your worktree branch to remote `dev`
- ✅ Verify after every push
- ❌ Never check out `dev` locally
- ❌ Never work in main repository
- ❌ Never skip the verification step

---

## 🔒 FINAL WORKTREE LOCATION ENFORCEMENT 🔒

**THIS SECTION EXISTS TO PREVENT THE MISTAKE THAT WAS MADE BEFORE**

When you need to create a worktree:

**STEP 1: STOP AND VERIFY**
Ask yourself: "Does my path contain `/Code/`?"

**STEP 2: USE THIS EXACT COMMAND FORMAT**
```bash
git worktree add /Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>
```

**STEP 3: AFTER CREATION, IMMEDIATELY VERIFY**
```bash
git worktree list | grep "/Code/"
```

If you don't see `/Code/` in the output, you created the worktree in the WRONG location.

**CONSEQUENCES OF VIOLATING THIS RULE:**
- ✅ Correct path: User can work productively
- ❌ Wrong path: Hours of cleanup, lost work, frustration

**THE ONLY ACCEPTABLE WORKTREE PATH:**
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes/<branch-name>
                                          ^^^^^ THIS PART IS CRITICAL
```

**If you're about to create a worktree and have ANY doubt, STOP and ask the user to verify the path.**
