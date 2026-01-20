"""
Memory Agent - Sistema de Memoria Persistente para Sesiones de Claude
=====================================================================

Proporciona persistencia de datos entre sesiones de Claude Code:
- Contexto de sesiones pasadas
- Aprendizajes por categoría (architecture, patterns, conventions)
- Errores conocidos y soluciones
- Historial de features implementadas
- Preferencias del usuario
- TODOs pendientes entre sesiones
- Sincronización con CLAUDE_MEMORY.md

Uso:
----
```python
from agents.memory import MemoryAgent

memory = MemoryAgent()
memory.add_learning('architecture', 'db_pattern', 'Usar INSERT OR REPLACE')
memory.add_error_solution('Celdas con comentarios', 'Usar data_only=False o editar manualmente')
memory.save_session_context('session_123', {'task': 'Implementar feature X'})
```
"""

import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib


logger = logging.getLogger(__name__)


class LearningCategory(Enum):
    """Categorias de aprendizajes."""
    ARCHITECTURE = "architecture"
    PATTERNS = "patterns"
    CONVENTIONS = "conventions"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTING = "testing"
    UI_UX = "ui_ux"
    DATABASE = "database"
    API = "api"
    BUSINESS_LOGIC = "business_logic"


class FeatureStatus(Enum):
    """Estados de features."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DEPRECATED = "deprecated"


class TodoPriority(Enum):
    """Prioridades de TODOs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SessionContext:
    """Contexto de una sesion."""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    branch_name: Optional[str] = None
    task_description: Optional[str] = None
    files_modified: List[str] = field(default_factory=list)
    commits: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Learning:
    """Un aprendizaje registrado."""
    key: str
    value: str
    category: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source_session: Optional[str] = None
    confidence: float = 1.0  # 0.0 a 1.0
    tags: List[str] = field(default_factory=list)


@dataclass
class ErrorSolution:
    """Un error conocido y su solucion."""
    error_id: str
    error_pattern: str
    error_keywords: List[str]
    solution: str
    solution_details: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    times_used: int = 0
    last_used: Optional[str] = None
    verified: bool = False


@dataclass
class FeatureRecord:
    """Registro de una feature implementada."""
    feature_name: str
    version: str
    status: str
    description: str
    implementation_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    endpoints: List[str] = field(default_factory=list)
    files_affected: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    notes: Optional[str] = None
    related_features: List[str] = field(default_factory=list)


@dataclass
class TodoItem:
    """Un TODO pendiente."""
    todo_id: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    completed: bool = False
    completed_at: Optional[str] = None
    source_session: Optional[str] = None


@dataclass
class UserPreference:
    """Preferencia del usuario."""
    key: str
    value: Any
    category: str = "general"
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class MemoryAgent:
    """
    Agente de Memoria Persistente para YuKyuDATA-app.

    Gestiona la persistencia de:
    - Contexto de sesiones
    - Aprendizajes del proyecto
    - Errores y soluciones
    - Historial de features
    - Preferencias del usuario
    - TODOs pendientes
    """

    # Default cleanup configuration
    DEFAULT_SESSION_MAX_AGE_DAYS = 30
    DEFAULT_TODO_MAX_AGE_DAYS = 90
    DEFAULT_ERROR_MAX_AGE_DAYS = 180
    DEFAULT_SESSION_KEEP_MINIMUM = 5

    def __init__(
        self,
        storage_path: Optional[str] = None,
        claude_memory_path: Optional[str] = None,
        auto_cleanup: bool = False,
        cleanup_on_load: bool = False
    ):
        """
        Inicializa el agente de memoria.

        Args:
            storage_path: Ruta al archivo JSON de almacenamiento.
                         Por defecto: agents/memory_store.json
            claude_memory_path: Ruta a CLAUDE_MEMORY.md.
                               Por defecto: CLAUDE_MEMORY.md en raiz del proyecto
            auto_cleanup: Si True, ejecuta cleanup automático al guardar
            cleanup_on_load: Si True, ejecuta cleanup al cargar datos existentes
        """
        # Determinar rutas
        self.base_dir = Path(__file__).parent.parent
        self.auto_cleanup = auto_cleanup

        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).parent / "memory_store.json"

        if claude_memory_path:
            self.claude_memory_path = Path(claude_memory_path)
        else:
            self.claude_memory_path = self.base_dir / "CLAUDE_MEMORY.md"

        # Estructura de datos en memoria
        self.data: Dict[str, Any] = {
            "sessions": {},
            "learnings": {},
            "errors": {},
            "features": [],
            "preferences": {},
            "todos": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_sessions": 0
            }
        }

        # Cargar datos existentes
        self._load()

        # Cleanup al cargar si está habilitado
        if cleanup_on_load:
            logger.info("Ejecutando cleanup automático al cargar...")
            self.run_full_cleanup()

        logger.info(f"MemoryAgent inicializado. Storage: {self.storage_path} (auto_cleanup={auto_cleanup})")

    # =========================================================================
    # PERSISTENCIA
    # =========================================================================

    def _load(self) -> None:
        """Carga datos desde el archivo JSON."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Merge con estructura por defecto para manejar nuevas claves
                    for key in self.data:
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
                logger.info(f"Datos cargados desde {self.storage_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Error al parsear JSON: {e}")
                # Backup del archivo corrupto
                backup_path = self.storage_path.with_suffix('.json.bak')
                if self.storage_path.exists():
                    os.rename(self.storage_path, backup_path)
                    logger.warning(f"Archivo corrupto movido a {backup_path}")
            except Exception as e:
                logger.error(f"Error al cargar memoria: {e}")

    def _save(self) -> bool:
        """
        Guarda datos al archivo JSON.

        Returns:
            True si se guardo correctamente, False en caso contrario.
        """
        try:
            self.data["metadata"]["last_updated"] = datetime.now().isoformat()

            # Crear directorio si no existe
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Escribir con formato legible
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)

            logger.debug(f"Datos guardados en {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar memoria: {e}")
            return False

    def _generate_id(self, prefix: str, content: str) -> str:
        """Genera un ID unico basado en contenido."""
        hash_input = f"{prefix}_{content}_{datetime.now().isoformat()}"
        return f"{prefix}_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"

    # =========================================================================
    # SESIONES
    # =========================================================================

    def save_session_context(self, session_id: str, context_dict: Dict[str, Any]) -> bool:
        """
        Guarda el contexto de una sesion.

        Args:
            session_id: Identificador unico de la sesion
            context_dict: Diccionario con el contexto de la sesion
                         Claves esperadas: task_description, branch_name, notes, etc.

        Returns:
            True si se guardo correctamente.

        Example:
            >>> memory.save_session_context('session_abc123', {
            ...     'task_description': 'Implementar feature de edicion',
            ...     'branch_name': 'claude/edit-feature-abc123',
            ...     'files_modified': ['main.py', 'app.js'],
            ...     'notes': ['Usar patron INSERT OR REPLACE']
            ... })
        """
        try:
            # Verificar si ya existe
            existing = self.data["sessions"].get(session_id, {})

            session_context = {
                "session_id": session_id,
                "start_time": existing.get("start_time", datetime.now().isoformat()),
                "end_time": context_dict.get("end_time"),
                "branch_name": context_dict.get("branch_name"),
                "task_description": context_dict.get("task_description"),
                "files_modified": context_dict.get("files_modified", []),
                "commits": context_dict.get("commits", []),
                "notes": context_dict.get("notes", []),
                "metadata": context_dict.get("metadata", {})
            }

            # Merge si ya existe
            if existing:
                # Append a listas existentes
                if "files_modified" in existing:
                    session_context["files_modified"] = list(set(
                        existing["files_modified"] + session_context["files_modified"]
                    ))
                if "commits" in existing:
                    session_context["commits"] = existing["commits"] + [
                        c for c in session_context["commits"] if c not in existing["commits"]
                    ]
                if "notes" in existing:
                    session_context["notes"] = existing["notes"] + [
                        n for n in session_context["notes"] if n not in existing["notes"]
                    ]

            self.data["sessions"][session_id] = session_context
            self.data["metadata"]["total_sessions"] = len(self.data["sessions"])

            self._save()
            logger.info(f"Contexto de sesion guardado: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar contexto de sesion: {e}")
            return False

    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera el contexto de una sesion.

        Args:
            session_id: Identificador de la sesion

        Returns:
            Diccionario con el contexto o None si no existe.
        """
        return self.data["sessions"].get(session_id)

    def get_all_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene las sesiones mas recientes.

        Args:
            limit: Numero maximo de sesiones a retornar

        Returns:
            Lista de sesiones ordenadas por fecha (mas reciente primero).
        """
        sessions = list(self.data["sessions"].values())
        sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        return sessions[:limit]

    def end_session(self, session_id: str, summary: Optional[str] = None) -> bool:
        """
        Marca una sesion como finalizada.

        Args:
            session_id: Identificador de la sesion
            summary: Resumen opcional de la sesion

        Returns:
            True si se actualizo correctamente.
        """
        if session_id in self.data["sessions"]:
            self.data["sessions"][session_id]["end_time"] = datetime.now().isoformat()
            if summary:
                self.data["sessions"][session_id].setdefault("notes", []).append(
                    f"[RESUMEN] {summary}"
                )
            self._save()
            return True
        return False

    # =========================================================================
    # APRENDIZAJES
    # =========================================================================

    def add_learning(
        self,
        category: str,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
        source_session: Optional[str] = None,
        confidence: float = 1.0
    ) -> bool:
        """
        Agrega un aprendizaje.

        Args:
            category: Categoria del aprendizaje (architecture, patterns, conventions, etc.)
            key: Clave identificadora del aprendizaje
            value: Valor/descripcion del aprendizaje
            tags: Etiquetas opcionales para busqueda
            source_session: ID de la sesion donde se aprendio
            confidence: Nivel de confianza (0.0 a 1.0)

        Returns:
            True si se agrego correctamente.

        Example:
            >>> memory.add_learning(
            ...     'architecture',
            ...     'db_pattern',
            ...     'Usar INSERT OR REPLACE para sincronizacion idempotente',
            ...     tags=['database', 'sqlite', 'crud']
            ... )
        """
        try:
            # Normalizar categoria
            category = category.lower().replace(" ", "_")

            # Crear estructura de categoria si no existe
            if category not in self.data["learnings"]:
                self.data["learnings"][category] = {}

            learning = {
                "key": key,
                "value": value,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "source_session": source_session,
                "confidence": max(0.0, min(1.0, confidence)),
                "tags": tags or []
            }

            # Si ya existe, actualizar manteniendo created_at
            if key in self.data["learnings"][category]:
                learning["created_at"] = self.data["learnings"][category][key].get(
                    "created_at", learning["created_at"]
                )

            self.data["learnings"][category][key] = learning
            self._save()

            logger.info(f"Aprendizaje agregado: [{category}] {key}")
            return True
        except Exception as e:
            logger.error(f"Error al agregar aprendizaje: {e}")
            return False

    def get_learnings(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene aprendizajes por categoria.

        Args:
            category: Categoria a filtrar. Si es None, retorna todos.

        Returns:
            Diccionario con los aprendizajes.
        """
        if category:
            category = category.lower().replace(" ", "_")
            return self.data["learnings"].get(category, {})
        return self.data["learnings"]

    def search_learnings(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Busca aprendizajes por texto.

        Args:
            query: Texto a buscar en claves, valores y tags
            category: Categoria opcional para filtrar

        Returns:
            Lista de aprendizajes que coinciden.
        """
        results = []
        query_lower = query.lower()

        categories_to_search = (
            [category.lower().replace(" ", "_")] if category
            else self.data["learnings"].keys()
        )

        for cat in categories_to_search:
            if cat not in self.data["learnings"]:
                continue
            for key, learning in self.data["learnings"][cat].items():
                # Buscar en key, value y tags
                if (query_lower in key.lower() or
                    query_lower in learning.get("value", "").lower() or
                    any(query_lower in tag.lower() for tag in learning.get("tags", []))):
                    results.append(learning)

        return results

    # =========================================================================
    # ERRORES Y SOLUCIONES
    # =========================================================================

    def add_error_solution(
        self,
        error_pattern: str,
        solution: str,
        solution_details: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        related_files: Optional[List[str]] = None
    ) -> str:
        """
        Registra un error y su solucion.

        Args:
            error_pattern: Patron o descripcion del error
            solution: Solucion al error
            solution_details: Detalles adicionales de la solucion
            keywords: Palabras clave para busqueda
            related_files: Archivos relacionados con el error

        Returns:
            ID del error registrado.

        Example:
            >>> memory.add_error_solution(
            ...     'Celdas con comentarios no se parsean',
            ...     'Usar data_only=False o sistema de edicion manual v2.1',
            ...     keywords=['excel', 'openpyxl', 'comments'],
            ...     related_files=['excel_service.py']
            ... )
        """
        try:
            error_id = self._generate_id("err", error_pattern)

            # Extraer keywords automaticamente si no se proporcionan
            if not keywords:
                keywords = self._extract_keywords(error_pattern)

            error_record = {
                "error_id": error_id,
                "error_pattern": error_pattern,
                "error_keywords": keywords,
                "solution": solution,
                "solution_details": solution_details,
                "related_files": related_files or [],
                "created_at": datetime.now().isoformat(),
                "times_used": 0,
                "last_used": None,
                "verified": False
            }

            self.data["errors"][error_id] = error_record
            self._save()

            logger.info(f"Error/solucion registrado: {error_id}")
            return error_id
        except Exception as e:
            logger.error(f"Error al registrar solucion: {e}")
            return ""

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrae palabras clave de un texto."""
        # Palabras comunes a ignorar
        stop_words = {
            'el', 'la', 'los', 'las', 'un', 'una', 'de', 'en', 'con', 'para',
            'por', 'que', 'se', 'no', 'es', 'al', 'del', 'a', 'y', 'o',
            'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has'
        }

        # Extraer palabras
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

        # Retornar unicos
        return list(set(keywords))[:10]

    def find_error_solution(self, error_message: str) -> List[Dict[str, Any]]:
        """
        Busca soluciones para un mensaje de error.

        Args:
            error_message: Mensaje de error a buscar

        Returns:
            Lista de soluciones ordenadas por relevancia.
        """
        results = []
        error_keywords = set(self._extract_keywords(error_message))

        for error_id, error_data in self.data["errors"].items():
            stored_keywords = set(error_data.get("error_keywords", []))
            pattern = error_data.get("error_pattern", "").lower()

            # Calcular score de relevancia
            keyword_match = len(error_keywords & stored_keywords)
            pattern_match = sum(1 for kw in error_keywords if kw in pattern)

            score = keyword_match * 2 + pattern_match

            if score > 0:
                results.append({
                    **error_data,
                    "_relevance_score": score
                })

        # Ordenar por relevancia y times_used
        results.sort(key=lambda x: (x["_relevance_score"], x.get("times_used", 0)), reverse=True)

        # Actualizar estadisticas del primer resultado
        if results:
            best_match_id = results[0]["error_id"]
            self.data["errors"][best_match_id]["times_used"] += 1
            self.data["errors"][best_match_id]["last_used"] = datetime.now().isoformat()
            self._save()

        return results

    def get_all_errors(self) -> List[Dict[str, Any]]:
        """Obtiene todos los errores registrados."""
        return list(self.data["errors"].values())

    def verify_error_solution(self, error_id: str, verified: bool = True) -> bool:
        """Marca una solucion como verificada."""
        if error_id in self.data["errors"]:
            self.data["errors"][error_id]["verified"] = verified
            self._save()
            return True
        return False

    # =========================================================================
    # FEATURES
    # =========================================================================

    def add_feature_history(
        self,
        feature_name: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Registra una feature implementada.

        Args:
            feature_name: Nombre de la feature
            details: Detalles de la feature
                - version: Version donde se implemento
                - description: Descripcion de la feature
                - status: planned/in_progress/completed/deprecated
                - endpoints: Lista de endpoints nuevos
                - files_affected: Archivos modificados
                - breaking_changes: Si tiene breaking changes
                - notes: Notas adicionales

        Returns:
            True si se registro correctamente.

        Example:
            >>> memory.add_feature_history('edit_excel', {
            ...     'version': '2.1',
            ...     'description': 'CRUD completo para yukyu_usage_details',
            ...     'status': 'completed',
            ...     'endpoints': ['/api/yukyu/usage-details'],
            ...     'files_affected': ['main.py', 'database.py']
            ... })
        """
        try:
            feature_record = {
                "feature_name": feature_name,
                "version": details.get("version", "0.0.0"),
                "status": details.get("status", "completed"),
                "description": details.get("description", ""),
                "implementation_date": details.get("date", datetime.now().strftime("%Y-%m-%d")),
                "endpoints": details.get("endpoints", []),
                "files_affected": details.get("files_affected", []),
                "breaking_changes": details.get("breaking_changes", False),
                "notes": details.get("notes"),
                "related_features": details.get("related_features", [])
            }

            # Verificar si ya existe para actualizar
            existing_idx = None
            for idx, f in enumerate(self.data["features"]):
                if f["feature_name"] == feature_name:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                self.data["features"][existing_idx] = feature_record
            else:
                self.data["features"].append(feature_record)

            self._save()
            logger.info(f"Feature registrada: {feature_name}")
            return True
        except Exception as e:
            logger.error(f"Error al registrar feature: {e}")
            return False

    def get_feature_history(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de features.

        Args:
            status: Filtrar por status (completed, in_progress, etc.)

        Returns:
            Lista de features ordenadas por fecha.
        """
        features = self.data["features"]

        if status:
            features = [f for f in features if f.get("status") == status]

        # Ordenar por fecha descendente
        features.sort(key=lambda x: x.get("implementation_date", ""), reverse=True)
        return features

    def get_feature_by_name(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene una feature por su nombre."""
        for feature in self.data["features"]:
            if feature["feature_name"] == feature_name:
                return feature
        return None

    # =========================================================================
    # PREFERENCIAS DEL USUARIO
    # =========================================================================

    def add_user_preference(
        self,
        key: str,
        value: Any,
        category: str = "general"
    ) -> bool:
        """
        Guarda una preferencia del usuario.

        Args:
            key: Clave de la preferencia
            value: Valor de la preferencia
            category: Categoria (general, communication, ui, workflow)

        Returns:
            True si se guardo correctamente.

        Example:
            >>> memory.add_user_preference('language', 'castellano', 'communication')
            >>> memory.add_user_preference('prefer_visual_explanations', True, 'communication')
        """
        try:
            preference = {
                "key": key,
                "value": value,
                "category": category,
                "updated_at": datetime.now().isoformat()
            }

            self.data["preferences"][key] = preference
            self._save()

            logger.info(f"Preferencia guardada: {key}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar preferencia: {e}")
            return False

    def get_user_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene las preferencias del usuario.

        Args:
            category: Filtrar por categoria

        Returns:
            Diccionario con las preferencias.
        """
        if category:
            return {
                k: v for k, v in self.data["preferences"].items()
                if v.get("category") == category
            }
        return self.data["preferences"]

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Obtiene una preferencia especifica.

        Args:
            key: Clave de la preferencia
            default: Valor por defecto si no existe

        Returns:
            Valor de la preferencia o default.
        """
        pref = self.data["preferences"].get(key)
        if pref:
            return pref.get("value", default)
        return default

    # =========================================================================
    # TODOs
    # =========================================================================

    def add_todo(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        due_date: Optional[str] = None,
        source_session: Optional[str] = None
    ) -> str:
        """
        Agrega un TODO pendiente.

        Args:
            title: Titulo del TODO
            description: Descripcion detallada
            priority: Prioridad (low, medium, high, critical)
            category: Categoria del TODO
            due_date: Fecha limite (YYYY-MM-DD)
            source_session: ID de la sesion origen

        Returns:
            ID del TODO creado.

        Example:
            >>> memory.add_todo(
            ...     'Mejorar parser de Excel',
            ...     'Detectar medio dia automaticamente',
            ...     priority='high',
            ...     category='parser'
            ... )
        """
        try:
            todo_id = self._generate_id("todo", title)

            todo = {
                "todo_id": todo_id,
                "title": title,
                "description": description,
                "priority": priority,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "due_date": due_date,
                "completed": False,
                "completed_at": None,
                "source_session": source_session
            }

            self.data["todos"][todo_id] = todo
            self._save()

            logger.info(f"TODO agregado: {todo_id} - {title}")
            return todo_id
        except Exception as e:
            logger.error(f"Error al agregar TODO: {e}")
            return ""

    def get_todos(self, completed: Optional[bool] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Obtiene TODOs filtrados.

        Args:
            completed: Filtrar por estado de completado
            category: Filtrar por categoria

        Returns:
            Lista de TODOs.
        """
        todos = list(self.data["todos"].values())

        if completed is not None:
            todos = [t for t in todos if t.get("completed") == completed]

        if category:
            todos = [t for t in todos if t.get("category") == category]

        # Ordenar por prioridad y fecha
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        todos.sort(key=lambda x: (
            priority_order.get(x.get("priority", "medium"), 2),
            x.get("created_at", "")
        ))

        return todos

    def complete_todo(self, todo_id: str) -> bool:
        """Marca un TODO como completado."""
        if todo_id in self.data["todos"]:
            self.data["todos"][todo_id]["completed"] = True
            self.data["todos"][todo_id]["completed_at"] = datetime.now().isoformat()
            self._save()
            return True
        return False

    def delete_todo(self, todo_id: str) -> bool:
        """Elimina un TODO."""
        if todo_id in self.data["todos"]:
            del self.data["todos"][todo_id]
            self._save()
            return True
        return False

    # =========================================================================
    # SINCRONIZACION CON CLAUDE_MEMORY.md
    # =========================================================================

    def generate_session_summary(self) -> str:
        """
        Genera un resumen formateado para CLAUDE_MEMORY.md.

        Returns:
            String con el resumen en formato Markdown.
        """
        lines = []
        now = datetime.now()

        # Header
        lines.append("# CLAUDE_MEMORY.md - Sistema de Memoria Persistente")
        lines.append("")
        lines.append("Este archivo sirve como memoria persistente entre sesiones de Claude Code.")
        lines.append("Claude debe leer este archivo al inicio de cada sesion para recordar contexto importante.")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Ultima actualizacion
        lines.append("## Ultima Actualizacion")
        lines.append(f"- **Fecha**: {now.strftime('%Y-%m-%d')}")

        # Obtener sesion mas reciente
        recent_sessions = self.get_all_sessions(limit=1)
        if recent_sessions:
            session = recent_sessions[0]
            task = session.get("task_description", "Sesion sin descripcion")
            lines.append(f"- **Sesion**: {task}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Decisiones de Arquitectura
        lines.append("## Decisiones de Arquitectura Importantes")
        lines.append("")

        arch_learnings = self.get_learnings("architecture")
        if arch_learnings:
            for idx, (key, learning) in enumerate(arch_learnings.items(), 1):
                lines.append(f"### {idx}. {key.replace('_', ' ').title()}")
                lines.append(f"- {learning.get('value', '')}")
                lines.append("")
        else:
            lines.append("*No hay decisiones de arquitectura registradas*")
            lines.append("")

        # Patrones de codigo
        pattern_learnings = self.get_learnings("patterns")
        if pattern_learnings:
            lines.append("### Patrones de Codigo")
            for key, learning in pattern_learnings.items():
                lines.append(f"- **{key}**: {learning.get('value', '')}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Features Implementadas
        lines.append("## Features Implementadas (Historial)")
        lines.append("")

        features = self.get_feature_history()
        if features:
            # Agrupar por version
            versions = {}
            for feature in features:
                ver = feature.get("version", "0.0.0")
                if ver not in versions:
                    versions[ver] = []
                versions[ver].append(feature)

            for ver in sorted(versions.keys(), reverse=True):
                feature_list = versions[ver]
                date = feature_list[0].get("implementation_date", "")
                lines.append(f"### v{ver} ({date})")
                for f in feature_list:
                    lines.append(f"- **{f['feature_name']}**: {f.get('description', '')}")
                    if f.get("endpoints"):
                        lines.append(f"  - Endpoints: {', '.join(f['endpoints'])}")
                lines.append("")
        else:
            lines.append("*No hay features registradas*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Errores Conocidos
        lines.append("## Errores Conocidos y Soluciones")
        lines.append("")

        errors = self.get_all_errors()
        if errors:
            for error in errors:
                verified = " [VERIFICADO]" if error.get("verified") else ""
                lines.append(f"### Error: {error.get('error_pattern', 'Sin patron')}{verified}")
                lines.append(f"- **Solucion**: {error.get('solution', '')}")
                if error.get("solution_details"):
                    lines.append(f"- **Detalles**: {error['solution_details']}")
                if error.get("related_files"):
                    lines.append(f"- **Archivos**: {', '.join(error['related_files'])}")
                lines.append("")
        else:
            lines.append("*No hay errores registrados*")
            lines.append("")

        lines.append("---")
        lines.append("")

        # TODOs Pendientes
        lines.append("## Proximas Mejoras Sugeridas (TODOs)")
        lines.append("")

        todos = self.get_todos(completed=False)
        if todos:
            for todo in todos:
                priority_emoji = {
                    "critical": "[CRITICO]",
                    "high": "[ALTA]",
                    "medium": "",
                    "low": "[BAJA]"
                }.get(todo.get("priority", "medium"), "")

                lines.append(f"1. [ ] **{todo.get('title', '')}** {priority_emoji}")
                if todo.get("description"):
                    lines.append(f"   - {todo['description']}")
        else:
            lines.append("*No hay TODOs pendientes*")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Preferencias del Usuario
        lines.append("## Contacto con Usuario")
        lines.append("")
        lines.append("### Preferencias conocidas:")

        prefs = self.get_user_preferences()
        if prefs:
            for key, pref in prefs.items():
                lines.append(f"- {key.replace('_', ' ').title()}: {pref.get('value', '')}")
        else:
            lines.append("- *No hay preferencias registradas*")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Convenciones
        lines.append("## Convenciones del Proyecto")
        lines.append("")

        conv_learnings = self.get_learnings("conventions")
        if conv_learnings:
            for key, learning in conv_learnings.items():
                lines.append(f"### {key.replace('_', ' ').title()}")
                lines.append(f"- {learning.get('value', '')}")
                lines.append("")

        lines.append("---")
        lines.append("")

        # Notas para Claude
        lines.append("## Notas para Claude")
        lines.append("")
        lines.append("### Al iniciar sesion:")
        lines.append("1. Leer este archivo primero")
        lines.append("2. Verificar estado de git (`git status`, `git log -3`)")
        lines.append("3. Revisar TODOs pendientes si existen")
        lines.append("")
        lines.append("### Antes de implementar:")
        lines.append("1. Verificar si ya existe funcionalidad similar")
        lines.append('2. Revisar seccion "Errores Conocidos"')
        lines.append('3. Seguir patrones establecidos en "Decisiones de Arquitectura"')
        lines.append("")
        lines.append("### Al terminar sesion:")
        lines.append("1. Actualizar este archivo con nuevos aprendizajes")
        lines.append("2. Documentar errores encontrados y soluciones")
        lines.append("3. Agregar features implementadas al historial")
        lines.append("")

        return "\n".join(lines)

    def sync_to_claude_memory(self) -> bool:
        """
        Sincroniza los datos al archivo CLAUDE_MEMORY.md.

        Returns:
            True si se sincronizo correctamente.
        """
        try:
            content = self.generate_session_summary()

            with open(self.claude_memory_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"CLAUDE_MEMORY.md sincronizado: {self.claude_memory_path}")
            return True
        except Exception as e:
            logger.error(f"Error al sincronizar CLAUDE_MEMORY.md: {e}")
            return False

    def import_from_claude_memory(self) -> Dict[str, int]:
        """
        Importa datos existentes desde CLAUDE_MEMORY.md.

        Parsea el archivo existente y extrae:
        - Decisiones de arquitectura -> learnings
        - Features -> features
        - Errores -> errors
        - TODOs -> todos
        - Preferencias -> preferences

        Returns:
            Diccionario con conteo de items importados por categoria.
        """
        stats = {
            "learnings": 0,
            "features": 0,
            "errors": 0,
            "todos": 0,
            "preferences": 0
        }

        if not self.claude_memory_path.exists():
            logger.warning(f"CLAUDE_MEMORY.md no existe: {self.claude_memory_path}")
            return stats

        try:
            with open(self.claude_memory_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parsear secciones
            sections = self._parse_markdown_sections(content)

            # Importar decisiones de arquitectura
            if "Decisiones de Arquitectura" in sections:
                for item in sections["Decisiones de Arquitectura"]:
                    if item.get("title") and item.get("content"):
                        self.add_learning(
                            "architecture",
                            item["title"].lower().replace(" ", "_"),
                            item["content"]
                        )
                        stats["learnings"] += 1

            # Importar features
            if "Features Implementadas" in sections:
                for item in sections["Features Implementadas"]:
                    if item.get("name"):
                        self.add_feature_history(item["name"], {
                            "version": item.get("version", "0.0.0"),
                            "description": item.get("description", ""),
                            "status": "completed"
                        })
                        stats["features"] += 1

            # Importar errores
            if "Errores Conocidos" in sections:
                for item in sections["Errores Conocidos"]:
                    if item.get("pattern") and item.get("solution"):
                        self.add_error_solution(
                            item["pattern"],
                            item["solution"],
                            solution_details=item.get("details")
                        )
                        stats["errors"] += 1

            # Importar TODOs
            if "Proximas Mejoras" in sections or "TODOs" in sections:
                section_name = "Proximas Mejoras" if "Proximas Mejoras" in sections else "TODOs"
                for item in sections[section_name]:
                    if item.get("title"):
                        self.add_todo(
                            item["title"],
                            description=item.get("description"),
                            priority=item.get("priority", "medium")
                        )
                        stats["todos"] += 1

            # Importar preferencias
            if "Preferencias" in sections:
                for item in sections["Preferencias"]:
                    if item.get("key") and item.get("value"):
                        self.add_user_preference(item["key"], item["value"])
                        stats["preferences"] += 1

            self._save()
            logger.info(f"Importacion completada: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error al importar desde CLAUDE_MEMORY.md: {e}")
            return stats

    def _parse_markdown_sections(self, content: str) -> Dict[str, List[Dict]]:
        """Parsea secciones de un archivo Markdown."""
        sections = {}
        current_section = None
        current_items = []

        lines = content.split('\n')

        for line in lines:
            # Detectar headers de seccion (##)
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = current_items
                current_section = line[3:].strip()
                current_items = []

            # Detectar sub-headers (###)
            elif line.startswith('### ') and current_section:
                title = line[4:].strip()
                current_items.append({"title": title, "content": ""})

            # Detectar items de lista
            elif line.startswith('- ') and current_items:
                item_content = line[2:].strip()
                if current_items and "content" in current_items[-1]:
                    if current_items[-1]["content"]:
                        current_items[-1]["content"] += " | " + item_content
                    else:
                        current_items[-1]["content"] = item_content

            # Detectar TODOs
            elif '[ ]' in line or '[x]' in line:
                match = re.search(r'\[([ x])\]\s*\*?\*?(.+?)\*?\*?', line)
                if match:
                    completed = match.group(1) == 'x'
                    title = match.group(2).strip()
                    current_items.append({
                        "title": title,
                        "completed": completed
                    })

        if current_section:
            sections[current_section] = current_items

        return sections

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadisticas del sistema de memoria.

        Returns:
            Diccionario con estadisticas.
        """
        return {
            "total_sessions": len(self.data["sessions"]),
            "total_learnings": sum(len(cat) for cat in self.data["learnings"].values()),
            "learnings_by_category": {k: len(v) for k, v in self.data["learnings"].items()},
            "total_errors": len(self.data["errors"]),
            "verified_errors": sum(1 for e in self.data["errors"].values() if e.get("verified")),
            "total_features": len(self.data["features"]),
            "total_preferences": len(self.data["preferences"]),
            "pending_todos": len([t for t in self.data["todos"].values() if not t.get("completed")]),
            "completed_todos": len([t for t in self.data["todos"].values() if t.get("completed")]),
            "storage_path": str(self.storage_path),
            "last_updated": self.data["metadata"].get("last_updated")
        }

    def export_to_dict(self) -> Dict[str, Any]:
        """Exporta todos los datos como diccionario."""
        return self.data.copy()

    def clear_all(self, confirm: bool = False) -> bool:
        """
        Limpia todos los datos almacenados.

        Args:
            confirm: Debe ser True para confirmar la operacion

        Returns:
            True si se limpio correctamente.
        """
        if not confirm:
            logger.warning("clear_all() requiere confirm=True")
            return False

        self.data = {
            "sessions": {},
            "learnings": {},
            "errors": {},
            "features": [],
            "preferences": {},
            "todos": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0",
                "total_sessions": 0
            }
        }

        self._save()
        logger.info("Todos los datos han sido limpiados")
        return True

    # =========================================================================
    # CLEANUP AUTOMÁTICO
    # =========================================================================

    def cleanup_old_sessions(
        self,
        max_age_days: int = 30,
        keep_minimum: int = 5
    ) -> Dict[str, int]:
        """
        Limpia sesiones antiguas para evitar acumulación de datos.

        Args:
            max_age_days: Edad máxima en días para mantener sesiones
            keep_minimum: Número mínimo de sesiones a mantener (incluso si son antiguas)

        Returns:
            Dict con estadísticas de cleanup: {'removed': N, 'kept': M}
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            sessions = self.data["sessions"]

            # Ordenar por fecha (más recientes primero)
            sorted_sessions = sorted(
                sessions.items(),
                key=lambda x: x[1].get("start_time", ""),
                reverse=True
            )

            # Mantener las más recientes (keep_minimum) y las que no son antiguas
            to_keep = {}
            to_remove = []

            for idx, (session_id, session_data) in enumerate(sorted_sessions):
                # Siempre mantener las primeras keep_minimum sesiones
                if idx < keep_minimum:
                    to_keep[session_id] = session_data
                    continue

                # Verificar edad
                start_time_str = session_data.get("start_time", "")
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str)
                        if start_time >= cutoff_date:
                            to_keep[session_id] = session_data
                        else:
                            to_remove.append(session_id)
                    except ValueError:
                        # Si no se puede parsear la fecha, mantener
                        to_keep[session_id] = session_data
                else:
                    to_keep[session_id] = session_data

            self.data["sessions"] = to_keep
            self.data["metadata"]["total_sessions"] = len(to_keep)
            self._save()

            result = {'removed': len(to_remove), 'kept': len(to_keep)}
            if to_remove:
                logger.info(f"Cleanup: {len(to_remove)} sesiones antiguas eliminadas, {len(to_keep)} mantenidas")
            return result

        except Exception as e:
            logger.error(f"Error en cleanup de sesiones: {e}")
            return {'removed': 0, 'kept': len(self.data["sessions"]), 'error': str(e)}

    def cleanup_completed_todos(
        self,
        max_age_days: int = 90
    ) -> Dict[str, int]:
        """
        Limpia TODOs completados que son antiguos.

        Args:
            max_age_days: Edad máxima en días para mantener TODOs completados

        Returns:
            Dict con estadísticas de cleanup
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            to_remove = []

            for todo_id, todo in self.data["todos"].items():
                if todo.get("completed"):
                    completed_at = todo.get("completed_at", "")
                    if completed_at:
                        try:
                            completed_time = datetime.fromisoformat(completed_at)
                            if completed_time < cutoff_date:
                                to_remove.append(todo_id)
                        except ValueError:
                            pass

            for todo_id in to_remove:
                del self.data["todos"][todo_id]

            self._save()

            result = {'removed': len(to_remove), 'kept': len(self.data["todos"])}
            if to_remove:
                logger.info(f"Cleanup: {len(to_remove)} TODOs completados eliminados")
            return result

        except Exception as e:
            logger.error(f"Error en cleanup de TODOs: {e}")
            return {'removed': 0, 'kept': len(self.data["todos"]), 'error': str(e)}

    def cleanup_unused_errors(
        self,
        min_usage: int = 0,
        max_age_days: int = 180
    ) -> Dict[str, int]:
        """
        Limpia errores que nunca se han usado y son antiguos.

        Args:
            min_usage: Uso mínimo requerido para mantener (0 = nunca usado)
            max_age_days: Edad máxima en días

        Returns:
            Dict con estadísticas de cleanup
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            to_remove = []

            for error_id, error in self.data["errors"].items():
                times_used = error.get("times_used", 0)
                created_at = error.get("created_at", "")

                if times_used <= min_usage and created_at:
                    try:
                        created_time = datetime.fromisoformat(created_at)
                        if created_time < cutoff_date:
                            to_remove.append(error_id)
                    except ValueError:
                        pass

            for error_id in to_remove:
                del self.data["errors"][error_id]

            self._save()

            result = {'removed': len(to_remove), 'kept': len(self.data["errors"])}
            if to_remove:
                logger.info(f"Cleanup: {len(to_remove)} errores sin uso eliminados")
            return result

        except Exception as e:
            logger.error(f"Error en cleanup de errores: {e}")
            return {'removed': 0, 'kept': len(self.data["errors"]), 'error': str(e)}

    def run_full_cleanup(
        self,
        session_max_age_days: int = 30,
        todo_max_age_days: int = 90,
        error_max_age_days: int = 180,
        session_keep_minimum: int = 5
    ) -> Dict[str, Dict[str, int]]:
        """
        Ejecuta cleanup completo de todos los tipos de datos.

        Args:
            session_max_age_days: Edad máxima para sesiones
            todo_max_age_days: Edad máxima para TODOs completados
            error_max_age_days: Edad máxima para errores sin uso
            session_keep_minimum: Mínimo de sesiones a mantener

        Returns:
            Dict con estadísticas de cleanup por tipo
        """
        logger.info("🧹 Iniciando cleanup completo...")

        results = {
            'sessions': self.cleanup_old_sessions(session_max_age_days, session_keep_minimum),
            'todos': self.cleanup_completed_todos(todo_max_age_days),
            'errors': self.cleanup_unused_errors(0, error_max_age_days)
        }

        total_removed = sum(r.get('removed', 0) for r in results.values())
        logger.info(f"✅ Cleanup completado. Total eliminados: {total_removed}")

        return results

    def get_storage_size(self) -> Dict[str, Any]:
        """
        Obtiene información sobre el tamaño del almacenamiento.

        Returns:
            Dict con tamaños por sección y total
        """
        import sys

        sizes = {
            'sessions': len(self.data["sessions"]),
            'learnings': sum(len(cat) for cat in self.data["learnings"].values()),
            'errors': len(self.data["errors"]),
            'features': len(self.data["features"]),
            'preferences': len(self.data["preferences"]),
            'todos': len(self.data["todos"]),
        }

        # Tamaño aproximado en bytes
        try:
            import json
            json_str = json.dumps(self.data, default=str)
            sizes['total_bytes'] = len(json_str.encode('utf-8'))
            sizes['total_kb'] = round(sizes['total_bytes'] / 1024, 2)
        except Exception:
            sizes['total_bytes'] = 0
            sizes['total_kb'] = 0

        # Archivo físico
        if self.storage_path.exists():
            sizes['file_bytes'] = self.storage_path.stat().st_size
            sizes['file_kb'] = round(sizes['file_bytes'] / 1024, 2)
        else:
            sizes['file_bytes'] = 0
            sizes['file_kb'] = 0

        return sizes


# =========================================================================
# FUNCIONES DE CONVENIENCIA
# =========================================================================

_memory_instance: Optional[MemoryAgent] = None


def get_memory_agent() -> MemoryAgent:
    """
    Obtiene una instancia singleton del MemoryAgent.

    Returns:
        Instancia de MemoryAgent.
    """
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MemoryAgent()
    return _memory_instance


def quick_save_learning(category: str, key: str, value: str) -> bool:
    """Funcion rapida para guardar un aprendizaje."""
    return get_memory_agent().add_learning(category, key, value)


def quick_find_solution(error: str) -> List[Dict[str, Any]]:
    """Funcion rapida para buscar soluciones."""
    return get_memory_agent().find_error_solution(error)


# =========================================================================
# MAIN (para testing)
# =========================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Demo del agente
    print("=" * 60)
    print("MEMORY AGENT - Demo")
    print("=" * 60)

    memory = MemoryAgent()

    # Agregar datos de ejemplo
    print("\n1. Agregando aprendizajes...")
    memory.add_learning(
        "architecture",
        "db_pattern",
        "Usar INSERT OR REPLACE para sincronizacion idempotente",
        tags=["database", "sqlite"]
    )
    memory.add_learning(
        "patterns",
        "singleton_app",
        "Frontend usa patron singleton App.{module}",
        tags=["javascript", "frontend"]
    )

    print("\n2. Registrando errores y soluciones...")
    memory.add_error_solution(
        "Celdas con comentarios no se parsean en Excel",
        "Usar sistema de edicion manual v2.1",
        solution_details="El parametro data_only=True ignora comentarios",
        related_files=["excel_service.py"]
    )

    print("\n3. Agregando feature...")
    memory.add_feature_history("edit_excel_v2.1", {
        "version": "2.1",
        "description": "CRUD completo para yukyu_usage_details",
        "status": "completed",
        "endpoints": ["/api/yukyu/usage-details", "/api/yukyu/recalculate"],
        "files_affected": ["main.py", "database.py", "app.js"]
    })

    print("\n4. Guardando preferencias...")
    memory.add_user_preference("language", "castellano", "communication")
    memory.add_user_preference("prefer_visual_explanations", True, "communication")

    print("\n5. Agregando TODOs...")
    memory.add_todo(
        "Mejorar parser de Excel",
        "Detectar medio dia automaticamente",
        priority="high",
        category="parser"
    )

    print("\n6. Guardando contexto de sesion...")
    memory.save_session_context("demo_session_001", {
        "task_description": "Demo del Memory Agent",
        "branch_name": "claude/memory-agent-demo",
        "files_modified": ["agents/memory.py"],
        "notes": ["Crear agente de memoria persistente"]
    })

    # Mostrar estadisticas
    print("\n" + "=" * 60)
    print("ESTADISTICAS")
    print("=" * 60)
    stats = memory.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Buscar solucion
    print("\n" + "=" * 60)
    print("BUSQUEDA DE SOLUCION")
    print("=" * 60)
    solutions = memory.find_error_solution("error al parsear comentarios en Excel")
    if solutions:
        print(f"  Encontradas {len(solutions)} soluciones:")
        for sol in solutions[:3]:
            print(f"    - {sol['solution']}")

    # Generar resumen
    print("\n" + "=" * 60)
    print("PREVIEW DEL RESUMEN PARA CLAUDE_MEMORY.md")
    print("=" * 60)
    summary = memory.generate_session_summary()
    print(summary[:2000] + "\n...[truncado]...")

    print("\n" + "=" * 60)
    print("Demo completado. Storage: " + str(memory.storage_path))
    print("=" * 60)
