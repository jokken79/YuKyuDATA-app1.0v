#!/usr/bin/env python3
"""
GitHub Issues Integration Module for YuKyuDATA-app

Este modulo proporciona funciones para interactuar con GitHub Issues API,
incluyendo creacion, listado, cierre de issues y sincronizacion de TODOs.

Requiere:
    - GITHUB_TOKEN: Token de acceso personal de GitHub
    - GITHUB_REPO: Repositorio en formato owner/repo (ej: jokken79/YuKyuDATA-app1.0v)

Uso:
    from scripts.github_issues import GitHubIssues

    gh = GitHubIssues()
    gh.create_issue("Bug encontrado", "Descripcion del bug", labels=["bug"])
    issues = gh.list_issues(state='open')
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuracion de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO = "jokken79/YuKyuDATA-app1.0v"
MEMORY_STORE_PATH = Path(__file__).parent.parent / "agents" / "memory_store.json"


class GitHubIssuesError(Exception):
    """Excepcion base para errores de GitHub Issues"""
    pass


class GitHubAuthError(GitHubIssuesError):
    """Error de autenticacion con GitHub"""
    pass


class GitHubAPIError(GitHubIssuesError):
    """Error de la API de GitHub"""
    pass


class GitHubIssues:
    """
    Cliente para interactuar con GitHub Issues API.

    Attributes:
        token (str): Token de acceso personal de GitHub
        repo (str): Repositorio en formato owner/repo
        headers (dict): Headers para las peticiones HTTP
    """

    def __init__(self, token: Optional[str] = None, repo: Optional[str] = None):
        """
        Inicializa el cliente de GitHub Issues.

        Args:
            token: Token de GitHub (usa GITHUB_TOKEN de .env si no se proporciona)
            repo: Repositorio en formato owner/repo (usa GITHUB_REPO de .env si no se proporciona)

        Raises:
            GitHubAuthError: Si no se proporciona token
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO", DEFAULT_REPO)

        if not self.token:
            raise GitHubAuthError(
                "GITHUB_TOKEN no configurado. "
                "Agrega GITHUB_TOKEN a tu archivo .env o pasalo como parametro."
            )

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        self.base_url = f"{GITHUB_API_BASE}/repos/{self.repo}"
        logger.info(f"GitHubIssues inicializado para repositorio: {self.repo}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Realiza una peticion HTTP a la API de GitHub.

        Args:
            method: Metodo HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint de la API (sin la base URL)
            data: Datos para enviar en el body (JSON)
            params: Parametros de query string

        Returns:
            Respuesta de la API como diccionario

        Raises:
            GitHubAPIError: Si la peticion falla
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )

            # Verificar errores de autenticacion
            if response.status_code == 401:
                raise GitHubAuthError("Token de GitHub invalido o expirado")

            # Verificar rate limiting
            if response.status_code == 403:
                remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
                reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                raise GitHubAPIError(
                    f"Rate limit excedido. Remaining: {remaining}, Reset: {reset_time}"
                )

            # Verificar errores generales
            if response.status_code >= 400:
                error_msg = response.json().get("message", response.text)
                raise GitHubAPIError(f"Error de API ({response.status_code}): {error_msg}")

            # Retornar respuesta vacia para DELETE exitoso
            if response.status_code == 204:
                return {"status": "success"}

            return response.json()

        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Error de conexion: {str(e)}")

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo issue en GitHub.

        Args:
            title: Titulo del issue
            body: Descripcion/cuerpo del issue (soporta Markdown)
            labels: Lista de etiquetas (ej: ["bug", "enhancement"])
            assignees: Lista de usernames para asignar
            milestone: Numero del milestone

        Returns:
            Datos del issue creado incluyendo numero y URL

        Example:
            >>> gh = GitHubIssues()
            >>> issue = gh.create_issue(
            ...     "Bug en parser Excel",
            ...     "El parser no detecta medio dia correctamente",
            ...     labels=["bug", "parser"]
            ... )
            >>> print(f"Issue #{issue['number']} creado: {issue['html_url']}")
        """
        data = {
            "title": title,
            "body": body
        }

        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone

        result = self._make_request("POST", "issues", data=data)

        logger.info(f"Issue #{result['number']} creado: {title}")

        return {
            "number": result["number"],
            "title": result["title"],
            "html_url": result["html_url"],
            "state": result["state"],
            "created_at": result["created_at"],
            "labels": [l["name"] for l in result.get("labels", [])]
        }

    def list_issues(
        self,
        state: str = "open",
        labels: Optional[str] = None,
        sort: str = "created",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Lista issues del repositorio.

        Args:
            state: Estado de issues ('open', 'closed', 'all')
            labels: Filtrar por etiquetas separadas por coma (ej: "bug,enhancement")
            sort: Ordenar por ('created', 'updated', 'comments')
            direction: Direccion del orden ('asc', 'desc')
            per_page: Numero de resultados por pagina (max 100)
            page: Numero de pagina

        Returns:
            Lista de issues con sus datos principales

        Example:
            >>> gh = GitHubIssues()
            >>> open_bugs = gh.list_issues(state='open', labels='bug')
            >>> for issue in open_bugs:
            ...     print(f"#{issue['number']}: {issue['title']}")
        """
        params = {
            "state": state,
            "sort": sort,
            "direction": direction,
            "per_page": min(per_page, 100),
            "page": page
        }

        if labels:
            params["labels"] = labels

        results = self._make_request("GET", "issues", params=params)

        # Filtrar solo issues (no pull requests)
        issues = [
            {
                "number": issue["number"],
                "title": issue["title"],
                "body": issue.get("body", ""),
                "state": issue["state"],
                "html_url": issue["html_url"],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "labels": [l["name"] for l in issue.get("labels", [])],
                "assignees": [a["login"] for a in issue.get("assignees", [])],
                "comments": issue.get("comments", 0)
            }
            for issue in results
            if "pull_request" not in issue
        ]

        logger.info(f"Listados {len(issues)} issues (state={state})")

        return issues

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Obtiene los detalles de un issue especifico.

        Args:
            issue_number: Numero del issue

        Returns:
            Datos completos del issue
        """
        result = self._make_request("GET", f"issues/{issue_number}")

        return {
            "number": result["number"],
            "title": result["title"],
            "body": result.get("body", ""),
            "state": result["state"],
            "html_url": result["html_url"],
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
            "closed_at": result.get("closed_at"),
            "labels": [l["name"] for l in result.get("labels", [])],
            "assignees": [a["login"] for a in result.get("assignees", [])],
            "comments": result.get("comments", 0),
            "user": result["user"]["login"]
        }

    def close_issue(self, issue_number: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Cierra un issue existente.

        Args:
            issue_number: Numero del issue a cerrar
            reason: Razon del cierre ('completed' o 'not_planned')

        Returns:
            Datos del issue actualizado

        Example:
            >>> gh = GitHubIssues()
            >>> gh.close_issue(42, reason="completed")
        """
        data = {"state": "closed"}

        if reason:
            data["state_reason"] = reason

        result = self._make_request("PATCH", f"issues/{issue_number}", data=data)

        logger.info(f"Issue #{issue_number} cerrado")

        return {
            "number": result["number"],
            "title": result["title"],
            "state": result["state"],
            "closed_at": result.get("closed_at"),
            "html_url": result["html_url"]
        }

    def reopen_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Reabre un issue cerrado.

        Args:
            issue_number: Numero del issue a reabrir

        Returns:
            Datos del issue actualizado
        """
        data = {"state": "open"}
        result = self._make_request("PATCH", f"issues/{issue_number}", data=data)

        logger.info(f"Issue #{issue_number} reabierto")

        return {
            "number": result["number"],
            "title": result["title"],
            "state": result["state"],
            "html_url": result["html_url"]
        }

    def add_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """
        Agrega un comentario a un issue.

        Args:
            issue_number: Numero del issue
            comment: Texto del comentario (soporta Markdown)

        Returns:
            Datos del comentario creado

        Example:
            >>> gh = GitHubIssues()
            >>> gh.add_comment(42, "Este issue esta siendo trabajado en la rama `feature/fix-parser`")
        """
        data = {"body": comment}

        result = self._make_request("POST", f"issues/{issue_number}/comments", data=data)

        logger.info(f"Comentario agregado al issue #{issue_number}")

        return {
            "id": result["id"],
            "body": result["body"],
            "created_at": result["created_at"],
            "html_url": result["html_url"],
            "user": result["user"]["login"]
        }

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Actualiza un issue existente.

        Args:
            issue_number: Numero del issue
            title: Nuevo titulo (opcional)
            body: Nuevo cuerpo (opcional)
            labels: Nuevas etiquetas (opcional, reemplaza las existentes)
            assignees: Nuevos asignados (opcional, reemplaza los existentes)

        Returns:
            Datos del issue actualizado
        """
        data = {}

        if title is not None:
            data["title"] = title
        if body is not None:
            data["body"] = body
        if labels is not None:
            data["labels"] = labels
        if assignees is not None:
            data["assignees"] = assignees

        if not data:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")

        result = self._make_request("PATCH", f"issues/{issue_number}", data=data)

        logger.info(f"Issue #{issue_number} actualizado")

        return {
            "number": result["number"],
            "title": result["title"],
            "state": result["state"],
            "html_url": result["html_url"],
            "updated_at": result["updated_at"]
        }

    def add_labels(self, issue_number: int, labels: List[str]) -> List[str]:
        """
        Agrega etiquetas a un issue (sin eliminar las existentes).

        Args:
            issue_number: Numero del issue
            labels: Lista de etiquetas a agregar

        Returns:
            Lista de todas las etiquetas del issue
        """
        result = self._make_request(
            "POST",
            f"issues/{issue_number}/labels",
            data={"labels": labels}
        )

        return [l["name"] for l in result]

    def remove_label(self, issue_number: int, label: str) -> bool:
        """
        Elimina una etiqueta de un issue.

        Args:
            issue_number: Numero del issue
            label: Nombre de la etiqueta a eliminar

        Returns:
            True si se elimino correctamente
        """
        try:
            self._make_request("DELETE", f"issues/{issue_number}/labels/{label}")
            return True
        except GitHubAPIError:
            return False

    def search_issues(self, query: str, state: str = "open") -> List[Dict[str, Any]]:
        """
        Busca issues usando la API de busqueda de GitHub.

        Args:
            query: Termino de busqueda
            state: Estado de issues ('open', 'closed', 'all')

        Returns:
            Lista de issues que coinciden con la busqueda
        """
        # Construir query completo
        full_query = f"repo:{self.repo} is:issue state:{state} {query}"

        # Usar endpoint de busqueda
        url = f"{GITHUB_API_BASE}/search/issues"
        params = {"q": full_query, "per_page": 100}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()

            return [
                {
                    "number": item["number"],
                    "title": item["title"],
                    "state": item["state"],
                    "html_url": item["html_url"],
                    "labels": [l["name"] for l in item.get("labels", [])]
                }
                for item in results.get("items", [])
            ]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en busqueda: {e}")
            return []

    def issue_exists_by_title(self, title: str, state: str = "all") -> Optional[int]:
        """
        Verifica si existe un issue con el titulo dado.

        Args:
            title: Titulo exacto del issue
            state: Estado de issues a buscar

        Returns:
            Numero del issue si existe, None si no
        """
        # Buscar issues con titulo similar
        issues = self.search_issues(f'"{title}" in:title', state=state)

        # Verificar coincidencia exacta
        for issue in issues:
            if issue["title"].strip().lower() == title.strip().lower():
                return issue["number"]

        return None

    def sync_todos_to_issues(self, memory_store_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Sincroniza TODOs de memory_store.json a GitHub Issues.

        Args:
            memory_store_path: Ruta al archivo memory_store.json

        Returns:
            Resumen de la sincronizacion con issues creados y omitidos

        Example:
            >>> gh = GitHubIssues()
            >>> result = gh.sync_todos_to_issues()
            >>> print(f"Creados: {result['created']}, Omitidos: {result['skipped']}")
        """
        store_path = memory_store_path or MEMORY_STORE_PATH

        if not store_path.exists():
            logger.warning(f"Archivo no encontrado: {store_path}")
            return {
                "status": "error",
                "message": f"Archivo no encontrado: {store_path}",
                "created": [],
                "skipped": [],
                "errors": []
            }

        try:
            with open(store_path, 'r', encoding='utf-8') as f:
                memory = json.load(f)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Error parseando JSON: {e}",
                "created": [],
                "skipped": [],
                "errors": []
            }

        todos = memory.get("todos", {})
        errors = memory.get("errors", {})

        created = []
        skipped = []
        sync_errors = []

        # Sincronizar TODOs pendientes
        for todo_id, todo in todos.items():
            if todo.get("completed"):
                continue

            title = f"[TODO] {todo.get('title', 'Sin titulo')}"

            # Verificar si ya existe
            existing = self.issue_exists_by_title(title)
            if existing:
                skipped.append({
                    "todo_id": todo_id,
                    "title": title,
                    "reason": f"Ya existe como issue #{existing}"
                })
                continue

            # Crear el issue
            try:
                priority_label = f"priority:{todo.get('priority', 'medium')}"
                category_label = todo.get("category", "general")

                body = self._format_todo_body(todo)

                issue = self.create_issue(
                    title=title,
                    body=body,
                    labels=["todo", priority_label, category_label]
                )

                created.append({
                    "todo_id": todo_id,
                    "issue_number": issue["number"],
                    "title": title,
                    "url": issue["html_url"]
                })

            except GitHubAPIError as e:
                sync_errors.append({
                    "todo_id": todo_id,
                    "title": title,
                    "error": str(e)
                })

        # Sincronizar errores conocidos
        for error_id, error in errors.items():
            if error.get("verified"):
                continue

            title = f"[ERROR] {error.get('error_pattern', 'Error sin patron')}"

            # Verificar si ya existe
            existing = self.issue_exists_by_title(title)
            if existing:
                skipped.append({
                    "error_id": error_id,
                    "title": title,
                    "reason": f"Ya existe como issue #{existing}"
                })
                continue

            # Crear el issue
            try:
                body = self._format_error_body(error)

                issue = self.create_issue(
                    title=title,
                    body=body,
                    labels=["bug", "from-memory"]
                )

                created.append({
                    "error_id": error_id,
                    "issue_number": issue["number"],
                    "title": title,
                    "url": issue["html_url"]
                })

            except GitHubAPIError as e:
                sync_errors.append({
                    "error_id": error_id,
                    "title": title,
                    "error": str(e)
                })

        result = {
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "created": created,
            "skipped": skipped,
            "errors": sync_errors,
            "summary": {
                "total_todos": len([t for t in todos.values() if not t.get("completed")]),
                "total_errors": len([e for e in errors.values() if not e.get("verified")]),
                "created_count": len(created),
                "skipped_count": len(skipped),
                "error_count": len(sync_errors)
            }
        }

        logger.info(
            f"Sincronizacion completada: {len(created)} creados, "
            f"{len(skipped)} omitidos, {len(sync_errors)} errores"
        )

        return result

    def _format_todo_body(self, todo: Dict[str, Any]) -> str:
        """Formatea el cuerpo del issue para un TODO."""
        body = f"""## Descripcion
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
*Issue generado automaticamente por YuKyuDATA GitHub Integration*
"""
        return body

    def _format_error_body(self, error: Dict[str, Any]) -> str:
        """Formatea el cuerpo del issue para un error conocido."""
        files = error.get("related_files", [])
        files_str = "\n".join([f"- `{f}`" for f in files]) if files else "- No especificados"

        keywords = error.get("error_keywords", [])
        keywords_str = ", ".join([f"`{k}`" for k in keywords]) if keywords else "N/A"

        body = f"""## Patron del Error
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
| **Verificado** | {'Si' if error.get('verified') else 'No'} |

## Origen
- **ID interno**: `{error.get('error_id', 'N/A')}`
- **Fuente**: `memory_store.json`

---
*Issue generado automaticamente por YuKyuDATA GitHub Integration*
"""
        return body


# ============================================
# Funciones de conveniencia (API funcional)
# ============================================

def create_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Crea un nuevo issue en GitHub.

    Funcion de conveniencia que crea una instancia de GitHubIssues internamente.

    Args:
        title: Titulo del issue
        body: Descripcion del issue
        labels: Lista de etiquetas

    Returns:
        Datos del issue creado
    """
    gh = GitHubIssues()
    return gh.create_issue(title, body, labels)


def list_issues(state: str = "open") -> List[Dict[str, Any]]:
    """
    Lista issues del repositorio.

    Args:
        state: Estado de issues ('open', 'closed', 'all')

    Returns:
        Lista de issues
    """
    gh = GitHubIssues()
    return gh.list_issues(state=state)


def close_issue(issue_number: int) -> Dict[str, Any]:
    """
    Cierra un issue existente.

    Args:
        issue_number: Numero del issue

    Returns:
        Datos del issue cerrado
    """
    gh = GitHubIssues()
    return gh.close_issue(issue_number)


def add_comment(issue_number: int, comment: str) -> Dict[str, Any]:
    """
    Agrega un comentario a un issue.

    Args:
        issue_number: Numero del issue
        comment: Texto del comentario

    Returns:
        Datos del comentario creado
    """
    gh = GitHubIssues()
    return gh.add_comment(issue_number, comment)


def sync_todos_to_issues() -> Dict[str, Any]:
    """
    Sincroniza TODOs de memory_store.json a GitHub Issues.

    Returns:
        Resumen de la sincronizacion
    """
    gh = GitHubIssues()
    return gh.sync_todos_to_issues()


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub Issues Integration para YuKyuDATA-app"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando: list
    list_parser = subparsers.add_parser("list", help="Listar issues")
    list_parser.add_argument(
        "--state",
        choices=["open", "closed", "all"],
        default="open",
        help="Estado de issues a listar"
    )
    list_parser.add_argument(
        "--labels",
        help="Filtrar por etiquetas (separadas por coma)"
    )

    # Comando: create
    create_parser = subparsers.add_parser("create", help="Crear nuevo issue")
    create_parser.add_argument("title", help="Titulo del issue")
    create_parser.add_argument("--body", "-b", default="", help="Cuerpo del issue")
    create_parser.add_argument(
        "--labels", "-l",
        nargs="+",
        help="Etiquetas del issue"
    )

    # Comando: close
    close_parser = subparsers.add_parser("close", help="Cerrar un issue")
    close_parser.add_argument("number", type=int, help="Numero del issue")

    # Comando: comment
    comment_parser = subparsers.add_parser("comment", help="Agregar comentario")
    comment_parser.add_argument("number", type=int, help="Numero del issue")
    comment_parser.add_argument("text", help="Texto del comentario")

    # Comando: sync
    sync_parser = subparsers.add_parser("sync", help="Sincronizar TODOs a issues")

    args = parser.parse_args()

    try:
        gh = GitHubIssues()

        if args.command == "list":
            issues = gh.list_issues(state=args.state, labels=args.labels)
            print(f"\n{'='*60}")
            print(f"Issues ({args.state}): {len(issues)}")
            print(f"{'='*60}\n")

            for issue in issues:
                labels_str = ", ".join(issue["labels"]) if issue["labels"] else "sin etiquetas"
                print(f"#{issue['number']} - {issue['title']}")
                print(f"   Estado: {issue['state']} | Etiquetas: {labels_str}")
                print(f"   URL: {issue['html_url']}")
                print()

        elif args.command == "create":
            issue = gh.create_issue(args.title, args.body, args.labels)
            print(f"\nIssue creado exitosamente!")
            print(f"  Numero: #{issue['number']}")
            print(f"  Titulo: {issue['title']}")
            print(f"  URL: {issue['html_url']}")

        elif args.command == "close":
            result = gh.close_issue(args.number)
            print(f"\nIssue #{args.number} cerrado exitosamente")
            print(f"  Estado: {result['state']}")

        elif args.command == "comment":
            result = gh.add_comment(args.number, args.text)
            print(f"\nComentario agregado al issue #{args.number}")
            print(f"  URL: {result['html_url']}")

        elif args.command == "sync":
            result = gh.sync_todos_to_issues()
            print(f"\n{'='*60}")
            print("Sincronizacion completada")
            print(f"{'='*60}")
            print(f"\nResumen:")
            print(f"  TODOs pendientes: {result['summary']['total_todos']}")
            print(f"  Errores no verificados: {result['summary']['total_errors']}")
            print(f"  Issues creados: {result['summary']['created_count']}")
            print(f"  Omitidos (duplicados): {result['summary']['skipped_count']}")
            print(f"  Errores de sync: {result['summary']['error_count']}")

            if result['created']:
                print(f"\nIssues creados:")
                for item in result['created']:
                    print(f"  - #{item['issue_number']}: {item['title']}")

        else:
            parser.print_help()

    except GitHubAuthError as e:
        print(f"\nError de autenticacion: {e}")
        print("Asegurate de configurar GITHUB_TOKEN en tu archivo .env")
        exit(1)
    except GitHubAPIError as e:
        print(f"\nError de API: {e}")
        exit(1)
