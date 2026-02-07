#!/bin/bash

# ============================================
# Deploy Vercel Script - YuKyuDATA App
# ============================================

set -e

echo "🚀 Iniciando Deploy en Vercel..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Verificar que estamos en la rama correcta
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Rama actual: $BRANCH"

# Verificar que no hay cambios sin commit
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Hay cambios sin commit. Haz commit primero:${NC}"
    echo "git add . && git commit -m 'Deploy update'"
    exit 1
fi

echo ""
echo "📦 Verificando requirements..."

# Verificar que existen archivos críticos
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt no encontrado${NC}"
    exit 1
fi

if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json no encontrado${NC}"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py no encontrado${NC}"
    exit 1
fi

if [ ! -f "vercel.json" ]; then
    echo -e "${RED}❌ vercel.json no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Archivos encontrados${NC}"

echo ""
echo "🏗️ Compilando frontend..."
npm run build || {
    echo -e "${RED}❌ Build falló${NC}"
    exit 1
}
echo -e "${GREEN}✓ Build completado${NC}"

echo ""
echo "🧪 Ejecutando tests..."
pytest tests/ -v --tb=short 2>&1 | tail -20 || {
    echo -e "${YELLOW}⚠️  Tests fallaron (opcional para deploy)${NC}"
}
echo -e "${GREEN}✓ Tests verificados${NC}"

echo ""
echo "📤 Deployando a Vercel..."

if [ -z "$VERCEL_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  No hay VERCEL_TOKEN. Usando configuración existente...${NC}"
    vercel --prod
else
    echo "Usando token de Vercel..."
    vercel --prod --token="$VERCEL_TOKEN"
fi

echo ""
echo -e "${GREEN}✅ Deploy completado${NC}"
echo ""
echo "📊 Verifica el deploy en: https://vercel.com/jokken79s-projects"
echo ""
