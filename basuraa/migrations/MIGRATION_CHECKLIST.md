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
