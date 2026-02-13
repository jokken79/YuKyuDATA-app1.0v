# ⚖️ Yukyu Compliance Sentinel

**Centinela de Cumplimiento Legal para 労働基準法第39条**

## 📋 Descripción

Skill especializado para monitorear, analizar y garantizar el cumplimiento de la Ley de Normas Laborales de Japón (労働基準法) Artículo 39, que establece que:

> **Empleados con 10+ días otorgados DEBEN tomar al menos 5 días de vacaciones pagadas al año.**

El incumplimiento puede resultar en multas de hasta ¥300,000 por empleado.

---

## ⚡ Comandos Disponibles

### `/compliance-check`
Verifica el estado de cumplimiento de todos los empleados activos.

**Uso:**
```bash
/compliance-check [--filter=factory|all]
```

**Categorías de cumplimiento:**
- 🟢 **COMPLIANT**: ≥5日 consumidos
- 🟡 **AT_RISK**: 3-4日 consumidos (necesita acción)
- 🟠 **HIGH_RISK**: 1-2日 consumidos (urgente)
- 🔴 **CRITICAL**: 0日 consumidos (crítico)
- ⚪ **EXEMPT**: <10日 otorgados (exento de obligación)

**Salida:**
```
⚖️ ESTADO DE CUMPLIMIENTO LEGAL - 労働基準法39条
═══════════════════════════════════════════════════

📊 Resumen General:
  Total empleados activos: 45
  Exentos (付与 <10日): 5
  Sujetos a obligación: 40

  🟢 COMPLIANT: 32 (80%)
  🟡 AT_RISK: 4 (10%)
  🟠 HIGH_RISK: 3 (7.5%)
  🔴 CRITICAL: 1 (2.5%)

⚠️ ALERTA: 8 empleados requieren acción inmediata
```

---

### `/compliance-risk`
Analiza detalladamente empleados en riesgo de incumplimiento.

**Uso:**
```bash
/compliance-risk [--severity=all|critical|high|medium]
```

**Información por empleado:**
- Días faltantes para cumplir
- Días disponibles en balance
- Historial de uso
- Patrón de consumo
- Recomendación de acción

**Salida:**
```
🚨 EMPLEADOS EN RIESGO DE INCUMPLIMIENTO
════════════════════════════════════════

🔴 CRÍTICO (0日 consumidos):
1. 山田 太郎 (YT0001) - 株式会社ABC
   付与: 14日 | 消化: 0日 | 残高: 14日
   ⚠️ Necesita: 5日 para cumplir
   📅 Patrón: Sin uso en últimos 6 meses
   💡 Acción: Programar 5日 antes de fin de período

🟠 ALTO RIESGO (1-2日 consumidos):
2. 佐藤 花子 (SH0002) - 工場XYZ
   付与: 12日 | 消化: 2日 | 残高: 10日
   ⚠️ Necesita: 3日 adicionales
   📅 Último uso: 2024-08-15
   💡 Acción: Programar 3日 en próximos 2 meses
```

---

### `/compliance-deadline`
Calcula fechas límite de cumplimiento para cada empleado.

**Uso:**
```bash
/compliance-deadline [employeeId]
```

**Lógica de cálculo:**
- Basado en `yukyuStartDate` del período actual
- Deadline = 1 año desde otorgamiento
- Alerta 60, 30, 14, 7 días antes

**Salida:**
```
📅 FECHAS LÍMITE DE CUMPLIMIENTO
═══════════════════════════════

Empleado: 山田 太郎 (YT0001)
Período actual: 2年6ヶ月 (付与: 12日)
Fecha de otorgamiento: 2024-04-01
Fecha límite: 2025-03-31

⏰ Estado: 89 días restantes
🔴 Días faltantes: 5日
📊 Ritmo necesario: 0.56日/semana

💡 Recomendación:
   Programar al menos 2日 en enero y 3日 en febrero
   para evitar incumplimiento.
```

---

### `/compliance-report`
Genera reporte formal de cumplimiento para auditorías externas.

**Uso:**
```bash
/compliance-report [--format=pdf|csv|excel] [--period=current|fiscal-year]
```

**Contenido del reporte:**
1. Resumen ejecutivo de cumplimiento
2. Lista de empleados exentos
3. Lista de empleados en cumplimiento
4. Detalle de empleados en riesgo
5. Acciones recomendadas
6. Historial de mejoras
7. Firma digital (timestamp)

**Formato PDF:**
```
═══════════════════════════════════════════════════════════════
              有給休暇取得義務 コンプライアンスレポート
                 労働基準法第39条第7項
═══════════════════════════════════════════════════════════════

会社名: [Company Name]
報告期間: 2024-04-01 ～ 2025-03-31
生成日: 2025-01-09

1. エグゼクティブサマリー
   対象社員数: 40名
   義務達成率: 80%
   要対応社員: 8名

2. リスク分析
   [Tabla de riesgos por severidad]

3. 推奨アクション
   [Lista de acciones por prioridad]

                                    _______________
                                    人事部長 署名
```

---

### `/compliance-predict`
Usa IA (Gemini) para predecir riesgos futuros de incumplimiento.

**Uso:**
```bash
/compliance-predict [--horizon=30|60|90 days]
```

**Análisis predictivo:**
- Patrones históricos de uso
- Tendencias estacionales
- Comportamiento por departamento
- Factores de riesgo identificados

**Salida:**
```
🤖 ANÁLISIS PREDICTIVO DE CUMPLIMIENTO (Gemini AI)
════════════════════════════════════════════════════

📊 Predicción a 90 días:

Riesgo de incumplimiento proyectado:
  🔴 Crítico: 3 empleados (↑2 vs actual)
  🟠 Alto: 5 empleados (↑1 vs actual)
  🟡 Medio: 8 empleados (→ sin cambio)

🎯 Factores de riesgo identificados:
  1. Temporada alta en fábrica A (dic-feb)
  2. 5 empleados sin uso en últimos 4 meses
  3. Patrón de "last-minute" en grupo B

💡 Recomendaciones IA:
  1. Enviar recordatorios automáticos a empleados
     con <3日 consumidos y >4 meses sin uso
  2. Programar 計画年休 para grupo de alto riesgo
  3. Considerar política de uso obligatorio en
     períodos de baja producción
```

---

## 🔧 Integración con Dashboard

El Compliance Sentinel se integra automáticamente con el Dashboard:

```typescript
// Dashboard.tsx - Legal Risk Section
const legalAlerts = useMemo(() => {
  return activeEmployees.filter(emp =>
    emp.grantedTotal >= 10 &&
    emp.usedTotal < 5 &&
    emp.status === '在職中'
  );
}, [activeEmployees]);
```

**Indicadores en Dashboard:**
- KPI de empleados en riesgo
- Gráfico de distribución de cumplimiento
- Panel de alertas con detalle de déficit

---

## 📊 Métricas Clave

| Métrica | Descripción | Umbral |
|---------|-------------|--------|
| **Compliance Rate** | % empleados cumpliendo | ≥95% objetivo |
| **Days Deficit** | Días faltantes totales | 0 objetivo |
| **Risk Velocity** | Cambio en riesgo vs mes anterior | <0 objetivo |
| **Time to Deadline** | Días promedio hasta límite | >60 días saludable |

---

## ⚠️ Consecuencias Legales

### Multas por incumplimiento (労働基準法第120条):
- **¥300,000** por empleado en incumplimiento
- **Responsabilidad del empleador**, no del empleado
- **Registro público** de infracciones

### Excepciones (計画年休):
- Empleados pueden diferir hasta 5日 con acuerdo
- Debe documentarse por escrito
- No aplica si empleado rechaza tomar vacaciones

---

## 🚀 Flujo de Trabajo Recomendado

```
1. Inicio de período fiscal (abril)
   └─ /compliance-check → Baseline

2. Mensualmente
   └─ /compliance-risk → Monitoreo

3. 90 días antes de fin de período
   └─ /compliance-predict → Predicción

4. 30 días antes de fin de período
   └─ /compliance-deadline → Alertas finales

5. Fin de período fiscal
   └─ /compliance-report → Auditoría
```

---

## 🔒 Garantías

✅ Cálculos basados en datos reales de `periodHistory`
✅ Alertas automatizadas por severidad
✅ Reportes exportables para auditorías
✅ Predicciones con IA para prevención
✅ Cumplimiento con 労働基準法39条7項
✅ Historial de acciones documentado

---

## 📄 Licencia

MIT - Uso libre para empresas
