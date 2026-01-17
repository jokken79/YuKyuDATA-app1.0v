---
name: yukyu-backup
description: Crea y gestiona backups de la base de datos YuKyu
version: 1.0.0
---

# /yukyu-backup - Gestión de Backups

Crea y gestiona backups de la base de datos de YuKyuDATA.

## Crear Backup Manual

### Usando SQLite
```bash
sqlite3 yukyu.db ".backup backups/yukyu_backup_$(date +%Y%m%d_%H%M%S).db"
```

### Usando copy (Windows)
```batch
copy yukyu.db backups\yukyu_backup_%date:~0,4%%date:~5,2%%date:~8,2%.db
```

### Usando API
```bash
curl -X POST http://localhost:8000/api/backup \
  -H "Authorization: Bearer <token>"
```

## Listar Backups

```bash
# Linux/Mac
ls -la backups/

# Windows
dir backups\
```

## Restaurar Backup

```bash
# 1. Detener servidor
# 2. Copiar backup
cp backups/yukyu_backup_20250117.db yukyu.db

# 3. Reiniciar servidor
```

## Política de Retención

- **Mantener:** Últimos 10 backups
- **Frecuencia recomendada:** Diaria
- **Almacenamiento:** Mínimo 100MB disponible

## Backup Automático

Agregar a crontab (Linux) o Task Scheduler (Windows):

```bash
# Crontab - Cada día a las 3:00 AM
0 3 * * * cd /path/to/yukyu && sqlite3 yukyu.db ".backup backups/yukyu_$(date +\%Y\%m\%d).db"
```

## Verificar Integridad

```bash
sqlite3 yukyu.db "PRAGMA integrity_check;"
```

**Resultado esperado:** `ok`
