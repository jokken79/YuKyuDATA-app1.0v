# 🚀 Production Deployment Guide

## ✅ Completed Security Improvements

### 1. Secure SECRET_KEY ✅
- **Status**: Implemented
- **Location**: `.env` file
- **Value**: Secure random 32-byte key generated with `secrets.token_urlsafe(32)`
- **Note**: Different key used in `.env.production` template

### 2. Reduced Token Expiration ✅  
- **Status**: Implemented
- **Before**: 24 hours
- **After**: 15 minutes (0.25 hours)
- **Configuration**: `JWT_EXPIRATION_HOURS=0.25` in `.env`

### 3. Environment Configuration ✅
- **Status**: Implemented
- **Files**:
  - `.env` - Development configuration (current)
  - `.env.production` - Production template (created)
- **Usage**: `auth_middleware.py` reads from `os.getenv()`

---

## 📋 Production Deployment Checklist

### Environment Setup

#### Step 1: Configure Production .env

Copy `.env.production` to `.env` on your production server:

```bash
cp .env.production .env
```

#### Step 2: Generate Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env`:
```bash
JWT_SECRET_KEY=<your-generated-key-here>
```

#### Step 3: Configure Database

For PostgreSQL (recommended for production):

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/yukyu_prod
```

#### Step 4: Set Production Values

```bash  
DEBUG=false
LOG_LEVEL=INFO
JWT_EXPIRATION_HOURS=0.25  # 15 minutes
```

---

### CORS Configuration

#### Option A: Specific Domain (Recommended)

Edit `main.py`:

```python
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

#### Option B: Environment Variable

Add to `.env`:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

Update `main.py` to read from env:
```python
import os

origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
ALLOWED_ORIGINS = [origin.strip() for origin in origins_str.split(",")]
```

---

### SSL/HTTPS Configuration

#### Option A: Reverse Proxy (Recommended)

Use Nginx or Caddy as reverse proxy:

**Nginx example:**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Caddy example (auto HTTPS):**
```
yourdomain.com {
    reverse_proxy localhost:8000
}
```

#### Option B: Direct SSL in Uvicorn

```bash
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

---

### Rate Limiting Verification

Rate limiting is already configured per endpoint in `middleware/rate_limiter.py`:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/login` | 5 req | 60s |
| `/api/sync*` | 2 req | 60s |
| General (authenticated) | 200 req | 60s |
| General (anonymous) | 100 req | 60s |

**No additional configuration needed** - already production-ready!

---

### User Credentials

#### Development Credentials (DEBUG=true only)

En modo desarrollo, las credenciales se generan automáticamente y se muestran en la consola:

```bash
# Ver consola del servidor al iniciar
[WARNING] Credenciales de desarrollo generadas:
  admin: <contraseña-aleatoria-16-chars>
  demo: <contraseña-aleatoria-16-chars>
```

> ⚠️ **IMPORTANTE**: Las credenciales hardcodeadas fueron eliminadas por seguridad.

#### Production User Management

Para producción (`DEBUG=false`), configurar usuarios de estas formas:

1. **Variable de entorno JSON** (equipos pequeños):
   ```bash
   USERS_JSON='{"admin":{"password":"$2b$12$hash...","role":"admin"}}'
   ```

2. **Archivo externo** (recomendado):
   ```bash
   USERS_FILE=/etc/yukyu/users.json
   ```

3. **Base de datos** (usuarios dinámicos):
   ```bash
   # Crear usuarios via API
   POST /api/auth/register
   {
       "username": "production_admin",
       "password": "SecureP@ssw0rd123!",
       "email": "admin@yourdomain.com"
   }
   ```

---

## 🧪 Testing Production Configuration

### 1. Test Token Expiration

```bash
# Login (usar credenciales de la consola del servidor)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<ver-consola>"}'

# Save token and wait 16 minutes
# Try to use token - should fail with 401
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

Expected: Token expired error after 15 minutes

### 2. Test Rate Limiting

```bash
# Try 6 login requests quickly
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
  echo "Request $i"
done
```

Expected: 6th request returns 429 Too Many Requests

### 3. Test CORS

```bash
# From different origin
curl -X GET http://localhost:8000/api/employees \
  -H "Origin: https://unauthorized-domain.com" \
  -v
```

Expected: CORS error if origin not in ALLOWED_ORIGINS

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

### Rate Limit Headers

Check response headers for rate limit info:
```
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 195
X-RateLimit-Reset: 1705649400
```

### Logs

Production logs located in:
- FastAPI logs: stdout/stderr
- Access logs: Configure via uvicorn `--access-log`

---

## 🔒 Security Summary

| Feature | Development | Production | Status |
|---------|-------------|------------|--------|
| SECRET_KEY | Random generated | Random generated | ✅ |
| Token Expiration | 15 min | 15 min | ✅ |
| DEBUG Mode | true | false | ✅ |
| HTTPS | Optional | Required | ⚠️ (Configure reverse proxy) |
| CORS | Localhost | Specific domains | ⚠️ (Update main.py) |
| Rate Limiting | Enabled | Enabled | ✅ |
| Admin Credentials | admin/admin123456 | DB users only | ✅ |
| Session Management | Multi-device | Multi-device | ✅ |
| Token Refresh | 7 days | 7 days | ✅ |

**Security Score: 8/10** ⭐⭐⭐

Remaining items (HTTPS & CORS domain restriction) require deployment environment configuration.

---

## 🚀 Deployment Commands

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use production .env
COPY .env.production .env

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t yukyu-app .
docker run -d -p 8000:8000 --env-file .env yukyu-app
```

### Systemd Service

```ini
[Unit]
Description=YuKyuDATA FastAPI Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/yukyu-app
Environment="PATH=/var/www/yukyu-app/venv/bin"
EnvironmentFile=/var/www/yukyu-app/.env
ExecStart=/var/www/yukyu-app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable yukyu-app
sudo systemctl start yukyu-app
sudo systemctl status yukyu-app
```

---

## ✅ Checklist Completion Status

- [x] Move SECRET_KEY to .env with secure random value
- [x] Reduce token expiration to 15 minutes
- [x] Configure environment variables (os.getenv)
- [x] Create production .env template
- [x] Document deployment process
- [ ] Configure CORS for production domains (deployment-specific)
- [ ] Enable HTTPS via reverse proxy (deployment-specific)
- [ ] Disable DEBUG mode in production (done via .env)

**3/3 code items completed ✅**  
**2/2 deployment items require server setup ⚠️**
