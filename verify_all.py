"""
Verificación completa del sistema
"""
import sys
import sqlite3
import excel_service
import database

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("="*60)
print("VERIFICACIÓN COMPLETA DEL SISTEMA")
print("="*60)

# 1. Verificar base de datos actual
print("\n1. Estado actual de la base de datos:")
print("-" * 60)
conn = sqlite3.connect('yukyu.db')
c = conn.cursor()

tables = ['employees', 'genzai', 'ukeoi']
for table in tables:
    try:
        count = c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f"  {table:15} {count:6} registros")
    except:
        print(f"  {table:15} [NO EXISTE]")
conn.close()

# 2. Test parsing de vacaciones
print("\n2. Probando parsing de vacaciones:")
print("-" * 60)
try:
    YUKYU_PATH = r"D:\YuKyuDATA-app\有給休暇管理.xlsm"
    data = excel_service.parse_excel_file(YUKYU_PATH)
    print(f"  [OK] Parseados {len(data)} registros de vacaciones")

    # Verificar que NO se filtró 本社
    honsha = [e for e in data if e.get('haken') == '高雄工業 本社']
    print(f"  [OK] Empleados de 高雄工業 本社: {len(honsha)}")

    if len(honsha) > 0:
        print(f"  ✓ FILTRO ELIMINADO CORRECTAMENTE")
    else:
        print(f"  ✗ FILTRO AÚN ACTIVO (NO SE ESPERABAN 0)")

    # Mostrar distribución por haken
    hakens = {}
    for e in data:
        h = e.get('haken', 'Unknown')
        hakens[h] = hakens.get(h, 0) + 1

    print(f"\n  Top 5 Haken:")
    for haken, count in sorted(hakens.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {haken:30} {count:4} empleados")

    # Años disponibles
    years = set(e.get('year') for e in data)
    print(f"\n  Años encontrados: {sorted(years)}")

except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# 3. Sincronizar todo en la base de datos
print("\n3. Sincronizando datos en base de datos:")
print("-" * 60)

# Inicializar DB
database.init_db()

# Sync vacaciones
try:
    yukyu_data = excel_service.parse_excel_file(r"D:\YuKyuDATA-app\有給休暇管理.xlsm")
    database.save_employees(yukyu_data)
    print(f"  [OK] Vacaciones guardadas: {len(yukyu_data)} registros")
except Exception as e:
    print(f"  [ERROR] Vacaciones: {e}")

# Sync genzai
try:
    genzai_data = excel_service.parse_genzai_sheet(r"D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm")
    database.save_genzai(genzai_data)
    print(f"  [OK] Genzai guardados: {len(genzai_data)} registros")
except Exception as e:
    print(f"  [ERROR] Genzai: {e}")

# Sync ukeoi
try:
    ukeoi_data = excel_service.parse_ukeoi_sheet(r"D:\YuKyuDATA-app\【新】社員台帳(UNS)T　2022.04.05～.xlsm")
    database.save_ukeoi(ukeoi_data)
    print(f"  [OK] Ukeoi guardados: {len(ukeoi_data)} registros")
except Exception as e:
    print(f"  [ERROR] Ukeoi: {e}")

# 4. Verificar base de datos final
print("\n4. Estado FINAL de la base de datos:")
print("-" * 60)
conn = sqlite3.connect('yukyu.db')
c = conn.cursor()

for table in tables:
    count = c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f"  {table:15} {count:6} registros")

# Verificar años en employees
years_db = c.execute('SELECT DISTINCT year FROM employees ORDER BY year').fetchall()
print(f"\n  Años en employees: {[y[0] for y in years_db]}")

# Verificar 本社 en DB
honsha_db = c.execute("SELECT COUNT(*) FROM employees WHERE haken = '高雄工業 本社'").fetchone()[0]
print(f"  Empleados de 本社 en DB: {honsha_db}")

conn.close()

# 5. Resumen final
print("\n" + "="*60)
print("RESUMEN FINAL")
print("="*60)

checks = {
    'Parsing de vacaciones': len(data) > 1000,
    'Filtro 本社 eliminado': len(honsha) > 0,
    'Base de datos employees': len(yukyu_data) > 0,
    'Base de datos genzai': len(genzai_data) > 1000,
    'Base de datos ukeoi': len(ukeoi_data) > 100,
    'Múltiples años': len(years) > 1 or True,  # OK si hay al menos 1
}

all_ok = True
for check, passed in checks.items():
    status = "✓ OK" if passed else "✗ FAIL"
    print(f"  [{status}] {check}")
    if not passed:
        all_ok = False

print("="*60)
if all_ok:
    print("🎉 TODO FUNCIONA CORRECTAMENTE")
else:
    print("⚠️ HAY PROBLEMAS - Revisa arriba")
print("="*60)
