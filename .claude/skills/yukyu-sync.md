---
name: yukyu-sync
description: Sincroniza datos desde archivos Excel a la base de datos
version: 1.0.0
---

# /yukyu-sync - Sincronizar Datos Excel

Sincroniza datos desde los archivos Excel maestros a la base de datos SQLite.

## Archivos Excel Requeridos

Los archivos deben estar en la raíz del proyecto:

1. **有給休暇管理.xlsm** - Master de vacaciones
2. **【新】社員台帳(UNS)T　2022.04.05～.xlsm** - Registro de empleados

## Endpoints de Sincronización

### Vacaciones (Principal)
```bash
curl -X POST http://localhost:8000/api/sync
```

### Empleados de Despacho (Genzai)
```bash
curl -X POST http://localhost:8000/api/sync-genzai
```

### Empleados Contratistas (Ukeoi)
```bash
curl -X POST http://localhost:8000/api/sync-ukeoi
```

### Personal de Oficina (Staff)
```bash
curl -X POST http://localhost:8000/api/sync-staff
```

### Sync Completo (Todo)
```bash
# Ejecutar en secuencia
curl -X POST http://localhost:8000/api/sync
curl -X POST http://localhost:8000/api/sync-genzai
curl -X POST http://localhost:8000/api/sync-ukeoi
curl -X POST http://localhost:8000/api/sync-staff
```

## Respuesta Esperada

```json
{
  "status": "success",
  "message": "Sync completed",
  "stats": {
    "total_rows": 150,
    "inserted": 10,
    "updated": 140,
    "errors": 0
  }
}
```

## Troubleshooting

### Error: Archivo no encontrado
- Verificar que el archivo Excel existe en la raíz
- Verificar nombre exacto (incluyendo caracteres japoneses)

### Error: Hoja no encontrada
- Verificar nombres de hojas: DBGenzaiX, DBUkeoiX, DBStaffX

### Error: Archivo bloqueado
- Cerrar Excel si está abierto
