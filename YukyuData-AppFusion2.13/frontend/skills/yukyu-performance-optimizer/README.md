# ⚡ Yukyu Performance Optimizer

**Optimizador de Rendimiento para React + localStorage**

## 📋 Descripción

Skill especializado para analizar, monitorear y optimizar el rendimiento de Yukyu Pro. Incluye herramientas para:

- Profiling de React components
- Optimización de localStorage
- Análisis de bundle size
- Detección de re-renders innecesarios
- Mejoras automáticas de código

---

## ⚡ Comandos Disponibles

### `/perf-analyze`
Ejecuta análisis completo de rendimiento de la aplicación.

**Uso:**
```bash
/perf-analyze [--deep] [--export=json]
```

**Métricas analizadas:**
- Time to Interactive (TTI)
- First Contentful Paint (FCP)
- localStorage read/write times
- Component render counts
- Memory usage
- Bundle chunk sizes

**Salida:**
```
⚡ ANÁLISIS DE RENDIMIENTO - YUKYU PRO
═══════════════════════════════════════════════════

📊 MÉTRICAS CORE WEB VITALS:
  FCP (First Contentful Paint): 1.2s ✅ (< 1.8s)
  LCP (Largest Contentful Paint): 2.1s ✅ (< 2.5s)
  TTI (Time to Interactive): 2.8s ⚠️ (< 3.8s pero mejorable)
  TBT (Total Blocking Time): 180ms ✅ (< 200ms)

📦 BUNDLE SIZE:
  Total: 847 KB
  ├─ vendor.js: 512 KB (60%)
  │  ├─ react: 45 KB
  │  ├─ recharts: 234 KB ⚠️ (grande)
  │  ├─ xlsx: 178 KB ⚠️ (grande)
  │  └─ otros: 55 KB
  ├─ app.js: 285 KB (34%)
  └─ css: 50 KB (6%)

💾 localStorage:
  Uso actual: 1.2 MB / 5 MB (24%)
  Tiempo de lectura: 45ms ⚠️ (>30ms)
  Empleados: 156
  Registros: 847

⚛️ REACT COMPONENTS:
  Renders por carga inicial: 12
  Componentes con useMemo: 6/11 ⚠️
  Componentes sin optimizar: 5

💡 RECOMENDACIONES:
  1. Lazy load recharts (solo en Dashboard)
  2. Lazy load xlsx (solo en ExcelSync)
  3. Agregar useMemo a LeaveRequest, AccountingReports
  4. Considerar IndexedDB para datos >2MB
```

---

### `/perf-storage`
Analiza y optimiza el uso de localStorage.

**Uso:**
```bash
/perf-storage [--cleanup] [--compress]
```

**Análisis:**
- Tamaño de datos almacenados
- Tiempo de serialización/deserialización
- Datos duplicados
- Datos obsoletos

**Salida:**
```
💾 ANÁLISIS DE localStorage
═══════════════════════════════════════════════════

📊 USO ACTUAL:
  Clave: yukyu_pro_storage
  Tamaño: 1.2 MB
  Límite: 5 MB (24% usado)

📋 DESGLOSE POR SECCIÓN:
  employees[]: 856 KB (71%)
  ├─ periodHistory: 512 KB (42%)
  ├─ yukyuDates: 234 KB (19%)
  └─ otros campos: 110 KB (9%)

  records[]: 312 KB (26%)
  config{}: 2 KB (0.2%)
  _meta: 30 KB (2.5%)

⏱️ TIEMPOS DE OPERACIÓN:
  JSON.parse(): 45ms ⚠️
  JSON.stringify(): 38ms ⚠️
  Lectura completa: 48ms
  Escritura completa: 42ms

🔍 PROBLEMAS DETECTADOS:
  1. yukyuDates duplicados en 3 empleados
     Ahorro potencial: 12 KB

  2. periodHistory con fechas como string y Date mezclados
     Recomendación: Normalizar a ISO string

  3. Records rechazados >6 meses sin limpiar
     Candidatos a eliminar: 45 registros (23 KB)

💡 OPTIMIZACIONES DISPONIBLES:
  /perf-storage --cleanup  → Limpiar datos obsoletos
  /perf-storage --compress → Compresión LZ-string (experimental)
```

---

### `/perf-components`
Analiza re-renders de componentes React.

**Uso:**
```bash
/perf-components [--watch] [--component=name]
```

**Análisis:**
- Renders por interacción
- Props que causan re-renders
- Callbacks no memorizados
- Context consumers

**Salida:**
```
⚛️ ANÁLISIS DE RE-RENDERS
═══════════════════════════════════════════════════

📊 RENDERS POR COMPONENTE (última interacción):

Dashboard.tsx:
  Renders: 1 ✅
  useMemo hooks: 8 ✅
  useCallback hooks: 2 ✅
  Optimizado: ✅

EmployeeList.tsx:
  Renders: 1 ✅
  useMemo hooks: 4 ✅
  useCallback hooks: 1 ✅
  Optimizado: ✅

ApplicationManagement.tsx:
  Renders: 3 ⚠️
  useMemo hooks: 2
  useCallback hooks: 0 ❌
  Problema: callbacks recreados en cada render

LeaveRequest.tsx:
  Renders: 5 ⚠️
  useMemo hooks: 3
  useCallback hooks: 0 ❌
  Problema:
    - handleSubmit recreado
    - filteredEmployees no memoizado
    - formData updates causan cascada

AccountingReports.tsx:
  Renders: 2 ⚠️
  useMemo hooks: 1
  useCallback hooks: 0 ❌
  Problema: period calculation en cada render

💡 FIXES SUGERIDOS:

1. ApplicationManagement.tsx:
   ```typescript
   // Antes
   const handleApprove = () => { ... }

   // Después
   const handleApprove = useCallback(() => { ... }, [deps])
   ```

2. LeaveRequest.tsx:
   ```typescript
   // Agregar useMemo para filteredEmployees
   const filteredEmployees = useMemo(() =>
     employees.filter(e => e.client === selectedClient),
     [employees, selectedClient]
   );
   ```
```

---

### `/perf-bundle`
Analiza el tamaño del bundle y dependencias.

**Uso:**
```bash
/perf-bundle [--treemap] [--unused]
```

**Análisis:**
- Chunks generados
- Dependencias por tamaño
- Código no utilizado
- Oportunidades de lazy loading

**Salida:**
```
📦 ANÁLISIS DE BUNDLE
═══════════════════════════════════════════════════

📊 BUILD STATS:
  Total: 847 KB (gzipped: 245 KB)
  Tiempo de build: 4.2s
  Chunks: 3

📋 CHUNKS DETALLE:

vendor-xxxxx.js (512 KB / 148 KB gzip):
┌─────────────────────────────────────────┐
│ recharts       ████████████████ 234 KB │ 46%
│ xlsx           ███████████      178 KB │ 35%
│ react-dom      ████             42 KB  │ 8%
│ framer-motion  ███              35 KB  │ 7%
│ otros          █                23 KB  │ 4%
└─────────────────────────────────────────┘

app-xxxxx.js (285 KB / 82 KB gzip):
┌─────────────────────────────────────────┐
│ components     ████████████     156 KB │ 55%
│ services       ████████         89 KB  │ 31%
│ types          ██               24 KB  │ 8%
│ utils          █                16 KB  │ 6%
└─────────────────────────────────────────┘

🔍 OPORTUNIDADES DE OPTIMIZACIÓN:

1. RECHARTS (234 KB → ~50 KB con lazy load)
   Solo se usa en Dashboard

   // vite.config.ts
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           charts: ['recharts']
         }
       }
     }
   }

   // Dashboard.tsx
   const Recharts = lazy(() => import('recharts'));

2. XLSX (178 KB → 0 KB en carga inicial)
   Solo se usa en ExcelSync

   const XLSX = lazy(() => import('xlsx'));

3. FRAMER-MOTION (35 KB)
   Considerar solo usar en transiciones críticas
   O reemplazar con CSS transitions

📊 IMPACTO ESTIMADO:
  Carga inicial: 847 KB → 435 KB (-49%)
  TTI: 2.8s → ~1.8s (-36%)
```

---

### `/perf-optimize`
Aplica optimizaciones automáticas al código.

**Uso:**
```bash
/perf-optimize [--type=all|hooks|imports|storage] [--dry-run]
```

**Optimizaciones disponibles:**

**hooks**: Agregar useMemo/useCallback faltantes
**imports**: Convertir a lazy imports
**storage**: Optimizar operaciones de localStorage

**Salida:**
```
🔧 OPTIMIZACIÓN AUTOMÁTICA
═══════════════════════════════════════════════════

📋 CAMBIOS A APLICAR:

1. LeaveRequest.tsx (línea 45):
   + import { useMemo, useCallback } from 'react';

   - const filteredEmployees = employees.filter(...)
   + const filteredEmployees = useMemo(() =>
   +   employees.filter(...),
   +   [employees, selectedClient]
   + );

2. ApplicationManagement.tsx (línea 78):
   - const handleApprove = () => { ... }
   + const handleApprove = useCallback(() => { ... }, [data]);

3. vite.config.ts:
   + manualChunks: {
   +   charts: ['recharts'],
   +   excel: ['xlsx']
   + }

4. Dashboard.tsx (línea 1):
   + const Recharts = React.lazy(() => import('recharts'));
   +
   + // En render
   + <Suspense fallback={<ChartSkeleton />}>
   +   <Recharts.AreaChart ... />
   + </Suspense>

✅ Aplicar cambios: /perf-optimize --type=all
📝 Solo preview: /perf-optimize --dry-run
```

---

## 📊 Métricas de Referencia

| Métrica | Actual | Objetivo | Estado |
|---------|--------|----------|--------|
| Bundle size | 847 KB | <500 KB | ⚠️ |
| TTI | 2.8s | <2s | ⚠️ |
| localStorage read | 45ms | <30ms | ⚠️ |
| Re-renders/action | 3 avg | 1 | ⚠️ |
| Memory (heap) | 45 MB | <50 MB | ✅ |

---

## 🎯 Quick Wins

### 1. Lazy Loading (impacto: alto)
```typescript
// Dashboard.tsx
const Recharts = lazy(() => import('recharts'));
```

### 2. useMemo en listas (impacto: medio)
```typescript
const filteredEmployees = useMemo(() =>
  employees.filter(e => e.status === '在職中'),
  [employees]
);
```

### 3. Debounce en búsqueda (impacto: medio)
```typescript
const debouncedSearch = useMemo(
  () => debounce((term) => setSearchTerm(term), 300),
  []
);
```

### 4. Virtualización de listas largas (impacto: alto)
```typescript
// Para listas >100 items
import { FixedSizeList } from 'react-window';
```

---

## 📄 Licencia

MIT - Uso libre para empresas
