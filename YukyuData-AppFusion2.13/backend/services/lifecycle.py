
import os
import shutil
from pathlib import Path
from fastapi import FastAPI
from services import excel_service
import database
from utils.logger import logger
from config.secrets_validation import validate_secrets

# Constants needed for auto-sync
# In a perfect world these would be in a config file, but we'll import them or define them here.
# For now, defining them relative to project root assuming this file is in services/
PROJECT_DIR = Path(__file__).parent.parent
DEFAULT_EXCEL_PATH = PROJECT_DIR / "有給休暇管理.xlsm"
EMPLOYEE_REGISTRY_PATH = PROJECT_DIR / "【新】社員台帳(UNS)T　2022.04.05～.xlsm"

def auto_sync_on_startup():
    """
    Sincroniza automáticamente los datos desde Excel si la base de datos está vacía.
    Esto asegura que los datos persisten y no hay que sincronizar manualmente cada vez.
    También crea un backup automático si la BD tiene datos.
    """
    try:
        # Check if employees table is empty
        employees = database.get_employees()

        # If database has data, create automatic backup on startup
        if len(employees) > 0:
            try:
                backup_result = database.create_backup()
                logger.info(f"🔒 Auto-backup created: {backup_result['filename']}")
            except Exception as backup_err:
                logger.warning(f"⚠️ Auto-backup failed (non-critical): {str(backup_err)}")

        if len(employees) == 0:
            logger.info("📊 Database is empty - attempting auto-sync from Excel...")

            # Try to sync vacation data
            if DEFAULT_EXCEL_PATH.exists():
                logger.info(f"📁 Found vacation Excel: {DEFAULT_EXCEL_PATH}")
                data = excel_service.parse_excel_file(DEFAULT_EXCEL_PATH)
                database.save_employees(data)

                # Also parse usage details
                usage_details = excel_service.parse_yukyu_usage_details(DEFAULT_EXCEL_PATH)
                database.save_yukyu_usage_details(usage_details)

                logger.info(f"✅ Auto-synced {len(data)} employees + {len(usage_details)} usage details")
            else:
                logger.warning(f"⚠️ Vacation Excel not found at: {DEFAULT_EXCEL_PATH}")

            # Try to sync Genzai (dispatch employees)
            if EMPLOYEE_REGISTRY_PATH.exists():
                logger.info(f"📁 Found employee registry: {EMPLOYEE_REGISTRY_PATH}")

                genzai_data = excel_service.parse_genzai_sheet(EMPLOYEE_REGISTRY_PATH)
                database.save_genzai(genzai_data)
                logger.info(f"✅ Auto-synced {len(genzai_data)} dispatch employees (Genzai)")

                ukeoi_data = excel_service.parse_ukeoi_sheet(EMPLOYEE_REGISTRY_PATH)
                database.save_ukeoi(ukeoi_data)
                logger.info(f"✅ Auto-synced {len(ukeoi_data)} contract employees (Ukeoi)")
            else:
                logger.warning(f"⚠️ Employee registry not found at: {EMPLOYEE_REGISTRY_PATH}")
        else:
            logger.info(f"✅ Database already has {len(employees)} employees - skipping auto-sync")

    except Exception as e:
        logger.error(f"❌ Auto-sync failed: {str(e)}")
        # Don't raise - allow server to start even if sync fails

def register_lifecycle_events(app: FastAPI):
    """
    Register startup and shutdown events for the application.
    """
    
    @app.on_event("startup")
    async def startup_event():
        """
        Initialization on application startup.
        - Validates production secrets configuration
        - Initializes database connection pool (for PostgreSQL)
        - Runs auto-sync if database is empty
        - Creates backup if database has data
        - Initializes Auth Service (Refresh Tokens)
        """
        try:
            logger.info("Starting up YuKyuDATA application...")

            # Validate secrets configuration (critical for production security)
            logger.info("Validating secrets configuration...")
            is_valid, errors, warnings = validate_secrets(exit_on_failure=True)

            if warnings:
                for warning in warnings:
                    logger.warning(f"Security warning: {warning}")

            if is_valid:
                logger.info("Secrets validation passed")
            else:
                # In development mode, log errors but continue
                for error in errors:
                    logger.error(f"Security error: {error}")

            # Initialize connection pool if using PostgreSQL
            if database.USE_POSTGRESQL:
                logger.info("🔌 Initializing PostgreSQL connection pool...")
                from database.connection import PostgreSQLConnectionPool
                database_url = os.getenv('DATABASE_URL')
                pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
                pool_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
                PostgreSQLConnectionPool.initialize(database_url, pool_size, pool_overflow)
                logger.info(f"✅ PostgreSQL pool initialized: {pool_size} min, {pool_overflow} max connections")
            else:
                logger.info("🗄️  Using SQLite database (no connection pool)")

            # Run auto-sync
            auto_sync_on_startup()
            
            # Initialize Auth Service (Refresh Tokens)
            # Import here to avoid circular dependencies if any
            from services.auth_service import auth_service
            auth_service.initialize()

            logger.info("✅ Startup complete")
        except Exception as e:
            logger.error(f"❌ Startup error: {str(e)}", exc_info=True)
            raise

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Cleanup on application shutdown.
        - Closes all database connections in the pool
        """
        try:
            logger.info("🛑 Shutting down YuKyuDATA application...")

            if database.USE_POSTGRESQL:
                logger.info("🔌 Closing PostgreSQL connection pool...")
                from database.connection import PostgreSQLConnectionPool
                PostgreSQLConnectionPool.close_pool()
                logger.info("✅ Connection pool closed")

            logger.info("✅ Shutdown complete")
        except Exception as e:
            logger.error(f"⚠️  Shutdown error: {str(e)}", exc_info=True)
