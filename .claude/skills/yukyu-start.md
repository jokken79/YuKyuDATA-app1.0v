---
name: yukyu-start
description: Inicia el servidor de YuKyuDATA con verificaciones de entorno
version: 1.0.0
---

# /yukyu-start - Iniciar Servidor YuKyu

Inicia el servidor de desarrollo de YuKyuDATA con todas las verificaciones necesarias.

## Pasos

1. **Verificar Python**
   ```bash
   python --version
   ```

2. **Activar entorno virtual**
   ```bash
   # Windows
   venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

3. **Verificar dependencias**
   ```bash
   pip show fastapi uvicorn
   ```

4. **Verificar .env**
   - Si no existe, crear con valores por defecto

5. **Iniciar servidor**
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Resultado Esperado

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## URLs

- **App:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Status:** http://localhost:8000/status
