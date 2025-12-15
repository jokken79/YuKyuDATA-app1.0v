"""
Verificar campo status en Genzai y Ukeoi
"""
import sys
import sqlite3

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("VERIFICACIÓN DE CAMPO STATUS")
print("=" * 60)

conn = sqlite3.connect('yukyu.db')
c = conn.cursor()

# Genzai
print("\n1. GENZAI (派遣社員):")
print("-" * 60)
total_genzai = c.execute('SELECT COUNT(*) FROM genzai').fetchone()[0]
print(f"   Total registros: {total_genzai}")

# Ver diferentes status
statuses_genzai = c.execute('SELECT DISTINCT status FROM genzai').fetchall()
print(f"   Status únicos: {[s[0] for s in statuses_genzai]}")

# Contar por status
for status in statuses_genzai:
    count = c.execute('SELECT COUNT(*) FROM genzai WHERE status = ?', status).fetchone()[0]
    print(f"   {status[0]:20} {count:6} empleados")

# Ukeoi
print("\n2. UKEOI (請負社員):")
print("-" * 60)
total_ukeoi = c.execute('SELECT COUNT(*) FROM ukeoi').fetchone()[0]
print(f"   Total registros: {total_ukeoi}")

# Ver diferentes status
statuses_ukeoi = c.execute('SELECT DISTINCT status FROM ukeoi').fetchall()
print(f"   Status únicos: {[s[0] for s in statuses_ukeoi]}")

# Contar por status
for status in statuses_ukeoi:
    count = c.execute('SELECT COUNT(*) FROM ukeoi WHERE status = ?', status).fetchone()[0]
    print(f"   {status[0]:20} {count:6} empleados")

# Verificar si hay 在職中
print("\n3. EMPLEADOS ACTIVOS (在職中):")
print("-" * 60)
active_genzai = c.execute("SELECT COUNT(*) FROM genzai WHERE status = '在職中'").fetchone()[0]
active_ukeoi = c.execute("SELECT COUNT(*) FROM ukeoi WHERE status = '在職中'").fetchone()[0]

print(f"   Genzai 在職中: {active_genzai}")
print(f"   Ukeoi 在職中:  {active_ukeoi}")
print(f"   Total 在職中:  {active_genzai + active_ukeoi}")

conn.close()
print("\n" + "=" * 60)
