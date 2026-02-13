# YuKyuData AppFusion 2.13

Esta es la versión fusionada de **YuKyuDATA-app1.0v** (Backend Python) y **JpYuKyu12.24V1.0** (Frontend React).

## 🚀 Cómo Ejecutar

Simplemente haz doble clic en el archivo:
**`start_fusion.bat`**

Este script se encargará de:
1.  Verificar que tengas Node.js y Python instalados.
2.  Crear el entorno virtual de Python e instalar dependencias (si es la primera vez).
3.  Instalar las dependencias de Node.js (si es la primera vez).
4.  Iniciar ambos servidores (Backend en puerto 8000, Frontend en puerto 3000).

## 📂 Estructura

*   **`backend/`**: El cerebro de la aplicación.
    *   **Tecnología**: Python, FastAPI, SQLite.
    *   **Puerto**: 8000.
    *   **Base de Datos**: `yukyu.db` (SQLite).
    *   **Seguridad**: JWT, CSRF, Rate Limiting.

*   **`frontend/`**: La interfaz de usuario moderna.
    *   **Tecnología**: React 19, Vite, TypeScript, Tailwind CSS.
    *   **Puerto**: 3000.
    *   **Configuración**: Proxy configurado para redirigir peticiones `/api` al backend.

## 🔧 Configuración

*   **Backend**: Archivo `.env` en directorio `backend/`.
*   **Frontend**: Archivo `.env` en directorio `frontend/` (opcional, para keys de API publicas).

## 👥 Desarrollo

Para desarrollar:
1.  Ejecuta `start_fusion.bat`.
2.  Abre `frontend/` en tu editor para cambios visuales (Hot Reload activo).
3.  Abre `backend/` para cambios de lógica (Auto-reload activo).

---
*Fusión realizada por Antigravity Agent el 2026-02-13.*
