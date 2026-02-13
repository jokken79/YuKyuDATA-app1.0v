# 🧪 Yukyu Test Suite

**Suite de Testing Completa para Yukyu Pro**

## 📋 Descripción

Skill especializado para generar, ejecutar y analizar tests en Yukyu Pro. Incluye:

- Unit tests para servicios
- Component tests para React
- Integration tests para flujos
- E2E scenarios para casos de uso
- Coverage analysis

---

## ⚡ Comandos Disponibles

### `/test-generate`
Genera tests automáticamente para servicios y componentes.

**Uso:**
```bash
/test-generate <target> [--type=unit|component|integration]
```

**Targets válidos:**
- `services/db` - Tests para servicio de base de datos
- `services/balanceCalculator` - Tests para cálculos de balance
- `services/validationService` - Tests para validaciones
- `components/Dashboard` - Tests para Dashboard
- `all` - Generar para todo

**Salida:**
```
🧪 GENERACIÓN DE TESTS
═══════════════════════════════════════════════════

Target: services/balanceCalculator
Tipo: unit

📝 ARCHIVO GENERADO: services/__tests__/balanceCalculator.test.ts

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import {
  getEmployeeBalance,
  getEmployeePeriods,
  isLegalRisk,
  getDaysNeededForCompliance
} from '../balanceCalculator';
import { Employee, PeriodHistory } from '../../types';

describe('balanceCalculator', () => {
  describe('getEmployeeBalance', () => {
    it('should return legacy values when no entryDate', () => {
      const employee: Employee = {
        id: 'TEST001',
        name: 'Test User',
        client: 'Test Client',
        grantedTotal: 10,
        usedTotal: 5,
        balance: 5,
        expiredCount: 0,
        status: '在職中',
        lastSync: new Date().toISOString()
      };

      const result = getEmployeeBalance(employee);

      expect(result.granted).toBe(10);
      expect(result.used).toBe(5);
      expect(result.remaining).toBe(5);
    });

    it('should calculate from periodHistory when available', () => {
      const employee = createEmployeeWithPeriodHistory([
        { granted: 10, used: 6, isExpired: true },
        { granted: 11, used: 3, isExpired: false }
      ]);

      const result = getEmployeeBalance(employee);

      expect(result.granted).toBe(11); // Only non-expired
      expect(result.used).toBe(9);     // Total used
      expect(result.remaining).toBe(8); // 11 - 3
    });

    it('should handle half-day (半日) correctly', () => {
      const employee = createEmployeeWithDates([
        '2024-01-15',
        '2024-01-16:half',
        '2024-01-17'
      ]);

      const result = getEmployeeBalance(employee);

      expect(result.used).toBe(2.5); // 1 + 0.5 + 1
    });

    it('should cap balance at 40 days legal limit', () => {
      const employee = createEmployeeWithPeriodHistory([
        { granted: 20, used: 0, isExpired: false },
        { granted: 20, used: 0, isExpired: false },
        { granted: 20, used: 0, isExpired: false }
      ]);

      const result = getEmployeeBalance(employee);

      expect(result.remaining).toBeLessThanOrEqual(40);
    });
  });

  describe('isLegalRisk', () => {
    it('should return true when granted>=10 and used<5', () => {
      expect(isLegalRisk({ grantedTotal: 10, usedTotal: 4 })).toBe(true);
      expect(isLegalRisk({ grantedTotal: 14, usedTotal: 0 })).toBe(true);
    });

    it('should return false when exempt', () => {
      expect(isLegalRisk({ grantedTotal: 9, usedTotal: 0 })).toBe(false);
    });

    it('should return false when compliant', () => {
      expect(isLegalRisk({ grantedTotal: 12, usedTotal: 5 })).toBe(false);
    });
  });
});
```

✅ Tests generados: 12
📊 Cobertura estimada: 85%
```

---

### `/test-coverage`
Analiza la cobertura de código actual.

**Uso:**
```bash
/test-coverage [--threshold=80] [--report=html|console]
```

**Salida:**
```
📊 ANÁLISIS DE COBERTURA
═══════════════════════════════════════════════════

Estado actual: ⚠️ SIN TESTS CONFIGURADOS

📋 COBERTURA ESTIMADA POR ANÁLISIS ESTÁTICO:

SERVICIOS (críticos):
┌──────────────────────────────────────────────────┐
│ db.ts                 ░░░░░░░░░░  0% │ CRÍTICO  │
│ balanceCalculator.ts  ░░░░░░░░░░  0% │ CRÍTICO  │
│ validationService.ts  ░░░░░░░░░░  0% │ CRÍTICO  │
│ expirationService.ts  ░░░░░░░░░░  0% │ ALTO     │
│ mergeService.ts       ░░░░░░░░░░  0% │ ALTO     │
│ exportService.ts      ░░░░░░░░░░  0% │ MEDIO    │
│ nameConverter.ts      ░░░░░░░░░░  0% │ BAJO     │
└──────────────────────────────────────────────────┘

COMPONENTES:
┌──────────────────────────────────────────────────┐
│ Dashboard.tsx         ░░░░░░░░░░  0% │ MEDIO    │
│ EmployeeList.tsx      ░░░░░░░░░░  0% │ MEDIO    │
│ ApplicationMgmt.tsx   ░░░░░░░░░░  0% │ ALTO     │
│ LeaveRequest.tsx      ░░░░░░░░░░  0% │ ALTO     │
│ ExcelSync.tsx         ░░░░░░░░░░  0% │ CRÍTICO  │
└──────────────────────────────────────────────────┘

💡 PLAN DE TESTING RECOMENDADO:

Prioridad 1 (Critical Path):
  1. db.ts - CRUD y flujos de aprobación
  2. balanceCalculator.ts - Cálculos de balance
  3. validationService.ts - Validaciones de negocio

Prioridad 2 (Business Logic):
  4. expirationService.ts - Cálculo de expiraciones
  5. mergeService.ts - Merge de Excel

Prioridad 3 (UI Flows):
  6. ApplicationManagement - Flujo de aprobación
  7. LeaveRequest - Creación de solicitudes
  8. ExcelSync - Importación

📦 SETUP REQUERIDO:

npm install -D vitest @testing-library/react @testing-library/jest-dom
```

---

### `/test-scenarios`
Genera escenarios de prueba de negocio (BDD-style).

**Uso:**
```bash
/test-scenarios [--flow=approval|import|compliance|all]
```

**Salida:**
```
📋 ESCENARIOS DE PRUEBA - FLUJO DE APROBACIÓN
═══════════════════════════════════════════════════

Feature: Aprobación de Solicitudes de Yukyu
  Como manager
  Quiero aprobar solicitudes de vacaciones
  Para que los empleados puedan tomar sus días

Scenario: Aprobar solicitud con balance suficiente
  Given un empleado "山田太郎" con balance de 10日
  And una solicitud pendiente para "2025-01-15" (día completo)
  When el manager aprueba la solicitud
  Then el estado cambia a "approved"
  And el balance del empleado se reduce a 9日
  And la fecha se agrega a yukyuDates[]
  And se muestra toast de confirmación

Scenario: Aprobar solicitud de medio día
  Given un empleado con balance de 5日
  And una solicitud pendiente para "2025-01-16" (半日)
  When el manager aprueba la solicitud
  Then el balance se reduce en 0.5日
  And yukyuDates contiene "2025-01-16:half"

Scenario: Rechazar aprobación por balance insuficiente
  Given un empleado "佐藤花子" con balance de 0日
  And una solicitud pendiente
  When el manager intenta aprobar
  Then la aprobación es rechazada
  And se muestra error "残高不足"
  And el código de error es "INSUFFICIENT_BALANCE"

Scenario: Rechazar aprobación por fecha duplicada
  Given un empleado con yukyuDates incluyendo "2025-01-15"
  And una solicitud para la misma fecha
  When el manager intenta aprobar
  Then la aprobación es rechazada
  And se muestra error "重複"
  And el código es "DUPLICATE_DATE"

Scenario: Rechazar aprobación de empleado retirado
  Given un empleado con status "退社"
  And una solicitud pendiente
  When el manager intenta aprobar
  Then la aprobación es rechazada
  And el código es "EMPLOYEE_RETIRED"

Scenario: Aprobación masiva
  Given 5 solicitudes pendientes de diferentes empleados
  When el manager selecciona todas y aprueba
  Then se muestran resultados: N éxitos, M fallos
  And cada fallo incluye razón específica

---

📋 ESCENARIOS DE PRUEBA - IMPORTACIÓN EXCEL
═══════════════════════════════════════════════════

Feature: Sincronización con Excel
  Como administrador
  Quiero importar datos desde Excel
  Para mantener el sistema actualizado

Scenario: Primera sincronización DAICHO
  Given un archivo Excel con 3 hojas (DBGenzaiX, DBUkeoiX, DBStaffX)
  And no hay empleados en el sistema
  When importo el archivo DAICHO
  Then se crean todos los empleados nuevos
  And cada empleado tiene: id, name, client, entryDate, status

Scenario: Re-sincronización YUKYU preserva aprobaciones locales
  Given empleados existentes con aprobaciones locales
  And un archivo YUKYU con datos actualizados
  When importo el archivo YUKYU
  Then los datos de Excel se actualizan
  And las aprobaciones locales se preservan
  And no hay fechas duplicadas

Scenario: Detección de conflictos en re-sync
  Given un empleado con 10 fechas en yukyuDates
  And un Excel con solo 8 fechas para el mismo empleado
  When importo el archivo
  Then se detecta conflicto "Excel tiene menos fechas"
  And se muestra warning al usuario
  And las fechas locales adicionales se preservan
```

---

### `/test-edge-cases`
Identifica y genera tests para casos edge.

**Uso:**
```bash
/test-edge-cases [--service=name]
```

**Salida:**
```
🔍 EDGE CASES IDENTIFICADOS
═══════════════════════════════════════════════════

📋 balanceCalculator.ts:

1. EMPLEADO SIN ENTRY DATE
   Input: employee.entryDate = undefined
   Expected: Retornar valores legacy sin error
   Test:
   ```typescript
   it('handles missing entryDate gracefully', () => {
     const emp = { ...baseEmployee, entryDate: undefined };
     expect(() => getEmployeeBalance(emp)).not.toThrow();
   });
   ```

2. PERÍODO CON TODAS LAS FECHAS EXPIRADAS
   Input: periodHistory donde todos isExpired = true
   Expected: granted = 0, remaining = 0
   Test:
   ```typescript
   it('returns zero balance when all periods expired', () => {
     const emp = createWithAllExpiredPeriods();
     const result = getEmployeeBalance(emp);
     expect(result.remaining).toBe(0);
   });
   ```

3. BALANCE EXCEDE 40 DÍAS
   Input: Múltiples períodos vigentes sumando >40日
   Expected: remaining capped at 40
   Test:
   ```typescript
   it('caps balance at legal limit of 40 days', () => {
     const emp = createWithExcessBalance();
     expect(getEmployeeBalance(emp).remaining).toBe(40);
   });
   ```

4. FECHA CON FORMATO INVÁLIDO EN YUKYUDATES
   Input: yukyuDates = ["2024-01-15", "invalid", "2024-01-16"]
   Expected: Ignorar inválidas, procesar válidas
   Test:
   ```typescript
   it('skips invalid dates in yukyuDates', () => {
     const emp = createWithInvalidDates();
     expect(() => getEmployeeBalance(emp)).not.toThrow();
   });
   ```

5. MEDIO DÍA EN BORDE DE PERÍODO
   Input: "2024-03-31:half" (último día de período)
   Expected: Contabilizar correctamente en período correcto
   Test:
   ```typescript
   it('assigns half-day to correct period at boundary', () => {
     // ...
   });
   ```

📋 validationService.ts:

6. EMPLEADO CON ID VACÍO
   Input: record.employeeId = ""
   Expected: Retornar EMPLOYEE_NOT_FOUND

7. FECHA EN FUTURO LEJANO
   Input: record.date = "2030-01-01"
   Expected: Permitir (no hay restricción de futuro)

8. APROBACIÓN DURANTE MIGRACIÓN
   Input: Aprobar mientras loadData() está en progreso
   Expected: Race condition handling

📋 mergeService.ts:

9. EXCEL CON FECHAS DUPLICADAS
   Input: Columnas 1 y 5 con misma fecha
   Expected: Deduplicar sin error

10. EMPLEADO EN EXCEL PERO NO EN LOCAL
    Input: Excel tiene empleado que no existe localmente
    Expected: Crear nuevo empleado
```

---

### `/test-regression`
Crea suite de regresión para bugs conocidos.

**Uso:**
```bash
/test-regression [--include-fixed]
```

**Salida:**
```
🐛 SUITE DE REGRESIÓN
═══════════════════════════════════════════════════

Tests para bugs conocidos y corregidos:

BUG #1: Re-sync Excel sobrescribe aprobaciones locales
Status: ✅ FIXED
Test:
```typescript
describe('BUG #1 Regression: Excel re-sync preserves local approvals', () => {
  it('should preserve local approvals during re-sync', async () => {
    // Setup: Employee with local approval
    const employee = createEmployeeWithLocalApproval('2025-01-15');

    // Action: Re-sync with Excel (missing 2025-01-15)
    const excelData = createExcelDataWithoutDate('2025-01-15');
    const result = mergeExcelData(excelData, employee);

    // Assert: Local approval preserved
    expect(result.employee.yukyuDates).toContain('2025-01-15');
    expect(result.warnings).toContain('local approval preserved');
  });
});
```

BUG #2: Balance negativo al aprobar
Status: ✅ FIXED
Test:
```typescript
describe('BUG #2 Regression: Prevent negative balance', () => {
  it('should reject approval when balance is 0', () => {
    const employee = { ...baseEmployee, balance: 0 };
    const record = createPendingRecord();

    const result = canApproveLeave(employee, record);

    expect(result.isValid).toBe(false);
    expect(result.code).toBe('INSUFFICIENT_BALANCE');
  });
});
```

BUG #4: yukyuDates no sincroniza con aprobación
Status: ✅ FIXED
Test:
```typescript
describe('BUG #4 Regression: yukyuDates syncs on approval', () => {
  it('should add date to yukyuDates when approved', async () => {
    const data = createTestData();
    const recordId = data.records[0].id;

    await db.approveRecord(recordId);

    const updated = db.loadData();
    const employee = updated.employees[0];
    expect(employee.yukyuDates).toContain(data.records[0].date);
  });
});
```

BUG #6: CSV Formula Injection
Status: ✅ FIXED
Test:
```typescript
describe('BUG #6 Regression: CSV sanitization', () => {
  it('should escape formula characters', () => {
    const malicious = '=SUM(A1:A10)';
    const sanitized = sanitizeValue(malicious);

    expect(sanitized).not.toStartWith('=');
    expect(sanitized).toBe("'=SUM(A1:A10)");
  });
});
```

📊 RESUMEN:
  Bugs conocidos: 6
  Tests de regresión: 12
  Cobertura de bugs: 100%
```

---

## 🛠️ Setup de Testing

```bash
# Instalar dependencias
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom

# Agregar a package.json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest --coverage",
    "test:ui": "vitest --ui"
  }
}

# Crear vitest.config.ts
export default {
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/setup.ts'
  }
}
```

---

## 📄 Licencia

MIT - Uso libre para empresas
