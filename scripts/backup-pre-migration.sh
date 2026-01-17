#!/bin/bash

# backup-pre-migration.sh
# Pre-migration backup and validation script for UUID schema migration
# Usage: ./scripts/backup-pre-migration.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Database configuration
DB_FILE="yukyu.db"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/yukyu_pre_migration_${TIMESTAMP}.db"
SCHEMA_FILE="${BACKUP_DIR}/schema_pre_migration_${TIMESTAMP}.sql"
DATA_EXPORT="${BACKUP_DIR}/data_export_pre_migration_${TIMESTAMP}.json"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   PRE-MIGRATION BACKUP & VALIDATION${NC}"
echo -e "${BLUE}   Timestamp: ${TIMESTAMP}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Verify database exists
echo -e "${YELLOW}[STEP 1/4]${NC} Verifying database..."
if [ ! -f "$DB_FILE" ]; then
    echo -e "${RED}ERROR: Database file '$DB_FILE' not found!${NC}"
    exit 1
fi

DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
echo -e "${GREEN}✓${NC} Database found: $DB_FILE (${DB_SIZE})"
echo ""

# Step 2: Create full backup
echo -e "${YELLOW}[STEP 2/4]${NC} Creating full database backup..."
cp "$DB_FILE" "$BACKUP_FILE"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}✓${NC} Backup created: $BACKUP_FILE (${BACKUP_SIZE})"
echo ""

# Step 3: Export schema and data using Python
echo -e "${YELLOW}[STEP 3/4]${NC} Exporting schema and data..."
python3 << 'PYTHON_SCRIPT'
import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

db_file = "yukyu.db"
schema_file = "backups/schema_pre_migration_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".sql"
data_export = "backups/data_export_pre_migration_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"

try:
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Export schema
    with open(schema_file, 'w') as f:
        for line in conn.iterdump():
            f.write(line + '\n')

    print(f"✓ Schema exported: {schema_file}")

    # Get all table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]

    # Export data as JSON with row counts
    data_summary = {}
    for table in tables:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]
        data_summary[table] = {
            "count": count,
            "samples": []
        }

        # Get first 3 samples for verification
        c.execute(f"SELECT * FROM {table} LIMIT 3")
        cols = [desc[0] for desc in c.description]
        for row in c.fetchall():
            data_summary[table]["samples"].append(dict(zip(cols, row)))

    with open(data_export, 'w') as f:
        json.dump(data_summary, f, indent=2, default=str)

    print(f"✓ Data summary exported: {data_export}")

    # Print summary
    print("\nTable Row Counts:")
    for table, info in sorted(data_summary.items()):
        print(f"  • {table}: {info['count']} rows")

    conn.close()

except Exception as e:
    print(f"✗ Error during export: {e}", file=sys.stderr)
    sys.exit(1)

PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to export schema and data${NC}"
    exit 1
fi
echo ""

# Step 4: Create migration checklist
echo -e "${YELLOW}[STEP 4/4]${NC} Creating migration checklist..."

CHECKLIST_FILE="MIGRATION_CHECKLIST.md"

cat > "$CHECKLIST_FILE" << 'CHECKLIST_CONTENT'
# Migration Checklist: SQLite to UUID Schema (Alembic)

## Pre-Migration Phase ✓

- [x] Database backup created
- [x] Schema exported
- [x] Data summary exported
- [x] Row counts documented
- [x] Current state verified

**Backup Location:** `backups/yukyu_pre_migration_*.db`
**Schema Export:** `backups/schema_pre_migration_*.sql`
**Data Export:** `backups/data_export_pre_migration_*.json`

---

## Migration Phase

### Step 1: Test Migration on Copy Database
- [ ] Copy yukyu.db to yukyu-test.db
- [ ] Run `alembic upgrade head` on test database
- [ ] Verify migration succeeded
- [ ] Verify no data loss on test database
- [ ] Document any issues found

### Step 2: Execute Migration on Production Database
- [ ] Create fresh backup before running migration
- [ ] Set environment: `export DATABASE_URL="sqlite:///$(pwd)/yukyu.db"`
- [ ] Run `alembic upgrade head`
- [ ] Monitor migration progress
- [ ] Verify migration completed successfully

### Step 3: Post-Migration Verification
- [ ] Run `alembic current` to confirm revision
- [ ] Verify employees table has UUID id column
- [ ] Verify all tables have UUID id column
- [ ] Run validation script: `python scripts/validate-migration.py`
- [ ] Check row counts match pre-migration values
- [ ] Verify no NULL UUIDs in any table
- [ ] Test sample queries
- [ ] Check indexes are still intact

### Step 4: Application Restart
- [ ] Stop running application
- [ ] Update database.py with new UUIDs handling if needed
- [ ] Restart application: `python -m uvicorn main:app`
- [ ] Test core endpoints
- [ ] Check application logs for errors

---

## Rollback Phase (if needed)

- [ ] Stop application
- [ ] Restore from backup: `cp backups/yukyu_pre_migration_*.db yukyu.db`
- [ ] Run `alembic downgrade` if needed
- [ ] Restart application
- [ ] Verify application working correctly

---

## Success Criteria

- [x] All tables backed up
- [ ] Alembic migration runs successfully
- [ ] No data loss (row counts match)
- [ ] All UUIDs generated correctly
- [ ] No NULL UUIDs found
- [ ] All constraints intact
- [ ] All indexes intact
- [ ] Application works with new schema

---

## Timestamps

- **Pre-Migration Time:** $(date)
- **Migration Start Time:** _______________
- **Migration End Time:** _______________
- **Post-Migration Verification:** _______________

---

## Notes

Add any notes or issues found during migration below:

```

```
CHECKLIST_CONTENT

echo -e "${GREEN}✓${NC} Checklist created: $CHECKLIST_FILE"
echo ""

# Final summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}PRE-MIGRATION BACKUP COMPLETE${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Backup Files:${NC}"
echo "  • Database: $BACKUP_FILE"
echo "  • Schema: $SCHEMA_FILE"
echo "  • Data Summary: $DATA_EXPORT"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review MIGRATION_CHECKLIST.md"
echo "  2. Test migration on copy: cp $DB_FILE yukyu-test.db"
echo "  3. Run: export DATABASE_URL='sqlite:///\$(pwd)/yukyu.db'"
echo "  4. Test: alembic upgrade head (on test database first)"
echo "  5. Verify: python scripts/validate-migration.py"
echo ""
