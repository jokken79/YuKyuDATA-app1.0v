# Backlog consolidado de pendientes Markdown

Generado automáticamente: 2026-02-19

## Resumen
- Archivos con pendientes: **28**
- Ítems pendientes detectados: **522**

## Top archivos con más pendientes
- `docs/MIGRATION_PLAN.md`: 96
- `docs/IMPLEMENTATION_PLAN.md`: 77
- `docs/PRODUCTION_CHECKLIST.md`: 56
- `static/src/legacy-bridge/MIGRATION_GUIDE.md`: 25
- `docs/UNIFIED_BRIDGE_SUMMARY.md`: 24
- `.github/ISSUE_TEMPLATE/claude_suggestion.md`: 24
- `FRONTEND-MIGRATION-GUIDE.md`: 21
- `static/js/RESUMEN-REFACTORING.md`: 21
- `.github/ISSUE_TEMPLATE/feature_request.md`: 16
- `docs/RUNBOOKS.md`: 15
- `UI-UX-FIXES-SUMMARY.md`: 14
- `docs/DATABASE_ADAPTER_README.md`: 13
- `scripts/disaster-recovery/RUNBOOK.md`: 13
- `tests/README.md`: 12
- `UI-UX-AUDIT-VISUAL-SUMMARY.md`: 10

## Pendientes por archivo

### `docs/MIGRATION_PLAN.md` (96)
- [ ] L91: `middleware/deprecation.py` creado
- [ ] L92: Middleware registrado en main.py
- [ ] L93: Tests de deprecation headers
- [ ] L118: app.js actualizado
- [ ] L119: constants.js actualizado
- [ ] L120: Managers verificados
- [ ] L121: Tests E2E pasando
- [ ] L208: Deprecation middleware activo
- [ ] L209: Frontend 100% en v1
- [ ] L210: Metricas muestran 0 requests v0
- [ ] L211: Archivos v0 eliminados
- [ ] L212: routes/__init__.py simplificado
- [ ] L213: main.py limpio
- [ ] L214: Tests actualizados y pasando
- [ ] L215: Documentacion actualizada
- [ ] L246: save_employees (bulk insert)
- [ ] L247: save_genzai / save_ukeoi / save_staff
- [ ] L248: validate_balance_limit
- [ ] L249: get_employee_total_balance
- [ ] L250: get_employee_hourly_wage
- [ ] L251: bulk_update_employees
- [ ] L252: revert_bulk_update
- [ ] L253: get_bulk_update_history
- [ ] L254: create_backup / restore_backup
- [ ] L255: log_audit
- [ ] L256: get_audit_log / get_audit_stats
- [ ] L257: cleanup_old_audit_logs
- [ ] L258: Todas las funciones de refresh_tokens
- [ ] L259: get_stats_by_factory
- [ ] L260: get_monthly_usage_summary
- [ ] L261: recalculate_employee_from_details
- [ ] L262: delete_old_yukyu_records
- [ ] L324: save_employees_orm implementado y testeado
- [ ] L325: save_genzai_orm implementado y testeado
- [ ] L326: save_ukeoi_orm implementado y testeado
- [ ] L327: save_staff_orm implementado y testeado
- [ ] L412: validate_balance_limit_orm
- [ ] L413: get_employee_hourly_wage_orm
- [ ] L414: recalculate_employee_used_days_orm
- [ ] L415: get_stats_by_factory_orm
- [ ] L416: get_monthly_usage_summary_orm
- [ ] L480: bulk_update_employees_orm
- [ ] L481: revert_bulk_update_orm
- [ ] L482: get_bulk_update_history_orm
- [ ] L483: Tests de atomicidad
- [ ] L539: log_audit_orm
- [ ] L540: get_audit_log_orm
- [ ] L541: get_audit_stats_orm
- [ ] L542: cleanup_old_audit_logs_orm
- [ ] L543: Todas las funciones de refresh_token_orm
- [ ] L544: Tests de seguridad
- [ ] L586: create_backup_orm
- [ ] L587: list_backups_orm
- [ ] L588: restore_backup_orm
- [ ] L589: delete_old_yukyu_records_orm
- [ ] L590: clear_* functions
- [ ] L702: 100% funciones tienen version _orm
- [ ] L703: Tests de paridad pasan para todas las funciones
- [ ] L704: Benchmarks muestran performance aceptable
- [ ] L705: Feature flag funciona correctamente
- [ ] L706: Rollback testeado
- [ ] L707: database.py marcado como deprecated
- [ ] L708: Documentacion actualizada
- [ ] L709: USE_ORM=true en produccion por 2 semanas sin issues
- [ ] L710: database.py eliminado
- [ ] L796: Bridge bidireccional completo
- [ ] L797: Tests de sincronizacion
- [ ] L798: Documentacion de API del bridge
- [ ] L901: Dashboard.js completo con toda la funcionalidad
- [ ] L902: DashboardManager con logica de negocio
- [ ] L903: app.js delega a moderno
- [ ] L904: Tests pasando
- [ ] L905: Visual regression tests
- [ ] L923: Table.js mejorado con sorting, filtering
- [ ] L924: Pagination.js
- [ ] L925: SearchInput.js
- [ ] L926: BulkActionBar.js
- [ ] L927: EmployeeEditModal.js
- [ ] L930: Employees.js completo
- [ ] L931: EmployeesManager con toda la logica
- [ ] L932: Componentes especializados
- [ ] L933: Tests de funcionalidad completa
- [ ] L996: Todas las paginas migradas
- [ ] L997: Todas las utilidades migradas
- [ ] L998: Tests E2E pasando
- [ ] L999: 2 semanas sin errores en produccion
- [ ] L1045: Todas las paginas en static/src/
- [ ] L1046: Bridge eliminado (no necesario)
- [ ] L1047: app.js reducido a bootstrap
- [ ] L1048: Tests E2E 100% pasando
- [ ] L1049: Lighthouse score >= 90
- [ ] L1050: Todos los idiomas funcionando
- [ ] L1051: Dark/Light mode funcionando
- [ ] L1052: PWA funcionando
- [ ] L1053: No errores en console
- [ ] L1054: Documentacion de componentes actualizada

### `docs/IMPLEMENTATION_PLAN.md` (77)
- [ ] L57: Instalar dependencias
- [ ] L58: Configurar jest.config.js
- [ ] L59: Crear setup.js con mocks globales
- [ ] L60: Verificar que tests pasen
- [ ] L68: Completar auth.test.js (20 tests)
- [ ] L69: Completar components.test.js (18 tests)
- [ ] L70: Completar responsive.test.js (10 tests)
- [ ] L71: Completar theme.test.js (12 tests)
- [ ] L72: Completar accessibility.test.js (25 tests)
- [ ] L77: Agregar test step en GitHub Actions
- [ ] L78: Configurar Codecov para coverage tracking
- [ ] L79: Reporte automático de coverage
- [ ] L101: Reemplazar localStorage access
- [ ] L102: Usar `credentials: 'include'` en fetch
- [ ] L103: Implementar `static/js/security-improvements.js`
- [ ] L115: Generar CSRF tokens
- [ ] L116: Validar en POST/PUT/DELETE
- [ ] L117: Implementar en frontend
- [ ] L124: Usar `design-tokens.js`
- [ ] L125: Convertir a CSS variables
- [ ] L126: Documentar en Figma
- [ ] L129: Identificar duplicados
- [ ] L130: Mergear estilos similares
- [ ] L131: Usar `css-improvements.css`
- [ ] L132: PurgeCSS para remover no usados
- [ ] L137: Minificar CSS
- [ ] L138: Critical CSS inline
- [ ] L139: Media queries optimizadas
- [ ] L146: Audit con axe DevTools
- [ ] L147: Mejorar aria labels (priority)
- [ ] L148: Aumentar color contrast ratios
- [ ] L149: Mejorar keyboard navigation
- [ ] L152: Todos los inputs tienen labels
- [ ] L153: Botones tienen focus visible
- [ ] L154: Texto tiene suficiente contraste
- [ ] L155: Navegación por teclado funciona
- [ ] L158: Usar `jest-axe`
- [ ] L159: Tests de keyboard navigation
- [ ] L160: Tests de color contrast
- [ ] L172: Implementar IntersectionObserver
- [ ] L173: Usar `static/js/lazy-loading.js`
- [ ] L174: Soportar navegadores antiguos
- [ ] L177: Charts cargados bajo demanda
- [ ] L178: Componentes por sección
- [ ] L179: Reducir JS inicial
- [ ] L191: Crear stories para componentes
- [ ] L192: Documentar Button, Form, Card, Modal
- [ ] L193: Addon de accesibilidad
- [ ] L196: Crear design-tokens.json
- [ ] L197: Documentar en README
- [ ] L198: Figma/Zeplin export
- [ ] L201: Setup local
- [ ] L202: Testing guide
- [ ] L203: Component usage
- [ ] L204: CSS architecture
- [ ] L215: Configurar `lighthouserc.json`
- [ ] L216: Agregar step en CI/CD
- [ ] L217: Establecer baselines
- [ ] L220: Performance: 75→85
- [ ] L221: Accessibility: 82→90
- [ ] L222: Best Practices: 85→92
- [ ] L223: SEO: 90→95
- [ ] L246: Instalar dependencias testing
- [ ] L247: Crear 55+ tests
- [ ] L248: Setup Jest CI/CD
- [ ] L249: Implementar security-improvements.js
- [ ] L250: Crear design-tokens.js
- [ ] L253: Migrar JWT a HttpOnly cookies
- [ ] L254: Mejorar Aria labels (WCAG)
- [ ] L255: Implementar lazy loading
- [ ] L256: Setup Storybook básico
- [ ] L257: Optimizar CSS (consolidar + minify)
- [ ] L260: Audit de accesibilidad completo
- [ ] L261: Setup Lighthouse CI
- [ ] L262: Completar documentación
- [ ] L263: Crear developer guide
- [ ] L264: Testing de todo antes de merge

### `docs/PRODUCTION_CHECKLIST.md` (56)
- [ ] L21: **DB.1** Backup procedure tested end-to-end
- [ ] L27: **DB.2** Point-in-time recovery (PITR) validated
- [ ] L32: **DB.3** Automated backup script deployed
- [ ] L39: **DB.4** Connection pool configured
- [ ] L44: **DB.5** Critical indexes verified (15+ required)
- [ ] L49: **DB.6** Query performance baseline established
- [ ] L56: **DB.7** Database migrations tested
- [ ] L61: **DB.8** UUID migration validated (v6.0)
- [ ] L69: **DB.9** Data integrity checks passed
- [ ] L74: **DB.10** Database size monitoring enabled
- [ ] L87: **API.1** Rate limiting configured
- [ ] L93: **API.2** CSRF protection enabled
- [ ] L98: **API.3** Security headers implemented
- [ ] L107: **API.4** JWT authentication working
- [ ] L114: **API.5** Session management configured
- [ ] L121: **API.6** Health check endpoints responsive
- [ ] L128: **API.7** API logging configured
- [ ] L135: **API.8** API versioning active
- [ ] L149: **FE.1** Bundle size acceptable
- [ ] L157: **FE.2** Lazy loading implemented
- [ ] L164: **FE.3** Service worker active (PWA)
- [ ] L170: **FE.4** App manifest configured
- [ ] L178: **FE.5** WCAG AA compliance verified
- [ ] L184: **FE.6** Performance metrics acceptable
- [ ] L198: **OPS.1** Docker image builds successfully
- [ ] L205: **OPS.2** Docker image security hardened
- [ ] L211: **OPS.3** Environment variables validated
- [ ] L219: **OPS.4** Blue-green deployment script tested
- [ ] L225: **OPS.5** Container orchestration ready
- [ ] L234: **OPS.6** Logging infrastructure operational
- [ ] L240: **OPS.7** Monitoring stack deployed
- [ ] L248: **OPS.8** Disaster recovery plan documented
- [ ] L262: **QA.1** Unit tests passing
- [ ] L269: **QA.2** Integration tests passing
- [ ] L277: **QA.3** Critical E2E tests passing
- [ ] L284: **QA.4** Performance tests acceptable
- [ ] L291: **QA.5** Security tests passing
- [ ] L307: **DEPLOY.1** All code commits reviewed
- [ ] L313: **DEPLOY.2** Dependencies updated and validated
- [ ] L321: **DEPLOY.3** Smoke test suite prepared
- [ ] L327: **DEPLOY.4** Rollback procedure verified
- [ ] L335: **DEPLOY.5** Monitoring alerts active
- [ ] L341: **DEPLOY.6** Incident response plan ready
- [ ] L355: **POST.1** Application is accessible
- [ ] L361: **POST.2** Core functionality working
- [ ] L367: **POST.3** Database connectivity verified
- [ ] L372: **POST.4** API endpoints responsive
- [ ] L379: **POST.5** Error rates stable
- [ ] L385: **POST.6** Response time acceptable
- [ ] L391: **POST.7** Resource utilization normal
- [ ] L397: **POST.8** Logs clean and informative
- [ ] L405: **POST.9** Feature functionality verified
- [ ] L411: **POST.10** Performance stable
- [ ] L417: **POST.11** Load handling verified
- [ ] L423: **POST.12** Backup automation working
- [ ] L429: **POST.13** Full system health

### `static/src/legacy-bridge/MIGRATION_GUIDE.md` (25)
- [ ] L390: Entender la feature actual en legacy (app.js)
- [ ] L391: Crear componente moderno en `/static/src/components/`
- [ ] L392: Exportar desde `index.js`
- [ ] L393: Registrar en bridge: `bridge.registerModernComponent(...)`
- [ ] L394: Registrar feature: `bridge.registerFeature('name', 'modern')`
- [ ] L395: Reemplazar calls en legacy con `bridge.renderInLegacy(...)`
- [ ] L396: Sincronizar estado si es necesario
- [ ] L397: Testear en ambos sistemas (dark/light mode)
- [ ] L398: Verificar accesibilidad (WCAG AA)
- [ ] L399: Medir performance
- [ ] L400: Actualizar documentación
- [ ] L404: Usar `registerFeature(..., 'hybrid')`
- [ ] L405: Documentar qué parte es legacy vs modern
- [ ] L406: Testear interacción entre sistemas
- [ ] L407: Planificar siguiente fase de migración
- [ ] L408: Documentar pasos para completar migración
- [ ] L513: StatCards moderno
- [ ] L514: EmployeeTable híbrido (legacy + botones modernos)
- [ ] L517: LeaveRequests completamente moderno
- [ ] L518: ApprovalModals modernos
- [ ] L521: ChartWidget moderno
- [ ] L522: ReportsPage moderno
- [ ] L525: Remover código legacy innecesario
- [ ] L526: Optimizar bundle size
- [ ] L527: Documentación final

### `docs/UNIFIED_BRIDGE_SUMMARY.md` (24)
- [ ] L466: Entender la feature actual en legacy (app.js)
- [ ] L467: Crear componente moderno en `/static/src/components/`
- [ ] L468: Exportar desde `components/index.js`
- [ ] L469: Registrar con `bridge.registerModernComponent()`
- [ ] L470: Registrar feature con `bridge.registerFeature()`
- [ ] L471: Reemplazar calls legacy con `bridge.renderInLegacy()`
- [ ] L472: Sincronizar estado si es necesario
- [ ] L473: Testear en ambos modos (dark/light)
- [ ] L474: Verificar accesibilidad (WCAG AA)
- [ ] L475: Medir performance (< 50ms render)
- [ ] L476: Actualizar documentación
- [ ] L477: Pasar tests (jest + playwright)
- [ ] L519: Migrar Dashboard (hybrid)
- [ ] L520: Migrar Employees (hybrid)
- [ ] L523: Migrar Leave Requests (modern)
- [ ] L524: Crear FormComponents modernos
- [ ] L525: 50% legacy code removido
- [ ] L528: Analytics (modern)
- [ ] L529: Reports (modern)
- [ ] L530: 75% legacy code removido
- [ ] L533: Cleanup final
- [ ] L534: Remover app.js
- [ ] L535: 100% moderno
- [ ] L536: Performance optimizations

### `.github/ISSUE_TEMPLATE/claude_suggestion.md` (24)
- [ ] L15: Mejora de codigo
- [ ] L16: Optimizacion
- [ ] L17: Refactoring
- [ ] L18: Nueva funcionalidad
- [ ] L19: Correccion potencial
- [ ] L20: Deuda tecnica
- [ ] L52: Alto - Probado o basado en patrones conocidos
- [ ] L53: Medio - Logica solida pero no probado
- [ ] L54: Bajo - Idea experimental
- [ ] L58: Dependencia 1
- [ ] L59: Dependencia 2
- [ ] L63: Tests unitarios
- [ ] L64: Tests de integracion
- [ ] L65: Testing manual
- [ ] L66: No requiere tests adicionales
- [ ] L81: La sugerencia es relevante para el proyecto
- [ ] L82: No introduce problemas de seguridad
- [ ] L83: Es compatible con la arquitectura existente
- [ ] L84: El esfuerzo de implementacion es razonable
- [ ] L85: Tiene valor suficiente para justificar el cambio
- [ ] L88: Aprobar para implementacion
- [ ] L89: Requiere mas investigacion
- [ ] L90: Posponer (agregar a backlog)
- [ ] L91: Rechazar (explicar en comentarios)

### `FRONTEND-MIGRATION-GUIDE.md` (21)
- [ ] L270: Create `data-service-v2.js` (fetch API, no jQuery)
- [ ] L271: Create `auth-service-v2.js`
- [ ] L272: Create `theme-manager-v2.js`
- [ ] L273: Update `app.js` to import new services
- [ ] L274: Test all API calls work via new services
- [ ] L277: Create `login-modal-v2.js`
- [ ] L278: Create `employee-table-v2.js`
- [ ] L279: Create `leave-request-form-v2.js`
- [ ] L280: Create `dashboard-cards-v2.js`
- [ ] L281: Integrate components into app.js
- [ ] L282: Visual regression testing (screenshot compare)
- [ ] L285: Create `pages-v2/dashboard-manager.js`
- [ ] L286: Create `pages-v2/employees-manager.js`
- [ ] L287: Create `pages-v2/leave-manager.js`
- [ ] L288: Test page transitions
- [ ] L289: Test responsive design (375px, 768px, 1024px)
- [ ] L292: Remove deprecated code markers
- [ ] L293: Delete unused legacy files
- [ ] L294: Performance audit (bundle size reduction)
- [ ] L295: Final E2E tests (Playwright)
- [ ] L296: Deploy to production

### `static/js/RESUMEN-REFACTORING.md` (21)
- [ ] L239: Probar app-refactored.js en desarrollo
- [ ] L240: Ejecutar test-modules.html
- [ ] L241: Verificar todas las funcionalidades del dashboard
- [ ] L242: Probar en diferentes navegadores
- [ ] L245: Extraer módulo `requests` → `request-manager.js`
- [ ] L246: Extraer módulo `calendar` → `calendar-manager.js`
- [ ] L247: Extraer módulo `compliance` → `compliance-manager.js`
- [ ] L248: Extraer módulo `analytics` → `analytics-service.js`
- [ ] L249: Extraer módulo `reports` → `report-generator.js`
- [ ] L250: Extraer módulo `settings` → `settings-manager.js`
- [ ] L251: Extraer módulo `employeeTypes` → `employee-types-manager.js`
- [ ] L252: Extraer módulo `animations` → `animation-controller.js`
- [ ] L255: Agregar tests unitarios para cada módulo
- [ ] L256: Agregar tests de integración
- [ ] L257: Configurar linting (ESLint)
- [ ] L258: Configurar formateo (Prettier)
- [ ] L259: Agregar CI/CD
- [ ] L262: Tree-shaking con bundler (Webpack/Vite)
- [ ] L263: Code splitting para carga lazy
- [ ] L264: Minificación de producción
- [ ] L265: Source maps para debugging

### `.github/ISSUE_TEMPLATE/feature_request.md` (16)
- [ ] L23: Criterio 1
- [ ] L24: Criterio 2
- [ ] L25: Criterio 3
- [ ] L40: Alta (necesario para operacion basica)
- [ ] L41: Media (mejora significativa)
- [ ] L42: Baja (nice-to-have)
- [ ] L46: Pequena (< 1 dia)
- [ ] L47: Media (1-3 dias)
- [ ] L48: Grande (> 3 dias)
- [ ] L52: `main.py` - Backend/API
- [ ] L53: `database.py` - Base de datos
- [ ] L54: `excel_service.py` - Parser de Excel
- [ ] L55: `fiscal_year.py` - Logica de negocio
- [ ] L56: `static/js/app.js` - Frontend principal
- [ ] L57: `static/css/` - Estilos
- [ ] L58: Nuevo archivo necesario

### `docs/RUNBOOKS.md` (15)
- [ ] L331: All commits are reviewed and approved
- [ ] L332: All CI checks pass (green in Actions)
- [ ] L333: No security alerts (or all dismissed)
- [ ] L336: Unit tests pass (coverage > 80%)
- [ ] L337: Integration tests pass (all DB versions)
- [ ] L338: E2E tests pass
- [ ] L339: Manual smoke testing completed
- [ ] L342: Version number bumped (semantic versioning)
- [ ] L343: CHANGELOG.md updated
- [ ] L344: Release notes prepared
- [ ] L345: Database migrations tested
- [ ] L348: Terraform plan reviewed
- [ ] L349: Cost estimation acceptable
- [ ] L350: No security warnings
- [ ] L351: Backup plan confirmed

### `UI-UX-FIXES-SUMMARY.md` (14)
- [ ] L504: Team review of design system
- [ ] L505: User feedback collection
- [ ] L508: Start Phase 1: Service layer migration (see `FRONTEND-MIGRATION-GUIDE.md`)
- [ ] L509: Test color contrast on all browsers
- [ ] L510: Mobile testing (375px viewport)
- [ ] L511: Keyboard navigation audit
- [ ] L514: Complete Phase 2: Component migration
- [ ] L515: Deprecate legacy CSS files
- [ ] L516: Performance benchmarking
- [ ] L517: E2E test updates
- [ ] L520: Complete Phases 3-4: Page managers + cleanup
- [ ] L521: Remove app.js (if fully migrated)
- [ ] L522: Production deployment
- [ ] L523: Performance monitoring

### `docs/DATABASE_ADAPTER_README.md` (13)
- [ ] L394: Leer `docs/QUICKSTART_ADAPTER.md` (5 min)
- [ ] L395: Ver `examples/database_adapter_usage.py` (10 min)
- [ ] L396: Ejecutar tests: `pytest tests/test_database_adapter.py -v` (2 min)
- [ ] L397: Integrar en tu endpoint (5 min)
- [ ] L398: Probar con `USE_ORM=true` (instantáneo)
- [ ] L402: Leer `docs/DATABASE_ADAPTER.md` migration guide
- [ ] L403: Preparar canary deployment (10%→50%→100%)
- [ ] L404: Configurar monitoring para performance
- [ ] L405: Plan de rollback: `export USE_ORM=false`
- [ ] L409: Revisar `IMPLEMENTATION_SUMMARY.md`
- [ ] L410: Validar Phase 2 roadmap
- [ ] L411: Planear timeline Phase 3 (canary)
- [ ] L412: Setup Phase 4 cleanup tasks

### `scripts/disaster-recovery/RUNBOOK.md` (13)
- [ ] L219: Database connectivity: ✓
- [ ] L220: Application health: 200 OK
- [ ] L221: HTTP error rate: < 5%
- [ ] L222: Database replication: < 1 second lag
- [ ] L223: Tertiary replica syncing: Active
- [ ] L455: Document incident timeline
- [ ] L456: Identify root cause
- [ ] L457: Create permanent fix
- [ ] L458: Update runbook based on learnings
- [ ] L459: Schedule blameless post-mortem
- [ ] L460: Distribute lessons learned to team
- [ ] L492: [Task 1] - Owner: @name - Due: [Date]
- [ ] L493: [Task 2] - Owner: @name - Due: [Date]

### `tests/README.md` (12)
- [ ] L296: ¿Los datos del usuario se escapan correctamente?
- [ ] L297: ¿Se validan los inputs?
- [ ] L298: ¿Se manejan valores null/undefined?
- [ ] L301: ¿Funciona con datos válidos?
- [ ] L302: ¿Falla correctamente con datos inválidos?
- [ ] L303: ¿Se manejan los edge cases?
- [ ] L306: ¿Funciona con otros módulos?
- [ ] L307: ¿Persiste el estado correctamente?
- [ ] L308: ¿Actualiza la UI adecuadamente?
- [ ] L311: ¿Se previenen race conditions?
- [ ] L312: ¿Se limpian los recursos?
- [ ] L313: ¿Es eficiente con datasets grandes?

### `UI-UX-AUDIT-VISUAL-SUMMARY.md` (10)
- [ ] L297: Read this summary
- [ ] L298: Understand the 14 issues
- [ ] L299: Locate hardcoded colors in app.js
- [ ] L302: Replace `#06b6d4` with `var(--color-primary-500)`
- [ ] L303: Update chart color arrays
- [ ] L304: Rebuild and test
- [ ] L307: Verify all charts show blue (not cyan)
- [ ] L308: Test dark mode
- [ ] L309: Keyboard navigation (TAB)
- [ ] L310: Mobile responsiveness (375px)

### `COLORS-FIXED-SUMMARY.md` (10)
- [ ] L255: Reload app: http://localhost:8000
- [ ] L256: Dashboard: Verify all charts show BLUE (not cyan)
- [ ] L257: Vacation usage: Text should be BLUE
- [ ] L258: Pie charts: Check palette is blue-based
- [ ] L259: Line charts: Verify blue gradient
- [ ] L260: Compliance: All borders should be BLUE
- [ ] L261: Dark mode: Still looks good
- [ ] L262: Focus states: Blue outline (TAB key)
- [ ] L263: Mobile: 375px viewport (responsive)
- [ ] L264: Console: No errors (F12)

### `ThemeTheBestJpkken/INDEX.md` (9)
- [ ] L313: Leer QUICK_START.md
- [ ] L314: Copiar ejemplo básico
- [ ] L315: Probar dark/light toggle
- [ ] L318: Explorar EJEMPLOS.md
- [ ] L319: Implementar formulario
- [ ] L320: Crear primer gráfico
- [ ] L323: Leer README.md completo
- [ ] L324: Personalizar colores
- [ ] L325: Optimizar para producción

### `static/src/legacy-bridge/README.md` (9)
- [ ] L293: Crear componente moderno en `/static/src/components/`
- [ ] L294: Registrar con `bridge.registerModernComponent()`
- [ ] L295: Registrar feature con `bridge.registerFeature()`
- [ ] L296: Reemplazar calls legacy con `bridge.renderInLegacy()`
- [ ] L297: Sincronizar estado si es necesario
- [ ] L298: Testear en ambos modos (dark/light)
- [ ] L299: Verificar accesibilidad (WCAG AA)
- [ ] L300: Medir performance
- [ ] L301: Documentar cambios

### `QUICK-FIX-14-COLORS.md` (8)
- [ ] L427: Opened `static/js/app.js`
- [ ] L428: Used Find & Replace (`Ctrl+H`)
- [ ] L429: Made 4 replacements (see above)
- [ ] L430: Saved file (`Ctrl+S`)
- [ ] L431: Reloaded server
- [ ] L432: Verified no cyan (#06b6d4) found in file
- [ ] L433: Tested in browser (charts, colors, dark mode)
- [ ] L434: Dashboard shows blue instead of cyan ✅

### `ThemeTheBestJpkken/QUICK_START.md` (8)
- [ ] L397: Copiar carpeta `ThemeTheBestJpkken` al proyecto
- [ ] L398: Enlazar fuentes de Google
- [ ] L399: Enlazar los 3 archivos CSS (main, arari-glow, premium-enhancements)
- [ ] L400: Agregar `data-theme="dark"` al `<html>`
- [ ] L401: Usar estructura `app-container` > `sidebar` + `main-content`
- [ ] L402: Implementar grid con `bento-grid` y `col-span-X`
- [ ] L403: Agregar theme toggle (opcional)
- [ ] L404: Cargar `chart-colors.js` si usas gráficos

### `.shared/ui-ux-pro-max/design-system.md` (7)
- [ ] L44: No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] L45: cursor-pointer on all clickable elements
- [ ] L46: Hover states with smooth transitions (150-300ms)
- [ ] L47: Light mode: text contrast 4.5:1 minimum
- [ ] L48: Focus states visible for keyboard nav
- [ ] L49: prefers-reduced-motion respected
- [ ] L50: Responsive: 375px, 768px, 1024px, 1440px

### `docs/DATABASE_ADAPTER.md` (6)
- [ ] L378: Complete ORM implementations for all CRUD operations
- [ ] L379: Add ORM-specific optimizations (lazy loading, eager loading)
- [ ] L380: Performance benchmarking
- [ ] L383: Remove raw SQL implementation
- [ ] L384: Make ORM the default
- [ ] L385: Advanced features (relationship caching, query optimization)

### `docs/QUICKSTART_ADAPTER.md` (6)
- [ ] L330: Leer este documento (5 min)
- [ ] L331: Ver `docs/DATABASE_ADAPTER.md` (10 min)
- [ ] L332: Ejecutar `examples/database_adapter_usage.py` (5 min)
- [ ] L333: Ejecutar tests: `pytest tests/test_database_adapter.py -v` (2 min)
- [ ] L334: Usar en un endpoint: `get_employees(year=2025)` (5 min)
- [ ] L335: Cambiar a ORM y verificar: `USE_ORM=true` (5 min)

### `.github/ISSUE_TEMPLATE/bug_report.md` (6)
- [ ] L41: `main.py`
- [ ] L42: `excel_service.py`
- [ ] L43: `database.py`
- [ ] L44: `fiscal_year.py`
- [ ] L45: `static/js/app.js`
- [ ] L46: Otro: ___

### `docs/IMPLEMENTATION_SUMMARY.md` (5)
- [ ] L162: Completar funciones de escritura en `database_orm.py`
- [ ] L163: Agregar optimizaciones ORM
- [ ] L166: Canary deployment (10% → 50% → 100%)
- [ ] L167: Monitoreo de performance
- [ ] L170: Eliminar database.py cuando ORM sea stable

### `YukyuData-AppFusion2.13/frontend/SUBAGENTS.md` (5)
- [ ] L234: No hay eval() o innerHTML sin sanitizar
- [ ] L235: Inputs sanitizados (CSV, Excel)
- [ ] L236: No hay secrets en código
- [ ] L237: Dependencias actualizadas
- [ ] L238: LocalStorage no expone datos sensibles

### `UI-UX-AUDIT-REPORT-COMPLETE.md` (3)
- [ ] L387: **App.js colors migrated to CSS variables** (Pending)
- [ ] L388: **All charts using design tokens** (Pending)
- [ ] L389: **Comprehensive testing in all browsers** (Pending)

### `docs/PRODUCTION.md` (3)
- [ ] L350: Configure CORS for production domains (deployment-specific)
- [ ] L351: Enable HTTPS via reverse proxy (deployment-specific)
- [ ] L352: Disable DEBUG mode in production (done via .env)
