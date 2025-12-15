"""
Test filtro de status
"""
import requests
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("TEST DE FILTRO DE STATUS")
print("=" * 60)

# Test Genzai
print("\n1. Genzai SIN filtro:")
try:
    r = requests.get("http://localhost:8000/api/genzai")
    data = r.json()
    print(f"   Total: {data['count']} empleados")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Genzai 在職中:")
try:
    r = requests.get("http://localhost:8000/api/genzai", params={"status": "在職中"})
    data = r.json()
    print(f"   Activos: {data['count']} empleados")
except Exception as e:
    print(f"   Error: {e}")

# Test Ukeoi
print("\n3. Ukeoi SIN filtro:")
try:
    r = requests.get("http://localhost:8000/api/ukeoi")
    data = r.json()
    print(f"   Total: {data['count']} empleados")
except Exception as e:
    print(f"   Error: {e}")

print("\n4. Ukeoi 在職中:")
try:
    r = requests.get("http://localhost:8000/api/ukeoi", params={"status": "在職中"})
    data = r.json()
    print(f"   Activos: {data['count']} empleados")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
