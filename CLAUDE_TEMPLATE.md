# CLAUDE.md Template

> **Instructions**: Copy this template to your repository as `CLAUDE.md` and customize the placeholders marked with `{{VARIABLE}}`.

---

## MANDATORY RULES - NO EXCEPTIONS

These rules are REQUIRED. There is NO other way to assist this user. If you cannot follow these rules exactly, you cannot help.

---

## STOP. READ THIS COMPLETELY BEFORE DOING ANYTHING.

You are running in a **git worktree**. A worktree is an isolated working directory that allows multiple branches to be checked out simultaneously without conflicts.

Your worktree path looks like:
```
{{WORKTREE_BASE_PATH}}/{{PROJECT_NAME}}/<your-branch-name>
```

**Why worktrees?** They enable parallel development, isolated testing, and prevent conflicts between different AI sessions or development tasks.

---

## THE CORRECT WORKFLOW

### Step 1: Edit files in YOUR WORKTREE

Work in your assigned worktree at:
```
{{WORKTREE_BASE_PATH}}/{{PROJECT_NAME}}/<branch-name>
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

# Should show something like:
# {{WORKTREE_BASE_PATH}}/{{PROJECT_NAME}}/<branch-name>

# Check current branch
git branch --show-current

# Should show your worktree branch name, NOT '{{TARGET_BRANCH}}' or 'main'
```

---

## CORRECT WORKFLOW EXAMPLE

**User request**: "{{EXAMPLE_TASK}}"

```bash
# 1. Edit the file in YOUR WORKTREE (use Edit tool)
# Path: {{WORKTREE_BASE_PATH}}/{{PROJECT_NAME}}/<your-branch>/{{EXAMPLE_FILE_PATH}}

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

{{CUSTOMIZE_THIS_SECTION}}

Example structure:
| Component | Location | Technology | Details |
|-----------|----------|------------|---------|
| Backend | `{{BACKEND_PATH}}` | {{BACKEND_TECH}} | {{BACKEND_DETAILS}} |
| Frontend | `{{FRONTEND_PATH}}` | {{FRONTEND_TECH}} | {{FRONTEND_DETAILS}} |
| API | `{{API_PATH}}` | {{API_TECH}} | {{API_DETAILS}} |

### File Size Limits

All source files must comply with maximum line counts to ensure maintainability, reviewability, and modularity.

| File Type | Max Lines | Reason |
|-----------|-----------|--------|
| Python (.py) | 250 | Single responsibility, easy review |
| JavaScript/TypeScript (.js, .ts, .jsx, .tsx) | 150 | Smaller modules, faster comprehension |
| Java (.java) | 400 | Accounts for verbosity |
| Swift (.swift) | 300 | Balance between protocol conformance and clarity |
| Shell (.sh) | 200 | Scripts should be focused |
| {{CUSTOM_LANG}} (.{{EXT}}) | {{LIMIT}} | {{REASON}} |

**Customization**: Adjust limits based on your project's language and conventions.

**Enforcement**: Files exceeding limits should be split using patterns from the project's refactoring guidelines.

---

## ROLES - AI Instance Responsibilities

{{CUSTOMIZE_THIS_SECTION}}

Define roles based on how AI instances are invoked in your workflow:

### {{ROLE_1_NAME}}
- **When**: {{TRIGGER_CONDITION}}
- **Responsibilities**: {{RESPONSIBILITIES}}
- **Access**: {{ACCESS_LEVEL}}
- **Limitations**: {{LIMITATIONS}}

### {{ROLE_2_NAME}}
- **When**: {{TRIGGER_CONDITION}}
- **Responsibilities**: {{RESPONSIBILITIES}}
- **Access**: {{ACCESS_LEVEL}}
- **Limitations**: {{LIMITATIONS}}

**Example roles**:
- Desktop Claude (full access)
- IDE-based Claude (language-specific)
- Terminal Claude (CLI operations)
- Web Claude (remote collaboration)

---

## TROUBLESHOOTING

### "Push failed - permission denied"
- Verify branch name matches your worktree
- Check you're pushing FROM worktree, not main repo
- Ensure using syntax: `git push origin <worktree-branch>:{{TARGET_BRANCH}}`

### "Not currently on any branch"
- You may be in detached HEAD state
- Run: `git checkout <your-worktree-branch>`

### "Cannot find worktree path"
- Verify path exists: `ls {{WORKTREE_BASE_PATH}}/{{PROJECT_NAME}}/`
- Check you're using correct branch name in path

### "File not found after editing"
- Confirm you edited file in WORKTREE path, not main repo
- Use absolute paths to avoid confusion

### {{CUSTOM_ISSUE}}
- {{SOLUTION}}

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

## PROJECT-SPECIFIC NOTES

{{ADD_CUSTOM_NOTES_HERE}}

Examples:
- Special environment variables required
- Pre-commit hooks or checks
- CI/CD integration requirements
- Testing requirements before pushing
- Code review process
- Documentation requirements

---

## REMEMBER

- ✅ Always work in the worktree
- ✅ Commit from the worktree
- ✅ Push your worktree branch to remote `{{TARGET_BRANCH}}`
- ✅ Verify after every push
- ❌ Never check out `{{TARGET_BRANCH}}` locally
- ❌ Never work in main repository
- ❌ Never skip the verification step

---

## TEMPLATE CUSTOMIZATION CHECKLIST

Before using this template, replace all `{{VARIABLES}}`:

- [ ] `{{WORKTREE_BASE_PATH}}` - Your worktrees base directory
- [ ] `{{PROJECT_NAME}}` - Your project name
- [ ] `{{TARGET_BRANCH}}` - Target branch for pushes (usually `dev`, `develop`, or `staging`)
- [ ] `{{EXAMPLE_TASK}}` - Representative task for your project
- [ ] `{{EXAMPLE_FILE_PATH}}` - Example file path
- [ ] `{{EXAMPLE_COMMIT_MESSAGE}}` - Example commit message
- [ ] `{{BACKEND_*}}`, `{{FRONTEND_*}}` - Component details
- [ ] `{{ROLE_*}}` - AI instance role definitions
- [ ] `{{CUSTOM_*}}` - Any project-specific content
- [ ] Remove this checklist section when done!

---

## ADDITIONAL RESOURCES

- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Project Contributing Guidelines]({{LINK_TO_CONTRIBUTING}})
- [Code Style Guide]({{LINK_TO_STYLE_GUIDE}})
- [Development Setup]({{LINK_TO_DEV_SETUP}})
