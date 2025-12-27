# CLAUDE.md

## MANDATORY RULES - NO EXCEPTIONS

These rules are REQUIRED. There is NO other way to assist this user. If you cannot follow these rules exactly, you cannot help.

---

## STOP. READ THIS COMPLETELY BEFORE DOING ANYTHING.

You are running in a **git worktree**. Your worktree path looks like:
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/<branch-name>
```

---

## THE CORRECT WORKFLOW

### Step 1: Edit files in YOUR WORKTREE

Work in your worktree at:
```
/Volumes/User_Smallfavor/Users/Smallfavor/Code/.claude-worktrees/SimpleTunes
```

Edit files here using the Edit tool.

### Step 2: Commit in your worktree

```bash
git add -A
git commit -m "your message"
```

### Step 3: Push your worktree branch to dev

```bash
git push origin <your-worktree-branch-name>:dev
```

Example:
```bash
git push origin elegant-turing:dev
```

---

## WHAT "PUSH TO DEV" MEANS

When the user says "push to dev":

1. Work in your worktree (edit files there)
2. Commit your changes in the worktree
3. Push your worktree branch to the remote dev branch:
   ```bash
   git push origin <worktree-branch>:dev
   ```

---

## COMMON MISTAKES - DO NOT MAKE THESE

| Wrong | Why it's wrong |
|-------|----------------|
| Edit files in main repo | You should work in your worktree |
| `cd` to main repo to commit | Commit from your worktree |
| `git checkout dev` in main repo | Push from worktree to dev instead |

---

## CORRECT WORKFLOW EXAMPLE

User says: "Fix the bug in BackendService.swift and push to dev"

```bash
# 1. Edit the file in YOUR WORKTREE
# Edit /Volumes/User_Smallfavor/Users/Smallfavor/.claude-worktrees/SimpleTunes/elegant-turing/frontend/SimpleTunes/API/BackendService.swift

# 2. Commit in worktree
git add -A && git commit -m "Fix bug in BackendService"

# 3. Push worktree branch to dev
git push origin elegant-turing:dev
```

---

## AFTER EVERY CHANGE - MANDATORY CONFIRMATION

After pushing, ALWAYS run this and show the output to the user:

```bash
git log origin/dev -1 --oneline
```

This confirms your commit is on origin/dev.

---

## PROJECT INFO

| Component | Location | Tech |
|-----------|----------|------|
| Backend | `backend/daemon.py` | Python, FastAPI, Port 49917 |
| Frontend | `frontend/SimpleTunes/` | Swift, SwiftUI, menu bar app |


### File Size Limits

All source files must comply with size limits:

| File Type | Max Lines |
|-----------|-----------|
| Python (.py) | 250 |
| JavaScript/TypeScript (.js, .ts, .jsx, .tsx) | 150 |
| Java (.java) | 400 |
| Swift (.swift) | 300 |
| Shell (.sh) | 200 |

## ROLES

- **DC (Desktop Claude Code):** Python backend, scripts, docs, git operations, Swift/SwiftUI frontend code
IF User starts an AI instance inside of Xcode:
- **XC (XClaude):** Swift/SwiftUI frontend code
IF User starts an AI instance online:
- **OC (Online Claude Code):** Python backend, scripts, docs, git operations, Swift/SwiftUI frontend code
IF User starts an AI instance locally:
- **TC (Terminal Claude Code)**
