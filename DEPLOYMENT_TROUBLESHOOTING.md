# Deployment Troubleshooting Guide - YuKyuDATA-app
**Versión:** 1.0
**Último actualizado:** 2026-01-17

---

## Common Issues and Solutions

### Issue 1: Deployment Hangs on "Waiting for Health Check"

**Symptoms:**
- Workflow está "In Progress" por más de 5 minutos en "Deploy Blue-Green"
- Logs muestran muchos dots (...........) sin progreso
- Container está corriendo pero no llega a "healthy"

**Root Causes:**
1. Application no puede conectar a database
2. Timeout de health check muy corto
3. Port no está disponible

**Diagnosis:**
```bash
# SSH al servidor
ssh DEPLOY_USER@DEPLOY_HOST

# Ver logs del container
docker logs yukyu-green  # o yukyu-blue

# Ver health status
docker inspect yukyu-green --format='{{.State.Health.Status}}'

# Ver puerto
docker port yukyu-green
```

**Solutions:**

**Si: Database connection error**
```bash
# Verificar conexión a BD
docker exec yukyu-green curl http://localhost:8000/api/health/db

# Si falla, revisar environment variables
docker inspect yukyu-green --format='{{.Config.Env}}'

# Verificar DATABASE_URL es correcto
# DATABASE_URL debe tener formato: postgresql://user:pass@host:port/dbname
```

**Si: Port not available**
```bash
# Verificar puerto 9000 y 9001
netstat -tlnp | grep 9000
netstat -tlnp | grep 9001

# Matar proceso en puerto si es necesario
sudo lsof -i :9000
sudo kill -9 <PID>
```

**Si: Health check timeout**
```bash
# Aumentar timeout en deploy-blue-green.sh
# Editar línea: HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"
# Cambiar 60 a 120 (segundos)

# O ejecutar manualmente con timeout mayor
HEALTH_CHECK_TIMEOUT=120 bash scripts/deploy-blue-green.sh latest
```

---

### Issue 2: Smoke Tests Fail After Deployment

**Symptoms:**
- Workflow detiene en "Smoke Tests"
- Health check pasó pero smoke tests fallan
- Logs muestran HTTP error codes (500, 502, 503)

**Root Causes:**
1. Application lanzó pero tiene errores internos
2. Endpoint no existe o cambió
3. Data no se migró correctamente

**Diagnosis:**
```bash
# Probar endpoints manualmente
curl -v http://localhost:9000/api/health
curl -v http://localhost:9000/api/employees
curl -v http://localhost:9000/docs

# Ver detailed error
curl -s http://localhost:9000/api/employees | jq '.'

# Ver logs de aplicación
docker logs -f yukyu-green
```

**Solutions:**

**Si: 500 Internal Server Error**
```bash
# Revisar logs para exception
docker logs yukyu-green 2>&1 | grep -A 5 "ERROR\|Traceback\|Exception"

# Posibles causes:
# 1. Import error en main.py
# 2. Database schema missing
# 3. Environment variable missing
```

**Si: 502 Bad Gateway**
```bash
# Nginx no puede conectar al backend
# Verificar nginx config
docker exec yukyu-nginx cat /etc/nginx/conf.d/upstream.conf

# Debería ser:
# upstream backend {
#     server 127.0.0.1:9000;  (o 9001)
# }

# Reiniciar nginx
docker exec yukyu-nginx nginx -s reload
```

**Si: 503 Service Unavailable**
```bash
# Application está up pero no respondiendo
# Ver si está out of memory o CPU
docker stats yukyu-green

# Ver conexiones
netstat -tan | grep 8000

# Reiniciar container
docker restart yukyu-green
```

---

### Issue 3: Rollback Fails

**Symptoms:**
- Workflow intenta rollback automático pero falla
- Old container no está corriendo
- Traffic no vuelve a versión anterior

**Root Causes:**
1. Old container fue removido prematuramente
2. Nginx config está corrupta
3. No hay versión previa para rollback

**Diagnosis:**
```bash
# Ver containers disponibles
docker ps -a | grep yukyu

# Ver color state
cat /tmp/yukyu-color.txt

# Ver nginx config
docker exec yukyu-nginx cat /etc/nginx/conf.d/upstream.conf
```

**Solutions:**

**Si: Old container not running**
```bash
# Check si existe (puede estar stopped)
docker ps -a | grep yukyu

# Si existe pero está stopped, reiniciar
docker start yukyu-blue   # o yukyu-green según corresponda

# Luego ejecutar rollback
bash scripts/rollback.sh
```

**Si: Nginx no actualiza**
```bash
# Actualizar upstream manualmente
docker exec yukyu-nginx bash -c "cat > /etc/nginx/conf.d/upstream.conf <<EOF
upstream backend {
    server 127.0.0.1:9000;
}
EOF
nginx -s reload"

# Verificar cambio
docker exec yukyu-nginx curl http://localhost/api/health
```

**Si: No hay versión previa**
```bash
# Si ambos containers fallaron, revisar historial de images
docker images | grep yukyu

# Puedes relanzar la versión anterior manualmente:
docker run -d --name yukyu-blue \
  -p 127.0.0.1:9000:8000 \
  ghcr.io/your-org/yukyu-app:previous-version
```

---

### Issue 4: Database Connection Fails

**Symptoms:**
- Health check fallan en step "Check database connectivity"
- Logs muestran "Cannot connect to database"
- /api/health/db retorna error

**Root Causes:**
1. PostgreSQL server is down
2. Credenciales incorrectas
3. Network connectivity issue

**Diagnosis:**
```bash
# Ver DATABASE_URL en container
docker inspect yukyu-green --format='{{.Config.Env}}' | grep DATABASE

# Conectar directamente a BD
docker exec yukyu-green psql -U <user> -d <dbname> -c "SELECT 1;"

# O para SQLite:
docker exec yukyu-green sqlite3 /app/data/yukyu.db ".schema employees"
```

**Solutions:**

**Si: PostgreSQL is down**
```bash
# Verificar si está corriendo
docker ps | grep postgres

# Si no está, iniciar:
docker-compose -f docker-compose.yml up -d postgres

# Si está pero no responde:
docker logs postgres
docker restart postgres
```

**Si: Credenciales incorrectas**
```bash
# Verificar en GitHub Secrets
# DEPLOY_HOST, DEPLOY_USER, DATABASE_URL, etc.

# O actualizar environment variables en deployment:
docker exec yukyu-green env | grep DATABASE
```

**Si: Network issue**
```bash
# Verificar conectividad desde container
docker exec yukyu-green nc -zv <db-host> <db-port>

# Si falla, revisar docker network
docker network ls
docker network inspect bridge

# Posible solución: usar docker network
docker run -d --name yukyu-green \
  --network app-network \
  -p 127.0.0.1:9001:8000 \
  ghcr.io/your-org/yukyu-app:latest
```

---

### Issue 5: Out of Memory or CPU Issues

**Symptoms:**
- Container crashes durante deployment
- Logs muestran "OOMKilled" o "exit code 137"
- CPU usage muy alta (> 95%)

**Root Causes:**
1. Memory limit muy bajo
2. Memory leak en aplicación
3. N+1 query en database

**Diagnosis:**
```bash
# Ver resource usage
docker stats yukyu-green

# Ver ulimits
docker inspect yukyu-green --format='{{.HostConfig.Memory}}'
docker inspect yukyu-green --format='{{.HostConfig.MemorySwap}}'

# Ver procesos dentro del container
docker top yukyu-green
```

**Solutions:**

**Aumentar memory limit:**
```bash
# En deploy-blue-green.sh, agregar:
docker run -d --name "$NEW_CONTAINER" \
  -m 2g \                          # Increase from default
  --memory-swap 2g \
  -p "127.0.0.1:${NEW_PORT}:8000" \
  ...
```

**Si: Memory leak**
```bash
# Revisar logs para memory usage trending
docker stats yukyu-green --no-stream

# Identificar cual query es lenta
# Agregar logging en services/

# Considerar agregar Redis para caching
# Ver services/caching.py para implementación
```

**Si: High CPU**
```bash
# Ver cual proceso está usando CPU
docker top yukyu-green

# Revisar logs para busy loops
docker logs yukyu-green | grep -i "while\|loop"

# Posible issue: uvicorn workers
# En docker run, agregar: --workers 4
# Ajustar según número de CPUs disponibles
```

---

### Issue 6: Traffic Doesn't Switch to New Version

**Symptoms:**
- Deployment completa exitosamente
- Pero requests siguen yendo a versión vieja
- Nginx no está actualizando upstream

**Root Causes:**
1. Nginx está en container separado que no actualiza
2. Browser caching antigua versión
3. Load balancer no está configurado

**Diagnosis:**
```bash
# Verificar nginx upstream config
docker exec yukyu-nginx cat /etc/nginx/conf.d/upstream.conf

# Ver cual container está respondiendo
curl -s http://localhost:8000/ | grep -i version

# Ver headers para identificar source
curl -v http://localhost:8000/ 2>&1 | grep "^< Server"
```

**Solutions:**

**Si: Nginx config no actualiza**
```bash
# Asegurarse que script actualiza correctamente
# Revisar deploy-blue-green.sh línea ~150

# Ejecutar manualmente:
docker exec yukyu-nginx bash -c "cat > /etc/nginx/conf.d/upstream.conf <<EOF
upstream backend {
    server 127.0.0.1:9000;
}
EOF
nginx -s reload"

# Verificar cambio
docker exec yukyu-nginx curl localhost/api/health
```

**Si: Browser cache**
```bash
# Hard refresh en browser: Ctrl+Shift+Delete (Cmd+Shift+Delete en Mac)
# O usar incognito mode

# Para verificar versión en backend:
curl -s http://localhost:8000/api/health | jq '.version'
```

**Si: Load balancer**
```bash
# Si hay load balancer adelante de nginx, revisar:
# - Sticky sessions habilitadas?
# - Connection pooling?
# - Cache settings?

# Posible solución: deshabilitar cache en load balancer
# durante deployment por 5 minutos
```

---

### Issue 7: Backup Verification Fails

**Symptoms:**
- Workflow `backup-verify.yml` en estado failed
- Backup file not found o corrupted
- Restore test falla

**Root Causes:**
1. Backup script no ejecutó
2. Disk space insuficiente
3. gzip corruption

**Diagnosis:**
```bash
# Verificar backups en servidor
ls -lah /opt/yukyu-app/backups/

# Verificar integridad
gzip -t /opt/yukyu-app/backups/yukyu_*.db.gz

# Ver tamaño de disco
df -h /opt/yukyu-app/

# Ver logs de backup
ls -t /opt/yukyu-app/logs/deployment/ | head -5
```

**Solutions:**

**Si: Backup no existe**
```bash
# Ejecutar backup manualmente
bash scripts/backup-database.sh ./backups 30

# Verificar resultado
ls -lah backups/yukyu_*.db.gz
```

**Si: Disk space issue**
```bash
# Limpiar backups viejos
find ./backups -name "yukyu_*.db.gz" -mtime +30 -delete

# O aumentar retention en script:
bash scripts/backup-database.sh ./backups 60
```

**Si: gzip corruption**
```bash
# Verificar archivo está bien formado
file ./backups/yukyu_*.db.gz

# Intentar reparar
gzip -d --force ./backups/yukyu_CORRUPTED.db.gz

# Si falla, backup está perdido
# Usar backup anterior:
ls -t ./backups/yukyu_*.db.gz
```

---

## Emergency Procedures

### Full System Failure

**Pasos para recuperarse:**

1. **Assess Damage (5 min)**
   ```bash
   # SSH al servidor
   ssh DEPLOY_USER@DEPLOY_HOST

   # Ver status
   docker ps -a
   docker logs yukyu-green
   docker logs yukyu-blue
   ```

2. **Stop All (2 min)**
   ```bash
   docker-compose down  # Si existe docker-compose.yml
   # O manualmente:
   docker stop yukyu-blue yukyu-green yukyu-nginx
   ```

3. **Restore from Backup (10-15 min)**
   ```bash
   # Encontrar backup más reciente
   ls -t backups/yukyu_*.db.gz | head -1

   # Descomprimir
   gunzip -c backups/yukyu_LATEST.db.gz > yukyu.db

   # Verificar integridad
   sqlite3 yukyu.db ".schema employees" | head
   ```

4. **Restart Services (5 min)**
   ```bash
   # Iniciar containers
   docker-compose -f docker-compose.yml up -d

   # Verificar health
   curl http://localhost:8000/api/health
   ```

5. **Verify (5 min)**
   ```bash
   # Test todos endpoints críticos
   bash scripts/smoke-tests.sh localhost:8000 true
   ```

---

## Debug Mode

Para troubleshoot issues más complejos:

```bash
# Ver todos logs en tiempo real
docker-compose logs -f --tail=100

# Entrar en container
docker exec -it yukyu-green /bin/bash

# En el container, puedes:
python -c "import database; database.init_db()"
sqlite3 /app/data/yukyu.db ".tables"
ps aux  # Ver procesos
env     # Ver environment variables

# Ejecutar curl desde container
curl http://localhost:8000/api/health

# Ver archivos
ls -la /app/
cat /app/main.py | head -20
```

---

## Escalation Path

Si no puedes resolver el issue:

1. **5 min:** Intenta soluciones en esta guía
2. **10 min:** Revisa logs detalladamente
3. **15 min:** Ejecuta rollback automático
4. **20 min:** Escalate a DevOps Lead
5. **25 min:** Inicia post-incident review

**Contactos (reemplazar con valores reales):**
- DevOps Lead: devops-lead@example.com
- On-Call Engineer: +1-555-DEVOPS
- Slack Channel: #devops-incidents
- PagerDuty: https://YOUR-ORG.pagerduty.com/

---

**Keep this guide accessible during deployments!**
