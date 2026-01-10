#!/bin/bash
# =============================================================================
# check-memory.sh - Check if CLAUDE_MEMORY.md needs updating
# =============================================================================

MEMORY_FILE="CLAUDE_MEMORY.md"

# Check if memory file exists
if [ ! -f "$MEMORY_FILE" ]; then
    echo "INFO: CLAUDE_MEMORY.md not found (will be created on first Claude session)"
    exit 0
fi

# Get last modification time
MEMORY_MTIME=$(stat -c %Y "$MEMORY_FILE" 2>/dev/null || stat -f %m "$MEMORY_FILE" 2>/dev/null)
CURRENT_TIME=$(date +%s)

# Check if modified in last 24 hours
DIFF=$((CURRENT_TIME - MEMORY_MTIME))
HOURS=$((DIFF / 3600))

if [ $HOURS -gt 24 ]; then
    echo "=============================================="
    echo "  CLAUDE_MEMORY.md Reminder"
    echo "=============================================="
    echo ""
    echo "Last updated: $HOURS hours ago"
    echo ""
    echo "Consider updating if:"
    echo "  - New features were added"
    echo "  - Architecture decisions were made"
    echo "  - Known issues were found/fixed"
    echo ""
    echo "This is just a reminder - commit will proceed."
    echo ""
fi

# Always pass (warning only)
exit 0
