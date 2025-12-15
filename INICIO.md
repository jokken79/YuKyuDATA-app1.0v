# Cómo Iniciar el Servidor

## Opción 1: Con Selección de Puerto (Recomendado)

Ejecuta:
```
start_app.bat
```

Te pedirá que ingreses el puerto. Simplemente presiona Enter para usar 8000 por defecto, o escribe otro número.

## Opción 2: Inicio Rápido con Puertos Predefinidos

### Puerto 8000 (Por defecto)
```
start_quick_8000.bat
```

### Puerto 3000
```
start_quick_3000.bat
```

### Puerto 5000
```
start_quick_5000.bat
```

## Opción 3: Línea de Comandos Manual

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port PUERTO_DESEADO
```

Ejemplo con puerto 9000:
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 9000
```

## Acceder al Sistema

Una vez iniciado el servidor, abre tu navegador en:
- **Dashboard**: http://localhost:PUERTO/
- **API Docs (Swagger)**: http://localhost:PUERTO/docs
- **API**: http://localhost:PUERTO/api/

## Detener el Servidor

Presiona `Ctrl+C` en la terminal donde está corriendo el servidor.

## Problemas Comunes

### Error: "Address already in use"
El puerto ya está siendo usado. Soluciones:
1. Usa otro puerto
2. Cierra el proceso que está usando ese puerto
3. En Windows, busca y mata el proceso:
   ```
   netstat -ano | findstr :8000
   taskkill /PID [número_de_proceso] /F
   ```

### El navegador no abre automáticamente
Abre manualmente: http://localhost:PUERTO/

### Cambios en el código no se reflejan
El servidor tiene `--reload` activado, pero si no funciona:
1. Detén el servidor (Ctrl+C)
2. Inicia nuevamente
