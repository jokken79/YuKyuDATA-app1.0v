---
name: yukyu-status
description: Muestra el estado completo del sistema YuKyu
version: 1.0.0
---

# /yukyu-status - Estado del Sistema

Muestra el estado completo del sistema YuKyuDATA.

## Verificaciones Rápidas

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

### 2. Status Dashboard
```bash
# Abrir en navegador
http://localhost:8000/status
```

### 3. API Docs
```bash
# Swagger UI
http://localhost:8000/docs

# ReDoc
http://localhost:8000/redoc
```

## Script de Estado

```bash
python scripts/project-status.py
```

**Output esperado:**
```
╔═══════════════════════════════════════════════════════════╗
║         YuKyu Dashboard - Project Status                  ║
╚═══════════════════════════════════════════════════════════╝

Database: yukyu.db (2.5 MB)
  - employees: 150 records
  - genzai: 80 records
  - ukeoi: 45 records
  - staff: 25 records
  - leave_requests: 234 records

Server: Running on http://localhost:8000
Tests: 45 passed, 0 failed
Coverage: 82%
```

## Verificar Componentes

### Base de Datos
```bash
sqlite3 yukyu.db "SELECT COUNT(*) FROM employees WHERE year = 2025;"
```

### Archivos Excel
```bash
# Verificar existencia
ls -la "有給休暇管理.xlsm"
ls -la "【新】社員台帳(UNS)T　2022.04.05～.xlsm"
```

### Logs
```bash
# Últimas 50 líneas
tail -50 logs/app.log

# Buscar errores
grep "ERROR" logs/app.log
```

### Espacio en Disco
```bash
# Linux/Mac
df -h .

# Windows
dir
```

## Indicadores de Salud

| Componente | Estado Esperado |
|------------|-----------------|
| API | Responde en <100ms |
| Database | Integrity check: ok |
| Disk | >500MB disponibles |
| Memory | <80% uso |
| Logs | Sin errores críticos |
