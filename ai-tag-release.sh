#!/bin/bash
# AI-Powered Release Tagger
# Usage: ./ai-tag-release.sh [--auto] [--patch|--minor|--major]

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

AUTO_MODE=false
VERSION_BUMP="minor"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto) AUTO_MODE=true; shift ;;
        --patch) VERSION_BUMP="patch"; shift ;;
        --minor) VERSION_BUMP="minor"; shift ;;
        --major) VERSION_BUMP="major"; shift ;;
        *) shift ;;
    esac
done

echo -e "${BLUE}=== AI-Powered Release Tagger ===${NC}\n"

# Check we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Detect project type
detect_project_type() {
    if [ -f "backend/main.py" ] && [ -d "frontend" ]; then
        echo "macOS clipboard manager|📋"
    elif [ -f "Package.swift" ]; then
        echo "Swift package|🔶"
    elif [ -f "package.json" ]; then
        echo "JavaScript application|🌐"
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        echo "Python application|🐍"
    else
        echo "software project|🔧"
    fi
}

PROJECT_INFO=$(detect_project_type)
PROJECT_TYPE=$(echo "$PROJECT_INFO" | cut -d'|' -f1)
PROJECT_EMOJI=$(echo "$PROJECT_INFO" | cut -d'|' -f2)

echo -e "${BLUE}${PROJECT_EMOJI} Project type: ${GREEN}${PROJECT_TYPE}${NC}"

# Get current version (highest semver tag, not just reachable from HEAD)
CURRENT_VERSION=$(git tag -l 'v*' | sort -V | tail -1)
CURRENT_VERSION=${CURRENT_VERSION:-v0.0.0}
echo -e "Current version: ${GREEN}${CURRENT_VERSION}${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "\n${YELLOW}⚠️  Uncommitted changes detected${NC}"
    git status --short

    if [ "$AUTO_MODE" = true ]; then
        echo -e "\n${BLUE}Auto-committing changes...${NC}"
        git add -A
        # Generate commit message from changed files
        CHANGED=$(git diff --cached --name-only | head -5 | tr '\n' ', ' | sed 's/,$//')
        COMMIT_MSG="Update: ${CHANGED}"
        git commit -m "$COMMIT_MSG"
        echo -e "${GREEN}✓ Committed: ${COMMIT_MSG}${NC}"
    else
        echo -e "\n${YELLOW}Please commit your changes first, or use --auto${NC}"
        read -p "Commit all changes now? (y/n) [n]: " COMMIT_NOW
        if [[ "$COMMIT_NOW" == "y" ]]; then
            git add -A
            read -p "Commit message: " COMMIT_MSG
            if [ -z "$COMMIT_MSG" ]; then
                COMMIT_MSG="Release preparation"
            fi
            git commit -m "$COMMIT_MSG"
        else
            echo -e "${RED}Aborted. Commit changes first.${NC}"
            exit 1
        fi
    fi
fi

# Calculate new version
CURRENT_VERSION_NO_V=${CURRENT_VERSION#v}
MAJOR=$(echo $CURRENT_VERSION_NO_V | cut -d. -f1)
MINOR=$(echo $CURRENT_VERSION_NO_V | cut -d. -f2)
PATCH=$(echo $CURRENT_VERSION_NO_V | cut -d. -f3)
PATCH=${PATCH:-0}

case $VERSION_BUMP in
    major) NEW_VERSION="v$((MAJOR + 1)).0.0" ;;
    minor) NEW_VERSION="v${MAJOR}.$((MINOR + 1)).0" ;;
    patch) NEW_VERSION="v${MAJOR}.${MINOR}.$((PATCH + 1))" ;;
esac

# Get commits since last tag
COMMITS=$(git log ${CURRENT_VERSION}..HEAD --pretty=format:"- %s" --no-merges 2>/dev/null || git log --pretty=format:"- %s" --no-merges -10)

if [ -z "$COMMITS" ]; then
    echo -e "\n${YELLOW}No new commits since ${CURRENT_VERSION}${NC}"
    exit 0
fi

echo -e "\n${BLUE}Changes since ${CURRENT_VERSION}:${NC}"
echo "$COMMITS" | head -10

# Generate release title from commits
FIRST_COMMIT=$(echo "$COMMITS" | head -1 | sed 's/^- //')
RELEASE_TITLE=$(echo "$FIRST_COMMIT" | cut -c1-50)

# Generate release notes
RELEASE_NOTES="$COMMITS"

echo -e "\n${BLUE}New version: ${GREEN}${NEW_VERSION}${NC}"
echo -e "${BLUE}Release title: ${GREEN}${RELEASE_TITLE}${NC}"

if [ "$AUTO_MODE" = false ]; then
    echo ""
    read -p "Proceed with release? (y/n) [y]: " CONFIRM
    CONFIRM=${CONFIRM:-y}
    if [[ "$CONFIRM" != "y" ]]; then
        echo -e "${YELLOW}Aborted${NC}"
        exit 0
    fi
fi

# Create tag
echo -e "\n${BLUE}Creating tag ${NEW_VERSION}...${NC}"
git tag -a "$NEW_VERSION" -m "${PROJECT_TYPE} Release ${NEW_VERSION}

${RELEASE_TITLE}

Changes:
${RELEASE_NOTES}

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Push
echo -e "${BLUE}Pushing to origin...${NC}"
git push origin HEAD --tags

echo -e "\n${GREEN}✅ Released ${NEW_VERSION}${NC}"
echo -e "${BLUE}View at: $(git remote get-url origin | sed 's/\.git$//')/releases/tag/${NEW_VERSION}${NC}"
