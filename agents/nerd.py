"""
Nerd Agent - Agente de Análisis Técnico Profundo
=================================================

El "cerebro analítico" del sistema. Especializado en:
- Análisis de código y arquitectura
- Detección de code smells y anti-patterns
- Métricas de calidad de código
- Análisis de dependencias
- Sugerencias de refactoring
- Análisis de complejidad ciclomática
- Detección de vulnerabilidades potenciales
- Análisis de rendimiento de queries
"""

import logging
import ast
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Niveles de severidad de problemas detectados."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(Enum):
    """Categorías de problemas."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    CODE_SMELL = "code_smell"
    ARCHITECTURE = "architecture"
    DEPENDENCY = "dependency"
    DOCUMENTATION = "documentation"


@dataclass
class CodeIssue:
    """Representa un problema encontrado en el código."""
    id: str
    category: IssueCategory
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int]
    title: str
    description: str
    suggestion: str
    code_snippet: Optional[str] = None
    effort_hours: float = 1.0
    tags: List[str] = field(default_factory=list)
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
            'code_snippet': self.code_snippet,
            'effort_hours': self.effort_hours,
            'tags': self.tags,
            'detected_at': self.detected_at
        }


@dataclass
class CodeMetrics:
    """Métricas de calidad de código."""
    file_path: str
    lines_of_code: int
    lines_of_comments: int
    blank_lines: int
    functions_count: int
    classes_count: int
    cyclomatic_complexity: float
    maintainability_index: float
    comment_ratio: float
    avg_function_length: float
    max_function_length: int
    duplication_ratio: float

    @property
    def health_score(self) -> float:
        """Calcula un score de salud del código (0-100)."""
        score = 100.0

        # Penalizar alta complejidad
        if self.cyclomatic_complexity > 10:
            score -= min(30, (self.cyclomatic_complexity - 10) * 3)

        # Penalizar funciones muy largas
        if self.avg_function_length > 30:
            score -= min(20, (self.avg_function_length - 30))

        # Penalizar poca documentación
        if self.comment_ratio < 0.1:
            score -= 10

        # Penalizar alta duplicación
        if self.duplication_ratio > 0.1:
            score -= min(20, self.duplication_ratio * 100)

        return max(0, min(100, score))


@dataclass
class DependencyInfo:
    """Información de una dependencia."""
    name: str
    current_version: Optional[str]
    latest_version: Optional[str]
    is_outdated: bool
    security_issues: List[str]
    usage_count: int


@dataclass
class AnalysisReport:
    """Reporte completo de análisis técnico."""
    timestamp: str
    files_analyzed: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    metrics: List[CodeMetrics]
    issues: List[CodeIssue]
    dependencies: List[DependencyInfo]
    recommendations: List[str]
    overall_health: float

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'files_analyzed': self.files_analyzed,
            'total_issues': self.total_issues,
            'issues_by_severity': {
                'critical': self.critical_issues,
                'high': self.high_issues,
                'medium': self.medium_issues,
                'low': self.low_issues
            },
            'overall_health': self.overall_health,
            'recommendations': self.recommendations
        }


class NerdAgent:
    """
    Agente Nerd - Análisis Técnico Profundo

    El "cerebro analítico" que examina todo el código en detalle:

    Capacidades:
    - Análisis de código Python (AST parsing)
    - Detección de code smells
    - Métricas de complejidad
    - Análisis de seguridad básico
    - Detección de SQL injection potencial
    - Análisis de dependencias
    - Sugerencias de mejora

    Ejemplo de uso:
    ```python
    nerd = NerdAgent()

    # Análisis completo del proyecto
    report = nerd.analyze_project("/path/to/project")

    # Análisis de un archivo específico
    issues = nerd.analyze_file("/path/to/file.py")

    # Análisis de queries SQL
    sql_issues = nerd.analyze_sql_queries("/path/to/database.py")

    # Obtener métricas
    metrics = nerd.get_code_metrics("/path/to/file.py")
    ```
    """

    # Patrones de code smells
    CODE_SMELL_PATTERNS = {
        'long_function': {'max_lines': 50, 'severity': IssueSeverity.MEDIUM},
        'too_many_params': {'max_params': 5, 'severity': IssueSeverity.MEDIUM},
        'deep_nesting': {'max_depth': 4, 'severity': IssueSeverity.HIGH},
        'magic_numbers': {'severity': IssueSeverity.LOW},
        'god_class': {'max_methods': 20, 'severity': IssueSeverity.HIGH},
        'duplicate_code': {'severity': IssueSeverity.MEDIUM},
    }

    # Patrones de seguridad
    SECURITY_PATTERNS = {
        'hardcoded_password': {
            'patterns': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
            ],
            'severity': IssueSeverity.CRITICAL
        },
        'sql_injection': {
            'patterns': [
                r'execute\s*\(\s*["\'].*\%s.*["\']',
                r'execute\s*\(\s*f["\']',
                r'cursor\.execute\s*\(\s*[^?].*\+',
            ],
            'severity': IssueSeverity.CRITICAL
        },
        'command_injection': {
            'patterns': [
                r'os\.system\s*\(',
                r'subprocess\.call\s*\(\s*[^[]',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'severity': IssueSeverity.HIGH
        },
        'path_traversal': {
            'patterns': [
                r'open\s*\([^)]*\+[^)]*\)',
                r'Path\s*\([^)]*\+[^)]*\)',
            ],
            'severity': IssueSeverity.HIGH
        }
    }

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente Nerd.

        Args:
            project_root: Ruta raíz del proyecto a analizar
        """
        self.project_root = Path(project_root)
        self._issue_counter = 0
        self._analysis_cache: Dict[str, AnalysisReport] = {}

    def _generate_issue_id(self) -> str:
        """Genera un ID único para un issue."""
        self._issue_counter += 1
        return f"NERD-{datetime.now().strftime('%Y%m%d')}-{self._issue_counter:04d}"

    # ========================================
    # ANÁLISIS DE CÓDIGO
    # ========================================

    def analyze_file(self, file_path: str) -> List[CodeIssue]:
        """
        Analiza un archivo Python para detectar problemas.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            Lista de problemas encontrados
        """
        issues = []
        path = Path(file_path)

        if not path.exists() or path.suffix != '.py':
            return issues

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Análisis con AST
            issues.extend(self._analyze_ast(file_path, content))

            # Análisis de patrones de seguridad
            issues.extend(self._analyze_security_patterns(file_path, content, lines))

            # Análisis de code smells
            issues.extend(self._analyze_code_smells(file_path, content, lines))

            logger.info(f"📊 Analizados {len(lines)} líneas en {file_path}: {len(issues)} problemas")

        except Exception as e:
            logger.error(f"Error analizando {file_path}: {e}")

        return issues

    def _analyze_ast(self, file_path: str, content: str) -> List[CodeIssue]:
        """Analiza el AST del código Python."""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Detectar funciones muy largas
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0

                    if func_lines > self.CODE_SMELL_PATTERNS['long_function']['max_lines']:
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.CODE_SMELL,
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            title=f"Función muy larga: {node.name}",
                            description=f"La función '{node.name}' tiene {func_lines} líneas. "
                                       f"Las funciones largas son difíciles de mantener.",
                            suggestion="Considera dividir esta función en funciones más pequeñas "
                                       "con responsabilidades únicas (Single Responsibility Principle).",
                            effort_hours=2.0,
                            tags=['refactoring', 'maintainability']
                        ))

                    # Demasiados parámetros
                    param_count = len(node.args.args)
                    if param_count > self.CODE_SMELL_PATTERNS['too_many_params']['max_params']:
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.CODE_SMELL,
                            severity=IssueSeverity.MEDIUM,
                            file_path=file_path,
                            line_number=node.lineno,
                            title=f"Demasiados parámetros: {node.name}",
                            description=f"La función '{node.name}' tiene {param_count} parámetros. "
                                       f"Esto indica posible violación del principio de responsabilidad única.",
                            suggestion="Considera usar un dataclass o dict para agrupar parámetros relacionados, "
                                       "o dividir la función.",
                            effort_hours=1.5,
                            tags=['refactoring', 'clean-code']
                        ))

                # Detectar clases muy grandes (God Class)
                if isinstance(node, ast.ClassDef):
                    method_count = sum(1 for n in ast.walk(node)
                                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))

                    if method_count > self.CODE_SMELL_PATTERNS['god_class']['max_methods']:
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.ARCHITECTURE,
                            severity=IssueSeverity.HIGH,
                            file_path=file_path,
                            line_number=node.lineno,
                            title=f"God Class detectada: {node.name}",
                            description=f"La clase '{node.name}' tiene {method_count} métodos. "
                                       f"Las clases muy grandes violan el principio de responsabilidad única.",
                            suggestion="Divide esta clase en clases más pequeñas con responsabilidades específicas. "
                                       "Considera usar composición en lugar de herencia.",
                            effort_hours=4.0,
                            tags=['architecture', 'refactoring', 'solid']
                        ))

                # Detectar uso de eval/exec
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in ['eval', 'exec']:
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.SECURITY,
                            severity=IssueSeverity.CRITICAL,
                            file_path=file_path,
                            line_number=node.lineno,
                            title=f"Uso peligroso de {node.func.id}()",
                            description=f"El uso de {node.func.id}() puede permitir ejecución de código arbitrario "
                                       f"y es un vector común de ataques de inyección.",
                            suggestion="Evita usar eval/exec. Si es necesario, valida estrictamente la entrada "
                                       "o usa ast.literal_eval() para datos literales.",
                            effort_hours=2.0,
                            tags=['security', 'critical']
                        ))

        except SyntaxError as e:
            issues.append(CodeIssue(
                id=self._generate_issue_id(),
                category=IssueCategory.RELIABILITY,
                severity=IssueSeverity.CRITICAL,
                file_path=file_path,
                line_number=e.lineno,
                title="Error de sintaxis",
                description=f"El archivo contiene un error de sintaxis: {e.msg}",
                suggestion="Corrige el error de sintaxis antes de continuar.",
                effort_hours=0.5,
                tags=['syntax', 'blocking']
            ))

        return issues

    def _analyze_security_patterns(
        self,
        file_path: str,
        content: str,
        lines: List[str]
    ) -> List[CodeIssue]:
        """Analiza patrones de seguridad conocidos."""
        issues = []

        for issue_type, config in self.SECURITY_PATTERNS.items():
            for pattern in config['patterns']:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.SECURITY,
                            severity=config['severity'],
                            file_path=file_path,
                            line_number=i,
                            title=f"Posible vulnerabilidad: {issue_type.replace('_', ' ').title()}",
                            description=self._get_security_description(issue_type),
                            suggestion=self._get_security_suggestion(issue_type),
                            code_snippet=line.strip()[:100],
                            effort_hours=2.0,
                            tags=['security', issue_type]
                        ))

        return issues

    def _get_security_description(self, issue_type: str) -> str:
        """Obtiene descripción de un problema de seguridad."""
        descriptions = {
            'hardcoded_password': "Se detectó una posible contraseña o secreto hardcodeado en el código. "
                                  "Esto es un riesgo crítico de seguridad.",
            'sql_injection': "Se detectó una posible vulnerabilidad de SQL injection. "
                            "Las queries deben usar parámetros vinculados, no concatenación.",
            'command_injection': "Se detectó una posible vulnerabilidad de inyección de comandos. "
                                "Los comandos del sistema deben validarse estrictamente.",
            'path_traversal': "Se detectó una posible vulnerabilidad de path traversal. "
                             "Las rutas de archivo deben validarse y sanitizarse."
        }
        return descriptions.get(issue_type, "Posible problema de seguridad detectado.")

    def _get_security_suggestion(self, issue_type: str) -> str:
        """Obtiene sugerencia para un problema de seguridad."""
        suggestions = {
            'hardcoded_password': "Usa variables de entorno (os.environ) o un gestor de secretos "
                                  "como AWS Secrets Manager, HashiCorp Vault, o archivos .env.",
            'sql_injection': "Usa queries parametrizadas: cursor.execute('SELECT * FROM t WHERE id=?', (id,)). "
                            "Considera usar un ORM como SQLAlchemy.",
            'command_injection': "Usa subprocess.run() con una lista de argumentos en lugar de shell=True. "
                                "Valida y escapa todas las entradas del usuario.",
            'path_traversal': "Usa pathlib para manejar rutas y valida que las rutas estén dentro "
                             "del directorio permitido con .resolve() y verificación de prefijo."
        }
        return suggestions.get(issue_type, "Revisa y corrige esta vulnerabilidad de seguridad.")

    def _analyze_code_smells(
        self,
        file_path: str,
        content: str,
        lines: List[str]
    ) -> List[CodeIssue]:
        """Detecta code smells comunes."""
        issues = []

        # Detectar números mágicos
        magic_number_pattern = r'(?<!["\'\w])\b(?<!\.)\d{2,}\b(?!["\'])'
        for i, line in enumerate(lines, 1):
            # Ignorar líneas que son comentarios o imports
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('import') or stripped.startswith('from'):
                continue

            matches = re.findall(magic_number_pattern, line)
            for match in matches:
                # Ignorar algunos casos comunes
                if match in ['100', '1000', '60', '24', '365']:
                    continue
                if 'line' in line.lower() or 'port' in line.lower():
                    continue

                issues.append(CodeIssue(
                    id=self._generate_issue_id(),
                    category=IssueCategory.CODE_SMELL,
                    severity=IssueSeverity.LOW,
                    file_path=file_path,
                    line_number=i,
                    title=f"Número mágico detectado: {match}",
                    description="Los números mágicos dificultan la comprensión y mantenimiento del código.",
                    suggestion=f"Extrae el valor {match} a una constante con nombre descriptivo.",
                    code_snippet=line.strip()[:80],
                    effort_hours=0.25,
                    tags=['magic-number', 'clean-code']
                ))

        # Detectar líneas muy largas
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(CodeIssue(
                    id=self._generate_issue_id(),
                    category=IssueCategory.MAINTAINABILITY,
                    severity=IssueSeverity.LOW,
                    file_path=file_path,
                    line_number=i,
                    title=f"Línea demasiado larga ({len(line)} caracteres)",
                    description="Las líneas muy largas dificultan la lectura del código.",
                    suggestion="Divide la línea en múltiples líneas. PEP 8 recomienda máximo 79-120 caracteres.",
                    effort_hours=0.1,
                    tags=['formatting', 'pep8']
                ))

        # Detectar TODO/FIXME abandonados
        todo_pattern = r'#\s*(TODO|FIXME|HACK|XXX)[\s:]+(.+)'
        for i, line in enumerate(lines, 1):
            match = re.search(todo_pattern, line, re.IGNORECASE)
            if match:
                issues.append(CodeIssue(
                    id=self._generate_issue_id(),
                    category=IssueCategory.MAINTAINABILITY,
                    severity=IssueSeverity.INFO,
                    file_path=file_path,
                    line_number=i,
                    title=f"{match.group(1).upper()} encontrado",
                    description=f"Comentario pendiente: {match.group(2).strip()[:50]}...",
                    suggestion="Considera resolver este TODO o crear un issue de seguimiento.",
                    code_snippet=line.strip()[:80],
                    effort_hours=0.5,
                    tags=['todo', 'technical-debt']
                ))

        return issues

    def get_code_metrics(self, file_path: str) -> Optional[CodeMetrics]:
        """
        Calcula métricas de calidad de código para un archivo.

        Args:
            file_path: Ruta al archivo Python

        Returns:
            CodeMetrics con las métricas calculadas
        """
        path = Path(file_path)

        if not path.exists() or path.suffix != '.py':
            return None

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Contar tipos de líneas
            loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comments = len([l for l in lines if l.strip().startswith('#')])
            blanks = len([l for l in lines if not l.strip()])

            # Analizar AST para funciones y clases
            tree = ast.parse(content)

            functions = [n for n in ast.walk(tree)
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

            # Calcular longitudes de funciones
            func_lengths = []
            for func in functions:
                if hasattr(func, 'end_lineno'):
                    func_lengths.append(func.end_lineno - func.lineno)

            avg_func_len = sum(func_lengths) / len(func_lengths) if func_lengths else 0
            max_func_len = max(func_lengths) if func_lengths else 0

            # Calcular complejidad ciclomática simplificada
            complexity = self._calculate_cyclomatic_complexity(tree)

            # Calcular ratio de comentarios
            comment_ratio = comments / max(loc, 1)

            # Índice de mantenibilidad simplificado
            mi = max(0, 100 - complexity * 2 - avg_func_len * 0.5)

            return CodeMetrics(
                file_path=file_path,
                lines_of_code=loc,
                lines_of_comments=comments,
                blank_lines=blanks,
                functions_count=len(functions),
                classes_count=len(classes),
                cyclomatic_complexity=complexity,
                maintainability_index=mi,
                comment_ratio=comment_ratio,
                avg_function_length=avg_func_len,
                max_function_length=max_func_len,
                duplication_ratio=0.0  # Requiere análisis más complejo
            )

        except Exception as e:
            logger.error(f"Error calculando métricas para {file_path}: {e}")
            return None

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calcula complejidad ciclomática simplificada."""
        complexity = 1  # Base

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
                if node.ifs:
                    complexity += len(node.ifs)

        return complexity

    # ========================================
    # ANÁLISIS DE PROYECTO COMPLETO
    # ========================================

    def analyze_project(
        self,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> AnalysisReport:
        """
        Analiza todo el proyecto Python.

        Args:
            include_patterns: Patrones glob a incluir (default: ["**/*.py"])
            exclude_patterns: Patrones glob a excluir

        Returns:
            AnalysisReport con resultados completos
        """
        include_patterns = include_patterns or ["**/*.py"]
        exclude_patterns = exclude_patterns or [
            "**/venv/**", "**/.venv/**", "**/node_modules/**",
            "**/__pycache__/**", "**/test_*.py", "**/*_test.py"
        ]

        all_issues: List[CodeIssue] = []
        all_metrics: List[CodeMetrics] = []
        files_analyzed = 0

        logger.info(f"🔬 Iniciando análisis del proyecto: {self.project_root}")

        for pattern in include_patterns:
            for file_path in self.project_root.glob(pattern):
                # Verificar exclusiones
                should_exclude = False
                for exclude in exclude_patterns:
                    if file_path.match(exclude):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                # Analizar archivo
                issues = self.analyze_file(str(file_path))
                all_issues.extend(issues)

                metrics = self.get_code_metrics(str(file_path))
                if metrics:
                    all_metrics.append(metrics)

                files_analyzed += 1

        # Clasificar issues por severidad
        critical = sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL)
        high = sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH)
        medium = sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM)
        low = sum(1 for i in all_issues if i.severity == IssueSeverity.LOW)

        # Calcular salud general
        avg_health = sum(m.health_score for m in all_metrics) / len(all_metrics) if all_metrics else 0
        overall_health = avg_health - (critical * 10) - (high * 5) - (medium * 2)
        overall_health = max(0, min(100, overall_health))

        # Generar recomendaciones
        recommendations = self._generate_recommendations(all_issues, all_metrics)

        report = AnalysisReport(
            timestamp=datetime.now().isoformat(),
            files_analyzed=files_analyzed,
            total_issues=len(all_issues),
            critical_issues=critical,
            high_issues=high,
            medium_issues=medium,
            low_issues=low,
            metrics=all_metrics,
            issues=all_issues,
            dependencies=[],  # Se puede expandir
            recommendations=recommendations,
            overall_health=overall_health
        )

        logger.info(f"✅ Análisis completado: {files_analyzed} archivos, "
                   f"{len(all_issues)} problemas, salud: {overall_health:.1f}%")

        return report

    def _generate_recommendations(
        self,
        issues: List[CodeIssue],
        metrics: List[CodeMetrics]
    ) -> List[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []

        # Verificar issues críticos
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            recommendations.append(
                f"⚠️ URGENTE: Hay {len(critical_issues)} problemas críticos de seguridad. "
                "Deben resolverse antes de cualquier deploy a producción."
            )

        # Verificar seguridad
        security_issues = [i for i in issues if i.category == IssueCategory.SECURITY]
        if security_issues:
            recommendations.append(
                f"🔒 Seguridad: Se encontraron {len(security_issues)} problemas de seguridad. "
                "Revisa credenciales hardcodeadas, SQL injection y validación de entrada."
            )

        # Verificar complejidad
        high_complexity = [m for m in metrics if m.cyclomatic_complexity > 15]
        if high_complexity:
            recommendations.append(
                f"📊 Complejidad: {len(high_complexity)} archivos tienen alta complejidad ciclomática. "
                "Considera refactorizar para mejorar mantenibilidad."
            )

        # Verificar funciones largas
        long_funcs = [i for i in issues if 'long_function' in str(i.tags)]
        if len(long_funcs) > 5:
            recommendations.append(
                f"📏 Funciones largas: Se detectaron {len(long_funcs)} funciones muy extensas. "
                "Aplica el principio de responsabilidad única (SRP)."
            )

        # Verificar documentación
        avg_comments = sum(m.comment_ratio for m in metrics) / len(metrics) if metrics else 0
        if avg_comments < 0.1:
            recommendations.append(
                "📝 Documentación: El ratio de comentarios es bajo (<10%). "
                "Considera añadir docstrings y comentarios explicativos."
            )

        # Si todo está bien
        if not recommendations:
            recommendations.append(
                "✅ ¡Excelente! El código está en buen estado. "
                "Continúa aplicando buenas prácticas."
            )

        return recommendations

    # ========================================
    # ANÁLISIS ESPECIALIZADO
    # ========================================

    def analyze_sql_queries(self, file_path: str) -> List[CodeIssue]:
        """
        Analiza un archivo específicamente para problemas de SQL.

        Args:
            file_path: Ruta al archivo con queries SQL

        Returns:
            Lista de problemas encontrados
        """
        issues = []
        path = Path(file_path)

        if not path.exists():
            return issues

        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Patrones de SQL peligroso
        dangerous_patterns = [
            (r'execute\s*\(\s*f["\']', "f-string en SQL"),
            (r'execute\s*\([^)]*\s*\+\s*', "concatenación en SQL"),
            (r'execute\s*\([^)]*%\s*\(', "formato % en SQL"),
            (r'execute\s*\([^)]*\.format\s*\(', ".format() en SQL"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        id=self._generate_issue_id(),
                        category=IssueCategory.SECURITY,
                        severity=IssueSeverity.CRITICAL,
                        file_path=file_path,
                        line_number=i,
                        title=f"SQL Injection: {desc}",
                        description=f"Se detectó {desc}, lo cual es vulnerable a SQL injection.",
                        suggestion="Usa queries parametrizadas: execute('SELECT * FROM t WHERE id=?', (id,))",
                        code_snippet=line.strip()[:100],
                        effort_hours=1.0,
                        tags=['sql-injection', 'security', 'critical']
                    ))

        return issues

    def analyze_api_endpoints(self, file_path: str) -> List[CodeIssue]:
        """
        Analiza endpoints de API para problemas comunes.

        Args:
            file_path: Ruta al archivo de API (FastAPI/Flask)

        Returns:
            Lista de problemas encontrados
        """
        issues = []
        path = Path(file_path)

        if not path.exists():
            return issues

        content = path.read_text(encoding='utf-8')
        lines = content.split('\n')

        # Detectar endpoints sin autenticación (simplificado)
        endpoint_pattern = r'@app\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)'
        auth_required_pattern = r'Depends\s*\(\s*(require_auth|get_current_user|verify_token)'

        in_endpoint = False
        endpoint_start = 0
        endpoint_path = ""
        has_auth = False

        for i, line in enumerate(lines, 1):
            # Detectar inicio de endpoint
            match = re.search(endpoint_pattern, line, re.IGNORECASE)
            if match:
                # Si había un endpoint anterior sin auth
                if in_endpoint and not has_auth and '/api/' in endpoint_path:
                    # Excluir endpoints públicos conocidos
                    public_endpoints = ['/api/auth/login', '/api/health', '/docs', '/redoc']
                    if not any(ep in endpoint_path for ep in public_endpoints):
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.SECURITY,
                            severity=IssueSeverity.HIGH,
                            file_path=file_path,
                            line_number=endpoint_start,
                            title=f"Endpoint sin autenticación: {endpoint_path}",
                            description=f"El endpoint {endpoint_path} parece no tener verificación de autenticación.",
                            suggestion="Añade Depends(require_auth) o similar para proteger este endpoint.",
                            effort_hours=0.5,
                            tags=['security', 'authentication', 'api']
                        ))

                in_endpoint = True
                endpoint_start = i
                endpoint_path = match.group(2)
                has_auth = False

            # Verificar si tiene auth
            if in_endpoint and re.search(auth_required_pattern, line):
                has_auth = True

            # Detectar fin de función
            if in_endpoint and line.strip().startswith('def ') and i > endpoint_start + 1:
                # Procesar endpoint anterior
                if not has_auth and '/api/' in endpoint_path:
                    public_endpoints = ['/api/auth/login', '/api/health', '/docs', '/redoc']
                    if not any(ep in endpoint_path for ep in public_endpoints):
                        issues.append(CodeIssue(
                            id=self._generate_issue_id(),
                            category=IssueCategory.SECURITY,
                            severity=IssueSeverity.HIGH,
                            file_path=file_path,
                            line_number=endpoint_start,
                            title=f"Endpoint sin autenticación: {endpoint_path}",
                            description=f"El endpoint {endpoint_path} parece no tener verificación de autenticación.",
                            suggestion="Añade Depends(require_auth) o similar para proteger este endpoint.",
                            effort_hours=0.5,
                            tags=['security', 'authentication', 'api']
                        ))
                in_endpoint = False

        return issues

    def get_tech_debt_estimate(self) -> Dict[str, Any]:
        """
        Calcula una estimación de deuda técnica del proyecto.

        Returns:
            Dict con estimación de horas/días para resolver issues
        """
        report = self.analyze_project()

        total_hours = sum(issue.effort_hours for issue in report.issues)

        by_category = {}
        for issue in report.issues:
            cat = issue.category.value
            if cat not in by_category:
                by_category[cat] = {'count': 0, 'hours': 0}
            by_category[cat]['count'] += 1
            by_category[cat]['hours'] += issue.effort_hours

        by_severity = {}
        for issue in report.issues:
            sev = issue.severity.value
            if sev not in by_severity:
                by_severity[sev] = {'count': 0, 'hours': 0}
            by_severity[sev]['count'] += 1
            by_severity[sev]['hours'] += issue.effort_hours

        return {
            'total_issues': len(report.issues),
            'total_hours': total_hours,
            'total_days': total_hours / 8,
            'by_category': by_category,
            'by_severity': by_severity,
            'priority_fixes': [
                issue.to_dict() for issue in report.issues
                if issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
            ][:10],
            'health_score': report.overall_health
        }


# Instancia singleton
_nerd_instance: Optional[NerdAgent] = None


def get_nerd_agent(project_root: str = ".") -> NerdAgent:
    """Obtiene la instancia global del Agente Nerd."""
    global _nerd_instance
    if _nerd_instance is None:
        _nerd_instance = NerdAgent(project_root)
    return _nerd_instance
