#!/usr/bin/env python3
"""
Script CLI para sincronizar TODOs y errores a GitHub Issues.

Este script lee el archivo memory_store.json y crea issues en GitHub
para TODOs pendientes y errores conocidos no verificados.

Uso:
    python scripts/sync-issues.py                    # Sincronizar todo
    python scripts/sync-issues.py --dry-run          # Ver que se crearia sin crear
    python scripts/sync-issues.py --todos-only       # Solo sincronizar TODOs
    python scripts/sync-issues.py --errors-only      # Solo sincronizar errores

Requisitos:
    - GITHUB_TOKEN configurado en .env
    - GITHUB_REPO configurado en .env (opcional, default: jokken79/YuKyuDATA-app1.0v)

Autor: YuKyuDATA-app Team
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Agregar el directorio raiz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(ROOT_DIR / ".env")

# Colores para output en terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Imprime un encabezado formateado."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Imprime mensaje de exito."""
    print(f"{Colors.GREEN}[OK] {text}{Colors.ENDC}")


def print_warning(text: str):
    """Imprime mensaje de advertencia."""
    print(f"{Colors.YELLOW}[!] {text}{Colors.ENDC}")


def print_error(text: str):
    """Imprime mensaje de error."""
    print(f"{Colors.RED}[ERROR] {text}{Colors.ENDC}")


def print_info(text: str):
    """Imprime mensaje informativo."""
    print(f"{Colors.CYAN}[INFO] {text}{Colors.ENDC}")


def load_memory_store() -> dict:
    """Carga el archivo memory_store.json."""
    memory_path = ROOT_DIR / "agents" / "memory_store.json"

    if not memory_path.exists():
        print_error(f"Archivo no encontrado: {memory_path}")
        sys.exit(1)

    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"Error parseando JSON: {e}")
        sys.exit(1)


def get_pending_todos(memory: dict) -> list:
    """Obtiene TODOs pendientes (no completados)."""
    todos = memory.get("todos", {})
    return [
        {**todo, "todo_id": todo_id}
        for todo_id, todo in todos.items()
        if not todo.get("completed")
    ]


def get_unverified_errors(memory: dict) -> list:
    """Obtiene errores no verificados."""
    errors = memory.get("errors", {})
    return [
        {**error}
        for error_id, error in errors.items()
        if not error.get("verified")
    ]


def format_todo_body(todo: dict) -> str:
    """Formatea el cuerpo del issue para un TODO."""
    return f"""## Descripcion
{todo.get('description', 'Sin descripcion')}

## Detalles
| Campo | Valor |
|-------|-------|
| **Prioridad** | {todo.get('priority', 'medium')} |
| **Categoria** | {todo.get('category', 'general')} |
| **Creado** | {todo.get('created_at', 'N/A')} |
| **Fecha limite** | {todo.get('due_date', 'No especificada')} |

## Origen
- **ID interno**: `{todo.get('todo_id', 'N/A')}`
- **Fuente**: `memory_store.json`

---
*Issue generado automaticamente por YuKyuDATA GitHub Sync*
"""


def format_error_body(error: dict) -> str:
    """Formatea el cuerpo del issue para un error."""
    files = error.get("related_files", [])
    files_str = "\n".join([f"- `{f}`" for f in files]) if files else "- No especificados"

    keywords = error.get("error_keywords", [])
    keywords_str = ", ".join([f"`{k}`" for k in keywords]) if keywords else "N/A"

    return f"""## Patron del Error
```
{error.get('error_pattern', 'No especificado')}
```

## Solucion Conocida
{error.get('solution', 'No hay solucion documentada')}

### Detalles de la Solucion
{error.get('solution_details', 'Sin detalles adicionales')}

## Archivos Relacionados
{files_str}

## Metadatos
| Campo | Valor |
|-------|-------|
| **Keywords** | {keywords_str} |
| **Veces usado** | {error.get('times_used', 0)} |
| **Ultimo uso** | {error.get('last_used', 'Nunca')} |

## Origen
- **ID interno**: `{error.get('error_id', 'N/A')}`
- **Fuente**: `memory_store.json`

---
*Issue generado automaticamente por YuKyuDATA GitHub Sync*
"""


def sync_to_github(
    todos: list,
    errors: list,
    dry_run: bool = False
) -> dict:
    """
    Sincroniza TODOs y errores a GitHub Issues.

    Args:
        todos: Lista de TODOs pendientes
        errors: Lista de errores no verificados
        dry_run: Si es True, solo muestra que se crearia

    Returns:
        Resumen de la sincronizacion
    """
    from scripts.github_issues import GitHubIssues, GitHubAuthError, GitHubAPIError

    results = {
        "created": [],
        "skipped": [],
        "errors": []
    }

    try:
        gh = GitHubIssues()
    except GitHubAuthError as e:
        print_error(str(e))
        return results

    # Sincronizar TODOs
    for todo in todos:
        title = f"[TODO] {todo.get('title', 'Sin titulo')}"

        # Verificar si ya existe
        if not dry_run:
            existing = gh.issue_exists_by_title(title)
            if existing:
                print_warning(f"Ya existe: {title} (Issue #{existing})")
                results["skipped"].append({
                    "title": title,
                    "reason": f"Duplicado de #{existing}"
                })
                continue

        # Preparar datos
        priority = todo.get("priority", "medium")
        category = todo.get("category", "general")
        labels = ["todo", f"priority:{priority}", category]
        body = format_todo_body(todo)

        if dry_run:
            print_info(f"[DRY-RUN] Crearia: {title}")
            print(f"          Labels: {', '.join(labels)}")
            results["created"].append({"title": title, "labels": labels})
        else:
            try:
                issue = gh.create_issue(title=title, body=body, labels=labels)
                print_success(f"Creado: #{issue['number']} - {title}")
                results["created"].append({
                    "title": title,
                    "number": issue["number"],
                    "url": issue["html_url"]
                })
            except GitHubAPIError as e:
                print_error(f"Error creando {title}: {e}")
                results["errors"].append({"title": title, "error": str(e)})

    # Sincronizar errores
    for error in errors:
        title = f"[ERROR] {error.get('error_pattern', 'Error sin patron')}"

        # Verificar si ya existe
        if not dry_run:
            existing = gh.issue_exists_by_title(title)
            if existing:
                print_warning(f"Ya existe: {title} (Issue #{existing})")
                results["skipped"].append({
                    "title": title,
                    "reason": f"Duplicado de #{existing}"
                })
                continue

        # Preparar datos
        labels = ["bug", "from-memory"]
        body = format_error_body(error)

        if dry_run:
            print_info(f"[DRY-RUN] Crearia: {title}")
            print(f"          Labels: {', '.join(labels)}")
            results["created"].append({"title": title, "labels": labels})
        else:
            try:
                issue = gh.create_issue(title=title, body=body, labels=labels)
                print_success(f"Creado: #{issue['number']} - {title}")
                results["created"].append({
                    "title": title,
                    "number": issue["number"],
                    "url": issue["html_url"]
                })
            except GitHubAPIError as e:
                print_error(f"Error creando {title}: {e}")
                results["errors"].append({"title": title, "error": str(e)})

    return results


def main():
    """Punto de entrada principal del script."""
    parser = argparse.ArgumentParser(
        description="Sincroniza TODOs y errores de memory_store.json a GitHub Issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/sync-issues.py                    # Sincronizar todo
  python scripts/sync-issues.py --dry-run          # Ver que se crearia sin crear
  python scripts/sync-issues.py --todos-only       # Solo sincronizar TODOs
  python scripts/sync-issues.py --errors-only      # Solo sincronizar errores
  python scripts/sync-issues.py --verbose          # Modo detallado

Configuracion:
  Asegurate de tener GITHUB_TOKEN configurado en tu archivo .env
  GITHUB_REPO es opcional (default: jokken79/YuKyuDATA-app1.0v)
"""
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar que se crearia sin crear issues reales"
    )

    parser.add_argument(
        "--todos-only",
        action="store_true",
        help="Solo sincronizar TODOs (ignorar errores)"
    )

    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Solo sincronizar errores (ignorar TODOs)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo detallado con mas informacion"
    )

    args = parser.parse_args()

    # Verificar configuracion
    if not os.getenv("GITHUB_TOKEN"):
        print_error("GITHUB_TOKEN no configurado en .env")
        print_info("Genera un token en: https://github.com/settings/tokens")
        print_info("Agrega a .env: GITHUB_TOKEN=ghp_tu_token_aqui")
        sys.exit(1)

    print_header("YuKyuDATA GitHub Issues Sync")

    repo = os.getenv("GITHUB_REPO", "jokken79/YuKyuDATA-app1.0v")
    print_info(f"Repositorio: {repo}")

    if args.dry_run:
        print_warning("Modo DRY-RUN: No se crearan issues reales")

    # Cargar datos
    print_info("Cargando memory_store.json...")
    memory = load_memory_store()

    # Obtener items a sincronizar
    todos = [] if args.errors_only else get_pending_todos(memory)
    errors = [] if args.todos_only else get_unverified_errors(memory)

    print_info(f"TODOs pendientes: {len(todos)}")
    print_info(f"Errores no verificados: {len(errors)}")

    if not todos and not errors:
        print_warning("No hay items para sincronizar")
        return

    # Mostrar detalles en modo verbose
    if args.verbose:
        print("\n--- TODOs ---")
        for todo in todos:
            print(f"  - [{todo.get('priority', 'medium')}] {todo.get('title')}")

        print("\n--- Errores ---")
        for error in errors:
            print(f"  - {error.get('error_pattern')}")

    # Ejecutar sincronizacion
    print("\n")
    results = sync_to_github(todos, errors, dry_run=args.dry_run)

    # Resumen final
    print_header("Resumen")

    created = len(results["created"])
    skipped = len(results["skipped"])
    error_count = len(results["errors"])

    if args.dry_run:
        print_info(f"Issues que se crearian: {created}")
    else:
        print_success(f"Issues creados: {created}")

    if skipped:
        print_warning(f"Omitidos (duplicados): {skipped}")

    if error_count:
        print_error(f"Errores: {error_count}")

    # Listar URLs de issues creados
    if not args.dry_run and results["created"]:
        print("\n--- Issues creados ---")
        for item in results["created"]:
            if "url" in item:
                print(f"  #{item['number']}: {item['url']}")

    print()


if __name__ == "__main__":
    main()
