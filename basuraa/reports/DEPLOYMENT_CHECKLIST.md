# Deployment Checklist - YuKyuDATA-app
**Versión:** 1.0
**Último actualizado:** 2026-01-17
**Responsable:** DevOps Engineer

---

## PRE-DEPLOYMENT CHECKLIST (24 horas antes)

### Code Readiness
- [ ] Todos los cambios están en la rama `main`
- [ ] No hay conflictos de merge
- [ ] Última versión compilada: `git log -1 --oneline`

### Testing
- [ ] Todos los tests pasan en local: `pytest tests/ -v`
- [ ] No hay failing E2E tests: `npx playwright test`
- [ ] Frontend assets se compilan sin errores: `npm run build`
- [ ] Coverage está por encima de 80%: `pytest tests/ --cov=.`

### Security
- [ ] No hay secrets en el código: `bash scripts/check-secrets.sh`
- [ ] JWT secrets son únicos por ambiente
- [ ] Database credentials están en GitHub Secrets
- [ ] SSH key para deployment está configurada

### Documentation
- [ ] CHANGELOG.md está actualizado
- [ ] Release notes preparadas (si aplica)
- [ ] Runbook de incident está disponible
- [ ] Equipo de soporte notificado

### Approvals (Production Only)
- [ ] Aprobación de Product Manager
- [ ] Aprobación de Security Team
- [ ] Notificación a Operations Team
- [ ] Change log creado en sistema de cambios

---

## DEPLOYMENT EXECUTION CHECKLIST

### Phase 1: Pre-Deployment (0-15 minutes)

**⏱️ Time: T-15min**

- [ ] Verificar dashboard de monitoring está accesible
- [ ] Crear snapshot de métricas actuales (CPU, Memory, Latency)
- [ ] Verificar backups recientes existen
- [ ] SSH access a servidor de deployment funciona

**Comando:**
```bash
# Verificar acceso a servidor
ssh -i ~/.ssh/deploy_key DEPLOY_USER@DEPLOY_HOST "echo 'SSH OK' && docker ps"

# Verificar backups
ssh -i ~/.ssh/deploy_key DEPLOY_USER@DEPLOY_HOST "ls -lah /opt/yukyu-app/backups/"
```

### Phase 2: Trigger Deployment (T-0)

**⏱️ Time: T+0min**

1. [ ] Ir a GitHub Actions: https://github.com/YOUR_ORG/YuKyuDATA-app1.0v/actions
2. [ ] Seleccionar workflow: `Blue-Green Deployment`
3. [ ] Hacer clic en "Run workflow"
4. [ ] Configurar:
   - Environment: `staging` o `production`
   - Version tag: `v1.2.3` o `latest`
5. [ ] Hacer clic en "Run workflow"
6. [ ] **NO cierres la página** - monitorea el progreso

**URL Workflow:**
```
https://github.com/jokken79/YuKyuDATA-app1.0v/actions/workflows/blue-green-deploy.yml
```

### Phase 3: Monitoring Deployment (T+0 to T+15)

**⏱️ Time: T+0min to T+15min**

- [ ] Esperar que "Pre-flight Checks" terminen (1-2 min)
- [ ] Esperar que "Run Tests" pasen (5-7 min)
- [ ] Esperar que "Build Docker Image" termine (3-5 min)
- [ ] Esperar que "Deploy Blue-Green" inicie (1 min)
- [ ] **MONITOR EN PARALELO:**
  - [ ] Ver logs del servidor: `ssh ... docker logs -f yukyu-{blue|green}`
  - [ ] Monitorear CPU/Memory en dashboard
  - [ ] Revisar error logs: `tail -f /var/log/yukyu-error.log`

**Comandos útiles durante deploy:**
```bash
# Ver logs del deployment
ssh DEPLOY_USER@DEPLOY_HOST "cd /opt/yukyu-app && tail -f logs/deployment/*.log"

# Ver status de containers
ssh DEPLOY_USER@DEPLOY_HOST "docker ps | grep yukyu"

# Ver cual es el color actual
ssh DEPLOY_USER@DEPLOY_HOST "cat /tmp/yukyu-color.txt"

# Ver logs de nginx
ssh DEPLOY_USER@DEPLOY_HOST "docker logs -f yukyu-nginx 2>&1 | tail -20"
```

### Phase 4: Validation (T+15 to T+20)

**⏱️ Time: T+15min to T+20min**

- [ ] Verificar workflow "Deploy Blue-Green" está en estado ✅ success
- [ ] Verificar workflow "Smoke Tests" está en estado ✅ success
- [ ] **NO ESPERES el workflow de backup** (corre en paralelo)
- [ ] Health check manual:
  ```bash
  curl -s https://your-app.com/api/health | jq '.'
  ```
  Debe retornar: `{"status": "healthy", "timestamp": "...", ...}`

- [ ] Login test:
  ```bash
  curl -X POST https://your-app.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}'
  ```
  Debe retornar: `{"access_token": "...", "refresh_token": "...", ...}`

- [ ] Data test:
  ```bash
  curl -s 'https://your-app.com/api/employees?year=2025' | jq '.meta.total'
  ```
  Debe retornar un número > 0 (si hay datos)

### Phase 5: Post-Deployment (T+20 to T+60)

**⏱️ Time: T+20min to T+60min**

#### First 5 minutes (T+20 to T+25)
- [ ] Dashboard de monitoring muestra nuevas métricas
- [ ] No hay picos anormales en CPU/Memory
- [ ] No hay increase en error rate
- [ ] Latency promedio < 1 segundo
- [ ] No hay errores en application logs

#### First 30 minutes (T+25 to T+55)
- [ ] Mantener monitoreo de las métricas clave
- [ ] Revisar logs de application cada 5 minutos
- [ ] Verificar sin cambios en error patterns
- [ ] Test endpoints críticos manualmente:
  - [ ] GET /api/employees
  - [ ] GET /api/leave-requests
  - [ ] POST /api/auth/login
  - [ ] POST /api/auth/logout
- [ ] Revisar con equipo de soporte:
  - [ ] Algún reporte de issues?
  - [ ] Algún comportamiento anormal?

#### After 60 minutes (T+55 onwards)
- [ ] ✅ Deployment considerado EXITOSO
- [ ] Crear incident para rollback window será auto-cerrado en 10 minutos
- [ ] Actualizar status page / release notes
- [ ] Notificar a stakeholders

**Comandos para monitoreo continuo:**
```bash
# Monitor en tiempo real (run every minute)
watch -n 60 'ssh DEPLOY_USER@DEPLOY_HOST \
  "curl -s http://localhost:8000/api/health | jq . && \
   docker stats --no-stream yukyu-blue yukyu-green 2>/dev/null || echo no-containers"'

# Ver health con timestamp
while true; do
  echo "$(date '+%Y-%m-%d %H:%M:%S')"
  curl -s http://localhost:8000/api/health | jq '.status'
  sleep 30
done
```

---

## EMERGENCY ROLLBACK CHECKLIST

**Usar SOLO si:**
- [ ] Error rate sube > 5%
- [ ] Latency sube > 5 segundos
- [ ] Database se desconecta
- [ ] Critical endpoint falla completamente

### Immediate Actions (within 30 seconds)

1. [ ] **STOP:**  No hagas más cambios
2. [ ] **ESCALATE:** Notifica a Product Manager y CTO
3. [ ] **ALERT:** Avisa a equipo de soporte
4. [ ] **ASSESS:** Determina si es actual deployment o infraestructura

### Rollback Execution (within 2 minutes)

**Automático (si falla workflow):**
- El workflow `blue-green-deploy.yml` ejecutará automáticamente rollback
- Espera al job "Automatic Rollback" completarse
- Verifica en GitHub Actions UI

**Manual (si automático no funciona):**
```bash
ssh DEPLOY_USER@DEPLOY_HOST "cd /opt/yukyu-app && bash scripts/rollback.sh"
```

**Pasos de rollback manual:**
```bash
# 1. Conectar al servidor
ssh -i ~/.ssh/deploy_key DEPLOY_USER@DEPLOY_HOST

# 2. Verificar color actual
cat /tmp/yukyu-color.txt  # Ej: "blue"

# 3. Ver containers
docker ps | grep yukyu

# 4. Ejecutar rollback
cd /opt/yukyu-app && bash scripts/rollback.sh

# 5. Verificar rollback
curl -s http://localhost:9000/api/health | jq '.'

# 6. Confirmar con app team
curl -s https://your-app.com/api/health | jq '.'
```

### Post-Rollback (within 5 minutes)

- [ ] Health checks retornan 200 OK
- [ ] Login funciona correctamente
- [ ] No hay nuevos errores en logs
- [ ] Métricas de CPU/Memory normales
- [ ] Team confirmó rollback exitoso

### Root Cause Analysis (within 24 hours)

- [ ] Crear incident/bug para el problema
- [ ] Revisar logs de deployment
- [ ] Identificar causa exacta
- [ ] Crear test case para prevenir
- [ ] Schedule fix review
- [ ] Documentar lesson learned

---

## MONITORING CHECKLIST (Ongoing)

### Every 5 Minutes
- [ ] Health endpoint retorna status "healthy"
- [ ] No nuevos errores críticos en logs
- [ ] CPU no sobrepasa 80%
- [ ] Memory no sobrepasa 85%

### Every Hour
- [ ] Revisar dashboard de metrics
- [ ] Verificar trending de key indicators
- [ ] Confirmar backups corren sin errores
- [ ] Check database replication lag (< 1s)

### Daily
- [ ] Backup verification workflow pasó ✅
- [ ] Error rate trending (should be stable)
- [ ] User reports or complaints
- [ ] Security alerts or anomalies

---

## ROLLBACK WINDOW

**Critical Info:**
- Duration: **10 minutes** after deployment completes
- After 10 min: Old container is automatically removed
- Manual rollback possible during window
- After window: Contact DevOps for manual rollback

**Color State:**
```bash
# Check current color (donde está el traffic)
cat /tmp/yukyu-color.txt  # Retorna: "blue" or "green"

# Check container status
docker ps | grep yukyu

# Ports:
# - Port 9000 = Blue   (ej: 127.0.0.1:9000)
# - Port 9001 = Green  (ej: 127.0.0.1:9001)
```

---

## COMMUNICATION TEMPLATE

### Deployment Started
```
🚀 DEPLOYMENT STARTED

Environment: [staging/production]
Version: [v1.2.3]
Triggered by: [GitHub actor]
Estimated duration: 15-20 minutes

⏳ Monitoring in progress...
```

### Deployment Successful
```
✅ DEPLOYMENT SUCCESSFUL

Environment: [staging/production]
Version: [v1.2.3]
Duration: [15 min 23 sec]
Status: All checks passed ✓

Rollback available for 10 minutes if needed.
```

### Deployment Failed
```
❌ DEPLOYMENT FAILED

Environment: [staging/production]
Version: [v1.2.3]
Error: [brief error description]

🔄 AUTOMATIC ROLLBACK IN PROGRESS
Previous version will be restored within 2 minutes.
```

---

## DEPLOYMENT SIGN-OFF

After deployment completes successfully, fill out:

- **Date/Time:** ___________________
- **Deployed by:** ___________________
- **Environment:** ___________________
- **Version:** ___________________
- **Duration:** ___________________
- **Issues encountered:** ___________________
- **Resolution:** ___________________
- **Approval:** ___________________

---

## Quick Reference

### Workflow URLs
```
CI Pipeline:           https://github.com/jokken79/YuKyuDATA-app1.0v/actions/workflows/ci.yml
Blue-Green Deploy:     https://github.com/jokken79/YuKyuDATA-app1.0v/actions/workflows/blue-green-deploy.yml
Backup Verification:   https://github.com/jokken79/YuKyuDATA-app1.0v/actions/workflows/backup-verify.yml
```

### Important Secrets (GitHub Settings)
```
Required for deployment:
- DEPLOY_HOST         = Server IP/hostname
- DEPLOY_USER         = SSH username
- DEPLOY_SSH_KEY      = SSH private key
- SLACK_WEBHOOK_URL   = Slack channel webhook (optional)
```

### Server Access
```bash
# SSH into server
ssh -i ~/.ssh/deploy_key DEPLOY_USER@DEPLOY_HOST

# Docker commands
docker ps                    # List containers
docker logs -f CONTAINER     # View logs
docker exec -it CONTAINER sh # Shell access
docker stats                 # Resource usage
```

### Application URLs
```
Staging:     https://staging.yukyu.example.com
Production:  https://yukyu.example.com
Health:      /api/health
Docs:        /docs
ReDoc:       /redoc
Login:       POST /api/auth/login
```

---

**Keep this checklist near deployment workstation!**
