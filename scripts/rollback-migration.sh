#!/bin/bash

# rollback-migration.sh
# Database rollback script for UUID schema migration
# Usage: ./scripts/rollback-migration.sh [database_file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
DB_FILE="${1:-yukyu.db}"
BACKUP_DIR="backups"
BACKUP_PATTERN="yukyu_pre_migration_*.db"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   DATABASE ROLLBACK (UUID Migration)${NC}"
echo -e "${BLUE}   Database: ${DB_FILE}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Verify backup exists
echo -e "${YELLOW}[STEP 1/3]${NC} Looking for pre-migration backup..."

BACKUPS=$(ls -1 "${BACKUP_DIR}/${BACKUP_PATTERN}" 2>/dev/null | sort -r)

if [ -z "$BACKUPS" ]; then
    echo -e "${RED}ERROR: No pre-migration backups found in ${BACKUP_DIR}/${BACKUP_PATTERN}${NC}"
    echo ""
    echo -e "${YELLOW}Available backups:${NC}"
    ls -lh "${BACKUP_DIR}"/yukyu_*.db 2>/dev/null || echo "  (none)"
    exit 1
fi

# Get most recent backup
LATEST_BACKUP=$(echo "$BACKUPS" | head -1)
echo -e "${GREEN}✓${NC} Found backup: $(basename $LATEST_BACKUP)"
echo ""

# Step 2: Confirm with user
echo -e "${YELLOW}[STEP 2/3]${NC} Rollback confirmation..."
echo ""
echo -e "${RED}WARNING: This will overwrite ${DB_FILE} with the pre-migration version!${NC}"
echo "  • Current: ${DB_FILE}"
echo "  • Restore: $LATEST_BACKUP"
echo ""
read -p "Continue with rollback? (yes/no): " -r CONFIRM
echo ""

if [[ ! $CONFIRM =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Rollback cancelled${NC}"
    exit 0
fi

# Step 3: Perform rollback
echo -e "${YELLOW}[STEP 3/3]${NC} Restoring database..."

# Create safety backup of current state
CURRENT_BACKUP="${BACKUP_DIR}/yukyu_rollback_backup_$(date +%Y%m%d_%H%M%S).db"
cp "${DB_FILE}" "${CURRENT_BACKUP}"
echo -e "${GREEN}✓${NC} Safety backup created: $(basename $CURRENT_BACKUP)"

# Restore from pre-migration backup
cp "${LATEST_BACKUP}" "${DB_FILE}"
echo -e "${GREEN}✓${NC} Database restored to: ${LATEST_BACKUP}"
echo ""

# Verify restore
python << 'PYTHON_SCRIPT'
import sqlite3

db_file = "yukyu.db"
try:
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM employees")
    count = c.fetchone()[0]
    conn.close()
    print(f"✓ Database verified: {count} employees found")
except Exception as e:
    print(f"✗ Error verifying database: {e}")
    exit(1)
PYTHON_SCRIPT

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}ROLLBACK COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  • Restored from: $(basename $LATEST_BACKUP)"
echo "  • Safety backup: $(basename $CURRENT_BACKUP)"
echo "  • Database file: $DB_FILE"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Verify application works correctly"
echo "  2. Review any errors in application logs"
echo "  3. Contact support if issues persist"
echo ""
