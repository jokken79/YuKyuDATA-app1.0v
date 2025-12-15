"""
Test filtro de status usando database.py
"""
import sys
import database

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("TEST DE FILTRO DE STATUS")
print("=" * 60)

# Test Genzai
print("\n1. Genzai SIN filtro:")
all_genzai = database.get_genzai()
print(f"   Total: {len(all_genzai)} empleados")

print("\n2. Genzai 在職中:")
active_genzai = database.get_genzai(status="在職中")
print(f"   Activos: {len(active_genzai)} empleados")

# Test Ukeoi
print("\n3. Ukeoi SIN filtro:")
all_ukeoi = database.get_ukeoi()
print(f"   Total: {len(all_ukeoi)} empleados")

print("\n4. Ukeoi 在職中:")
active_ukeoi = database.get_ukeoi(status="在職中")
print(f"   Activos: {len(active_ukeoi)} empleados")

print("\n" + "=" * 60)
print("RESUMEN:")
print("=" * 60)
print(f"Genzai total: {len(all_genzai)} | 在職中: {len(active_genzai)}")
print(f"Ukeoi total:  {len(all_ukeoi)} | 在職中: {len(active_ukeoi)}")
print(f"Total activos (在職中): {len(active_genzai) + len(active_ukeoi)}")
print("=" * 60)
