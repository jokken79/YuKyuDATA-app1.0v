# FASE 3 Phase 5: Testing & Validation

## Overview

Phase 5 implements comprehensive testing for the PostgreSQL migration, ensuring:
- SQLite backward compatibility
- PostgreSQL functionality
- Connection pooling reliability
- Data integrity across databases

## Test Suites

### 1. Unit Tests: Database Compatibility (`test_database_compatibility.py`)

Tests SQLite and PostgreSQL dual-database support without requiring actual database connections.

**Coverage:**
- Connection initialization (SQLite/PostgreSQL)
- Parameter placeholder handling (? vs %s)
- UPSERT functionality (INSERT OR REPLACE vs ON CONFLICT)
- Encryption/Decryption consistency
- All data types and constraints

**Key Test Classes:**
- `TestDatabaseConnectionInit` - Connection setup
- `TestParameterPlaceholders` - Query parameter handling
- `TestEmployeeSaveCompatibility` - Employee CRUD operations
- `TestEncryptionCompatibility` - Encryption/decryption
- `TestGenzaiSaveCompatibility` - Dispatch employee data
- `TestLeaveRequestCompatibility` - Leave request workflow
- `TestYukyuUsageDetailsCompatibility` - Usage tracking
- `TestDatabaseInitialization` - Schema creation

**Run:**
```bash
pytest tests/test_database_compatibility.py -v
```

### 2. Integration Tests: PostgreSQL (`test_postgresql_integration.py`)

Tests actual PostgreSQL functionality using real database connections.

**Prerequisites:**
```bash
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:pass@localhost:5432/yukyu
```

**Coverage:**
- PostgreSQL connection establishment
- Table creation and schema validation
- Primary keys and constraints
- UPSERT with ON CONFLICT
- Data integrity and encryption
- Timestamps and auto-increment
- Unique constraints

**Key Test Classes:**
- `TestPostgreSQLConnection` - Connection pooling
- `TestPostgreSQLTableCreation` - Schema validation
- `TestPostgreSQLUpsertFunctionality` - UPSERT operations
- `TestPostgreSQLDataIntegrity` - Data consistency
- `TestPostgreSQLConstraints` - Constraint enforcement
- `TestPostgreSQLIndexes` - Index creation
- `TestPostgreSQLReturningClause` - Auto-increment handling

**Run:**
```bash
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:pass@localhost:5432/yukyu
pytest tests/test_postgresql_integration.py -v
```

### 3. Connection Pooling Tests (`test_connection_pooling.py`)

Tests PostgreSQL connection pool functionality and concurrency.

**Prerequisites:**
Same as integration tests (requires PostgreSQL)

**Coverage:**
- Pool initialization
- Connection acquisition and release
- Concurrent access (10+ workers)
- Pool limits enforcement
- Connection reuse after errors
- Graceful cleanup
- Environment variable configuration

**Key Test Classes:**
- `TestConnectionPoolBasics` - Pool initialization
- `TestConnectionPoolConcurrency` - Multi-threaded access
- `TestConnectionPoolWithDatabase` - Database integration
- `TestConnectionPoolCleanup` - Shutdown procedures
- `TestConnectionPoolErrorHandling` - Error recovery
- `TestPoolConfigurationFromEnvironment` - Configuration management

**Run:**
```bash
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://user:pass@localhost:5432/yukyu
pytest tests/test_connection_pooling.py -v
```

## Test Configuration

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
markers =
    unit: Unit tests
    integration: Integration tests
    pooling: Pooling tests
addopts = -v --tb=short
```

### conftest.py

Provides shared fixtures:
- `database_type` - Current database configuration
- `database_url` - Database connection URL
- `sample_*_data` - Test data fixtures for all entity types

## Running Tests

### Test Runner Script

```bash
# Run all tests
python scripts/run_tests.py

# Run SQLite tests only
python scripts/run_tests.py --sqlite-only

# Run PostgreSQL tests only (requires PostgreSQL configured)
python scripts/run_tests.py --postgresql-only

# Show help
python scripts/run_tests.py --help
```

### Manual pytest Commands

```bash
# All tests
pytest tests/ -v

# Specific suite
pytest tests/test_database_compatibility.py -v

# With markers
pytest -m unit -v           # Unit tests
pytest -m integration -v    # Integration tests
pytest -m pooling -v        # Pooling tests

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## Environment Setup

### For SQLite Tests (Default)
```bash
# No setup needed - uses in-memory/temp SQLite databases
pytest tests/test_database_compatibility.py
```

### For PostgreSQL Tests

1. **Install PostgreSQL (Docker recommended)**
```bash
docker run -d \
  --name postgres-test \
  -e POSTGRES_USER=yukyu_user \
  -e POSTGRES_PASSWORD=change_me \
  -e POSTGRES_DB=yukyu \
  -p 5432:5432 \
  postgres:15-alpine
```

2. **Set environment variables**
```bash
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://yukyu_user:change_me@localhost:5432/yukyu

# Optional: Connection pool configuration
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20
```

3. **Run migrations (Alembic)**
```bash
alembic upgrade head
```

4. **Run tests**
```bash
python scripts/run_tests.py
```

## Test Data

All tests use sample data in JSON-like dictionaries:

### Employee Sample
```python
{
    'id': 'EMP001_2025',
    'employeeNum': 'EMP001',
    'name': '田中太郎',
    'haken': '工場A',
    'granted': 20.0,
    'used': 5.0,
    'balance': 15.0,
    'expired': 0.0,
    'usageRate': 25.0,
    'year': 2025
}
```

### Encrypted Fields
Tests verify encryption/decryption for:
- `birth_date` (all employee types)
- `hourly_wage` (genzai, ukeoi)
- `address`, `postal_code`, `visa_type` (staff)

## Expected Results

### SQLite Tests
✅ All 50+ tests should pass
- Database compatibility verified
- Parameter placeholders working
- UPSERT logic correct
- Encryption/decryption working

### PostgreSQL Tests (when configured)
✅ All 40+ tests should pass
- Connection pool working
- Tables created with Alembic
- ON CONFLICT UPSERT working
- Constraints enforced
- Encryption/decryption working

### Connection Pooling Tests (when PostgreSQL configured)
✅ All 30+ tests should pass
- Pool initialization successful
- Concurrent access working
- Max connections enforced
- Error recovery working
- Graceful shutdown working

## Troubleshooting

### "PostgreSQL not configured" message
Solution: Set `DATABASE_TYPE=postgresql` and `DATABASE_URL` environment variables

### Tests skipped with no PostgreSQL
This is expected behavior - tests gracefully skip when PostgreSQL is not available

### "Cannot connect to PostgreSQL"
Check:
1. PostgreSQL server is running
2. `DATABASE_URL` is correct
3. Database/user/password exist
4. Network connectivity (if remote)

### Test timeout (> 5 minutes)
May indicate:
- Slow network/database
- Connection pool exhaustion
- Hanging threads

Try increasing timeout or reducing concurrent tests

## Continuous Integration

For CI/CD pipelines (GitHub Actions, GitLab CI, etc.):

```yaml
test-sqlite:
  script:
    - pip install pytest
    - pytest tests/test_database_compatibility.py -v

test-postgresql:
  script:
    - pip install pytest psycopg2-binary
    - export DATABASE_TYPE=postgresql
    - export DATABASE_URL=postgresql://test:test@postgres:5432/test
    - alembic upgrade head
    - pytest tests/ -v
  services:
    - postgres:15
```

## Next Steps

After Phase 5 testing is complete:

1. **Phase 6: Deployment Strategy**
   - Production deployment steps
   - Migration procedures
   - Rollback strategies

2. **Phase 9: Full-Text Search**
   - PostgreSQL tsvector
   - GIN indexes
   - Search API endpoints

3. **Phase 10: PITR Backups**
   - WAL archiving
   - Point-in-time recovery
   - Backup automation

## Metrics & Success Criteria

✅ **Phase 5 Success Criteria:**
- [ ] All SQLite unit tests pass (50+)
- [ ] All PostgreSQL integration tests pass (40+) or gracefully skip
- [ ] All connection pooling tests pass (30+) or gracefully skip
- [ ] 100% backward compatibility with SQLite maintained
- [ ] No data loss during migration
- [ ] Encryption/decryption working in both databases
- [ ] Connection pool handling 10+ concurrent connections
- [ ] Error recovery working correctly

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [PostgreSQL Testing](https://www.postgresql.org/)
- [psycopg2 Connection Pooling](https://www.psycopg.org/psycopg2/docs/extras.html#class-threadedconnectionpool)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/faq/testing.html)

---

**Phase 5 Status:** Testing & Validation in progress
**Last Updated:** 2025-12-23
**Next Phase:** Phase 6 - Deployment Strategy
