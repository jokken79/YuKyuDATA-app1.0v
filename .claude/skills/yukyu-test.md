---
name: yukyu-test
description: Ejecuta la suite de tests de YuKyuDATA con cobertura
version: 1.0.0
---

# /yukyu-test - Ejecutar Tests

Ejecuta la suite completa de tests de YuKyuDATA.

## Comando Principal

```bash
pytest tests/ -v --ignore=tests/test_connection_pooling.py
```

## Opciones

### Tests específicos
```bash
# Solo auth
pytest tests/test_auth.py -v

# Solo fiscal year (críticos)
pytest tests/test_fiscal_year.py -v

# Solo LIFO
pytest tests/test_lifo_deduction.py -v
```

### Con cobertura
```bash
pytest tests/ --cov=. --cov-report=html --ignore=tests/test_connection_pooling.py
```

### Tests rápidos (sin lentos)
```bash
pytest tests/ -v -m "not slow" --ignore=tests/test_connection_pooling.py
```

## Variables de Entorno Requeridas

```bash
TESTING=true
DEBUG=true
RATE_LIMIT_ENABLED=false
```

## Tests Críticos

Estos tests DEBEN pasar siempre:

1. `test_fiscal_year.py` - Lógica de ley laboral japonesa
2. `test_lifo_deduction.py` - Deducción LIFO correcta
3. `test_auth.py` - Autenticación JWT

## Resultado Esperado

```
tests/test_auth.py::TestAuthentication::test_login_success PASSED
tests/test_auth.py::TestAuthentication::test_login_invalid_password PASSED
...
==================== X passed, Y warnings in Z.XXs ====================
```
