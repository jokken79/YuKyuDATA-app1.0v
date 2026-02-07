# 📚 Manual de Deploy en Vercel - YuKyuDATA App

**Versión:** 1.0
**Fecha:** Febrero 2026
**Último actualizado:** Por Claude Code

---

## 📋 Requisitos Previos

- Cuenta en [vercel.com](https://vercel.com)
- Node.js >= 18.0.0
- Python 3.12+
- Git configurado
- Token de Vercel (generado en Account Settings)

---

## 🚀 Método 1: Deploy Automático (GitHub Integration - Recomendado)

### Ventajas
✅ Deploy automático en cada push a `main`
✅ No necesitas token en tu máquina
✅ Preview automático en PRs
✅ Más seguro

### Pasos

#### 1. Conectar GitHub a Vercel
```
1. Ve a https://vercel.com/login
2. Click en "GitHub" para conectar
3. Autoriza el acceso a tu repositorio
4. Vercel debería auto-detectar jokken79/YuKyuDATA-app1.0v
```

#### 2. Configurar Proyecto en Vercel
```
1. Click en "Import Project"
2. Selecciona el repositorio
3. Framework: Other (no auto-detecta porque es FastAPI)
4. Root Directory: ./
5. Build Command: npm run build
6. Install Command: pip install -r requirements.txt && npm install
```

#### 3. Configurar Variables de Entorno
En el dashboard de Vercel, ir a **Settings > Environment Variables**:

```
DEBUG=false
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./yukyu.db
CORS_ORIGINS=https://tu-dominio.vercel.app
JWT_SECRET_KEY=[generar con: python -c "import secrets; print(secrets.token_urlsafe(32))"]
JWT_REFRESH_SECRET_KEY=[generar con: python -c "import secrets; print(secrets.token_urlsafe(32))"]
DATABASE_ENCRYPTION_KEY=[generar con: python -c "import secrets; print(secrets.token_hex(32))"]
```

#### 4. Deploy
```
1. Vercel automáticamente deployará cuando hagas push a main
2. Ver progreso en Vercel Dashboard
3. Acceder a https://yukyudata-app.vercel.app (o tu URL)
```

---

## 🔑 Método 2: Deploy Manual con Vercel CLI + Token

### Cuándo usar
- No quieres usar GitHub integration
- Quieres controlar exactamente cuándo deployar
- Testing local antes de push

### Pasos

#### 1. Instalar Vercel CLI
```bash
npm install -g vercel
```

#### 2. Generar Token en Vercel
```
1. Ve a https://vercel.com/account/tokens
2. Click "Create Token"
3. Dale un nombre: "claudecode-deployment"
4. Expira en: 7 días (recomendado por seguridad)
5. Copia el token
```

⚠️ **CRÍTICO:** El token es como tu contraseña - guardarlo en `.env` local NUNCA

#### 3. Autenticar Vercel CLI
```bash
vercel login
# Pega el token cuando pida
```

O autenticar con token:
```bash
vercel --token=TU_TOKEN_AQUI
```

#### 4. Deploy (Opción A: Interactivo)
```bash
# Desde la raíz del proyecto
vercel

# Responder preguntas:
# ✔ Set up and deploy? → Yes
# ✔ Which scope? → Tu cuenta personal
# ✔ Link to existing project? → No (primera vez)
# ✔ Project name? → yukyudata-app (o el que prefieras)
# ✔ Directory? → ./
# ✔ Build command? → npm run build
```

#### 4. Deploy (Opción B: Automático - CI/CD)
```bash
vercel --prod --token A6vjlPsCrDaRt0nerIJoB792
```

---

## 📁 Estructura de Archivos Deploy

Vercel espera esta estructura:

```
/
├── main.py                          # Entry point FastAPI
├── package.json                     # Scripts npm
├── requirements.txt                 # Dependencies Python
├── vercel.json                      # Configuración Vercel
├── static/                          # Frontend (CSS, JS, assets)
│   ├── js/
│   ├── src/
│   ├── css/
│   └── media/
├── routes/v1/                       # API endpoints
├── services/                        # Lógica de negocio
├── database/                        # Datos (ORM)
├── orm/models/                      # Modelos SQLAlchemy
└── dist/                            # Build output (generado por webpack)
```

---

## 🔧 Configuración vercel.json

El archivo `vercel.json` contiene:

```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "installCommand": "pip install -r requirements.txt && npm install",
  "env": {
    "PYTHONUNBUFFERED": "1",
    "JWT_SECRET_KEY": "@JWT_SECRET_KEY",
    "DATABASE_URL": "@DATABASE_URL"
  },
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": { "runtime": "python3.12" }
    },
    {
      "src": "static/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "/static/$1" },
    { "src": "/api/(.*)", "dest": "main.py" },
    { "src": "/(.*)", "dest": "main.py" }
  ]
}
```

**Qué significa:**
- `builds`: Qué archivos compilar y cómo
- `routes`: Cómo enrutar requests
- `env`: Variables secretas (usa `@` para referenciar)

---

## 🗄️ Base de Datos en Vercel

### Opción 1: SQLite (Recomendado para MVP)
- Base de datos local en contenedor
- **Limitación:** Se reinicia en cada deploy (datos se pierden)
- **Solución:** Usar backup/restore o PostgreSQL

```bash
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./yukyu.db
```

### Opción 2: PostgreSQL (Producción)
- BD persistente en la nube
- Recomendado para datos importantes

Servicios recomendados:
- **Railway.app** (fácil integración)
- **Supabase** (PostgreSQL + auth)
- **Neon** (sin servidor)
- **AWS RDS**

Configuración:
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@host:5432/yukyu
```

---

## 🌐 Configurar Dominio Custom

### En Vercel Dashboard
```
1. Project Settings > Domains
2. Add Domain
3. Ingresar: tudominio.com
4. Vercel te da DNS records a agregar
5. Ir a tu proveedor DNS (Godaddy, Namecheap, etc)
6. Agregar los records CNAME/TXT
7. Esperar 15-30 min propagación
```

### En package.json
Actualizar `CORS_ORIGINS`:
```json
"CORS_ORIGINS": "https://tudominio.com"
```

---

## ✅ Verificar Deploy

### Logs en Vivo
```bash
vercel logs [PROJECT_NAME] --tail
```

### Health Check
```bash
curl https://tu-proyecto.vercel.app/api/health
# Response: {"status": "ok"}
```

### Endpoints Disponibles
```
GET  https://tu-proyecto.vercel.app/docs              # Swagger UI
GET  https://tu-proyecto.vercel.app/api/health        # Health
GET  https://tu-proyecto.vercel.app/api/employees     # Empleados
POST https://tu-proyecto.vercel.app/api/sync          # Sincronizar Excel
```

---

## 🔄 Redeploy Automático

### Opción 1: Push a main (GitHub Integration)
```bash
git add .
git commit -m "feat: actualizar"
git push origin main
# Vercel automáticamente deployará
```

### Opción 2: Vercel CLI
```bash
git add .
git commit -m "feat: actualizar"
vercel --prod
```

---

## 🐛 Troubleshooting

### Error: "Build failed"
```
Solución:
1. Ver logs: vercel logs [PROJECT] --tail
2. Verificar package.json - debe tener "build" script
3. Verificar requirements.txt existe
4. Correr localmente: npm run build && python main.py
```

### Error: "Module not found"
```
Solución:
1. Verificar requirements.txt tiene todas las dependencies
2. pip install -r requirements.txt localmente
3. Hacer push nuevamente
```

### Error: "Static files not found (404 on CSS/JS)"
```
Solución:
1. Verificar webpack build genera dist/
2. En vercel.json: outputDirectory: "dist"
3. Routes deben mapear /static correctamente
```

### Slow Response (> 30s)
```
Solución:
1. Vercel timeout por defecto es 30s
2. En vercel.json:
   "functions": {
     "main.py": { "maxDuration": 60 }
   }
3. Optimizar consultas SQL
```

### Base de datos vacía después de deploy
```
Razón: SQLite se reinicia con cada deploy
Soluciones:
1. Usar PostgreSQL (Ver sección Base de Datos)
2. O migrar datos via API restore
3. O usar backups + restore automático
```

---

## 🔒 Seguridad - IMPORTANTE

### ❌ NUNCA hacer esto:
```bash
# NO hardcodear secrets en código
DATABASE_URL=postgresql://user:password@host  # ❌ PROHIBIDO

# NO commitear .env
git add .env  # ❌ PROHIBIDO

# NO poner token en repositorio
vercel --token=A6vjl...  # ❌ PROHIBIDO en commit
```

### ✅ Hacer esto en su lugar:
```bash
# Usar variables en Vercel Dashboard
# Environment Variables > Add New

# Usar .env.local (local only)
echo "JWT_SECRET_KEY=..." > .env
echo ".env" >> .gitignore

# Token solo en máquina local
vercel login  # Se guarda en ~/.vercel
```

### Después de Deployar
```
🔴 REVOCA EL TOKEN INMEDIATAMENTE:
1. Ve a https://vercel.com/account/tokens
2. Busca el token usado
3. Click Delete
4. Genera uno nuevo para siguiente deploy
```

---

## 📊 Monitoreo

### Analytics en Vercel
```
Dashboard > Project > Analytics
- Page Load Time
- Core Web Vitals
- Error Rate
- Function Invocations
```

### Logs
```bash
vercel logs [PROJECT_NAME]                    # Últimos logs
vercel logs [PROJECT_NAME] --tail             # En vivo
vercel logs [PROJECT_NAME] --since 1h         # Últimas 1h
```

---

## 🆘 Soporte

**Documentación Oficial:**
- https://vercel.com/docs
- https://vercel.com/docs/concepts/deployments/environments

**Comunidad:**
- GitHub Issues: https://github.com/jokken79/YuKyuDATA-app1.0v/issues
- Discord Vercel: https://discord.gg/vercel

---

## 📝 Checklist Pre-Deploy

- [ ] `main.py` existe en raíz
- [ ] `package.json` tiene script `"build": "webpack --mode production"`
- [ ] `requirements.txt` actualizado con todas las dependencies
- [ ] `vercel.json` configurado correctamente
- [ ] `.gitignore` excluye `.env`, `node_modules/`, `dist/`
- [ ] Variables de entorno configuradas en Vercel Dashboard
- [ ] Tests pasan localmente: `pytest tests/ -v`
- [ ] Build pasa localmente: `npm run build`
- [ ] No hay secrets en código

---

## 📞 Próximos Pasos

1. **Configurar CD/CI**: GitHub Actions deploya automáticamente
2. **Monitoreo**: Setup Sentry para error tracking
3. **Database**: Migrar a PostgreSQL para producción
4. **Performance**: Optimizar Core Web Vitals

---

**Hecho con ❤️ por Claude Code**
**YuKyuDATA Team - Febrero 2026**
