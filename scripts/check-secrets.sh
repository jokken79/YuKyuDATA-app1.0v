#!/bin/bash
# =============================================================================
# check-secrets.sh - Detect secrets and credentials in staged files
# =============================================================================

# Patterns to detect (case insensitive)
PATTERNS=(
    'password\s*[:=]'
    'api[_-]?key\s*[:=]'
    'secret[_-]?key\s*[:=]'
    'access[_-]?token\s*[:=]'
    'auth[_-]?token\s*[:=]'
    'private[_-]?key'
    'BEGIN RSA PRIVATE KEY'
    'BEGIN OPENSSH PRIVATE KEY'
    'BEGIN EC PRIVATE KEY'
    'BEGIN PGP PRIVATE KEY'
    'aws_access_key_id'
    'aws_secret_access_key'
    'AKIA[0-9A-Z]{16}'
    'ghp_[a-zA-Z0-9]{36}'
    'gho_[a-zA-Z0-9]{36}'
    'github_pat_'
    'sk-[a-zA-Z0-9]{48}'
    'Bearer [a-zA-Z0-9_-]{20,}'
)

# Files to skip
SKIP_PATTERNS=(
    '.env.example'
    'package-lock.json'
    '*.md'
    'check-secrets.sh'
)

FOUND_SECRETS=0

# Get staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

for file in $STAGED_FILES; do
    # Skip certain files
    SKIP=0
    for skip_pattern in "${SKIP_PATTERNS[@]}"; do
        if [[ "$file" == $skip_pattern ]]; then
            SKIP=1
            break
        fi
    done

    if [ $SKIP -eq 1 ]; then
        continue
    fi

    # Check if file exists and is readable
    if [ ! -f "$file" ] || [ ! -r "$file" ]; then
        continue
    fi

    # Check each pattern
    for pattern in "${PATTERNS[@]}"; do
        MATCH=$(grep -inE "$pattern" "$file" 2>/dev/null | head -3)
        if [ -n "$MATCH" ]; then
            echo "WARNING: Potential secret found in $file:"
            echo "$MATCH"
            echo ""
            FOUND_SECRETS=1
        fi
    done
done

if [ $FOUND_SECRETS -eq 1 ]; then
    echo "=============================================="
    echo "  SECRETS DETECTED - Review before committing"
    echo "=============================================="
    echo ""
    echo "If these are false positives, you can:"
    echo "  1. Add to .gitignore"
    echo "  2. Use 'git commit --no-verify' (not recommended)"
    echo "  3. Add # noqa: secret comment"
    echo ""
    exit 1
fi

exit 0
