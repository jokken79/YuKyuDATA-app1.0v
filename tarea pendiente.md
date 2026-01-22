# Tareas Pendientes - Auditoría YuKyuDATA

**Fecha de auditoría:** 2026-01-22
**Versión analizada:** 1.0v
**Estado general:** Bueno con mejoras requeridas

---

## Resumen de Puntuaciones

| Área | Puntuación | Estado |
|------|------------|--------|
| Arquitectura/APIs | 8.5/10 | Excelente |
| UI/UX | 7.5/10 | Buena con mejoras |
| Seguridad | 7.5/10 | Requiere fixes |
| Compliance Legal | 9.5/10 | Excepcional |

---

## Tareas Críticas (Esta semana)

### [ ] 1. Rotar JWT_SECRET_KEY
- **Severidad:** CRÍTICA
- **Archivo:** `.env`
- **Problema:** Clave expuesta en historial de git
- **Acción:**
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  # Actualizar JWT_SECRET_KEY en .env
  ```

### [ ] 2. Remover .env del repositorio
- **Severidad:** CRÍTICA
- **Acción:**
  ```bash
  git rm --cached .env
  echo ".env" >> .gitignore
  ```

### [ ] 3. Corregir CORS headers
- **Severidad:** MEDIA
- **Archivo:** `main.py:240`
- **Problema:** `allow_headers=["*"]` permite cualquier header
- **Solución:**
  ```python
  allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "Accept-Language"]
  ```

---

## Tareas Urgentes (Este mes)

### [ ] 4. Agregar responsive design móvil
- **Severidad:** MEDIA
- **Archivos:** `static/css/unified-design-system.css`
- **Problema:** Solo 1 media query, sin breakpoints móviles
- **Solución:**
  ```css
  @media (max-width: 768px) {
      .dashboard-grid { grid-template-columns: 1fr; }
      .stat-card { padding: 1rem; }
      .modal-container { width: 90vw; }
  }

  @media (max-width: 480px) {
      body { font-size: 14px; }
  }
  ```

### [ ] 5. Implementar URL routing / deep linking
- **Severidad:** MEDIA
- **Archivo:** `static/js/app.js`
- **Problema:** No se pueden compartir links a páginas específicas
- **Solución:**
  ```javascript
  window.addEventListener('hashchange', () => {
      const view = location.hash.slice(1) || 'dashboard';
      App.navigate(view);
  });
  ```

### [ ] 6. Corregir SQL injection potencial
- **Severidad:** MEDIA
- **Archivo:** `services/reports.py:211`
- **Problema:** Interpolación de nombre de tabla
- **Solución:** Usar CASE o diccionario de funciones

### [ ] 7. Agregar Content-Security-Policy header
- **Severidad:** BAJA
- **Archivo:** `middleware/security_headers.py`
- **Solución:**
  ```python
  "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
  ```

---

## Tareas Importantes (Este trimestre)

### [ ] 8. Mover tokens JWT a httpOnly cookies
- **Severidad:** BAJA
- **Archivos:** `static/js/app.js`, `services/auth_service.py`
- **Problema:** localStorage vulnerable a XSS
- **Solución:** Usar cookies httpOnly con SameSite=Strict

### [ ] 9. Eliminar console.logs de producción
- **Severidad:** BAJA
- **Archivo:** `static/js/app.js`
- **Problema:** 78 console.logs exponen información
- **Solución:**
  ```javascript
  const logger = {
      debug: (msg) => process.env.NODE_ENV === 'development' && console.log(msg),
      info: console.info,
      error: console.error
  };
  ```

### [ ] 10. Completar Storybook para componentes
- **Severidad:** BAJA
- **Directorio:** `static/src/components/`
- **Problema:** Solo Modal.stories.js existe
- **Acción:** Crear stories para los 16 componentes

### [ ] 11. Implementar rate limiter distribuido
- **Severidad:** BAJA
- **Archivo:** `middleware/rate_limiter.py`
- **Problema:** Rate limit en memoria, no funciona con múltiples workers
- **Solución:** Usar Redis para límites compartidos

### [ ] 12. Escapar valores numéricos en frontend
- **Severidad:** BAJA
- **Archivo:** `static/js/app.js:1229`
- **Problema:** Valores numéricos no escapados (XSS potencial)
- **Solución:**
  ```javascript
  const granted = App.utils.escapeHtml(String(e.granted));
  ```

---

## Mejoras Opcionales

### [ ] 13. Consolidar archivos CSS de tokens
- **Archivos:** `unified-design-system.css`, `yukyu-tokens.css`
- **Problema:** Tokens duplicados/conflictivos

### [ ] 14. Implementar state management reactivo
- **Archivo:** `static/js/app.js`
- **Problema:** Estado global sin reactividad
- **Solución:** Considerar Zustand o similar

### [ ] 15. Agregar logs centralizados
- **Problema:** Logs solo en stdout/archivo local
- **Solución:** Integrar Sentry o ELK Stack

### [ ] 16. Respetar prefers-color-scheme
- **Archivo:** `static/js/modules/theme-manager.js`
- **Problema:** No detecta preferencia del sistema
- **Solución:**
  ```javascript
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  ```

---

## Vulnerabilidades Identificadas

| ID | Vulnerabilidad | Severidad | Archivo | Línea |
|----|----------------|-----------|---------|-------|
| V1 | Secretos en git | CRÍTICA | .env | - |
| V2 | Wildcard CORS headers | MEDIA | main.py | 240 |
| V3 | Interpolación tabla SQL | MEDIA | reports.py | 211 |
| V4 | CSRF sin estado server-side | BAJA | csrf.py | 128 |
| V5 | Contraseña sin complejidad | BAJA | models/user.py | 127 |
| V6 | Rate limiter en memoria | BAJA | rate_limiter.py | 120 |
| V7 | XSS valores numéricos | BAJA | app.js | 1229 |
| V8 | Sin CSP header | BAJA | security_headers.py | 95 |
| V9 | Fallback JWT_REFRESH débil | BAJA | auth_service.py | 53 |

---

## Fortalezas Identificadas

- Arquitectura en capas bien definida (Routes → Services → Repositories → Database)
- 50+ endpoints REST organizados en 21 módulos
- Sistema JWT con refresh tokens persistentes en BD
- Compliance legal japonés excepcional (労働基準法 第39条)
- Audit trail con hashing SHA-256 chain-linked
- 14 agentes especializados con circuit breaker
- Design system unificado con Dark/Light mode
- PWA completo con offline support
- i18n (japonés, español, inglés)

---

## Notas Adicionales

- Los directorios `basuraa/` y `ThemeTheBestJpkken/` están excluidos de CI/CD (código legacy)
- Pytest markers disponibles: `unit`, `integration`, `pooling`, `slow`, `e2e`, `flaky`
- La tabla GRANT_TABLE es exacta según 労働基準法 Art. 39.2

---

**Próxima revisión recomendada:** 2026-02-22
