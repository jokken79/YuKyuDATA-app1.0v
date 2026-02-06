import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


BACKUP_DIR = Path(__file__).parent.parent / "backups"
MAX_BACKUPS = 10


def _get_db_path() -> Path:
    """Get the SQLite database file path."""
    db_url = os.getenv('DATABASE_URL', 'sqlite:///yukyu.db')
    if 'sqlite' in db_url:
        db_file = db_url.replace('sqlite:///', '')
        return Path(db_file)
    return Path('yukyu.db')


def create_backup() -> Dict[str, Any]:
    """Create a SQLite database backup."""
    BACKUP_DIR.mkdir(exist_ok=True)

    db_path = _get_db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"yukyu_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / filename

    shutil.copy2(str(db_path), str(backup_path))

    # Keep only last MAX_BACKUPS
    backups = sorted(BACKUP_DIR.glob("yukyu_backup_*.db"), key=lambda p: p.stat().st_mtime)
    while len(backups) > MAX_BACKUPS:
        oldest = backups.pop(0)
        oldest.unlink()

    return {
        'filename': filename,
        'path': str(backup_path),
        'size_bytes': backup_path.stat().st_size,
        'created_at': datetime.now().isoformat(),
    }


def list_backups() -> List[Dict[str, Any]]:
    """List all available database backups."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for f in sorted(BACKUP_DIR.glob("yukyu_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True):
        stat = f.stat()
        backups.append({
            'filename': f.name,
            'size_bytes': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return backups


def restore_backup(filename: str) -> Dict[str, Any]:
    """Restore database from a backup file."""
    backup_path = BACKUP_DIR / filename
    if not backup_path.exists():
        raise ValueError(f"Backup not found: {filename}")

    db_path = _get_db_path()

    # Create safety backup before restore
    if db_path.exists():
        safety_name = f"yukyu_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        safety_path = BACKUP_DIR / safety_name
        BACKUP_DIR.mkdir(exist_ok=True)
        shutil.copy2(str(db_path), str(safety_path))

    shutil.copy2(str(backup_path), str(db_path))

    return {
        'restored_from': filename,
        'restored_at': datetime.now().isoformat(),
        'db_path': str(db_path),
    }
