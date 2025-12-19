"""
UX Analyst Agent - Agente de Análisis de Experiencia de Usuario
================================================================

Experto en UX que analiza y mejora la experiencia del usuario:
- Análisis de flujos de usuario
- Detección de fricción en interfaces
- Análisis de formularios
- Evaluación heurística (Nielsen)
- Mapeo de user journeys
- Análisis de microinteracciones
- Sugerencias de mejoras de usabilidad
- Análisis de carga cognitiva
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class HeuristicType(Enum):
    """10 Heurísticas de Nielsen para evaluación de usabilidad."""
    VISIBILITY = "visibility_of_system_status"
    MATCH = "match_between_system_and_real_world"
    CONTROL = "user_control_and_freedom"
    CONSISTENCY = "consistency_and_standards"
    ERROR_PREVENTION = "error_prevention"
    RECOGNITION = "recognition_rather_than_recall"
    FLEXIBILITY = "flexibility_and_efficiency"
    AESTHETIC = "aesthetic_and_minimalist_design"
    ERROR_RECOVERY = "help_users_recognize_recover_errors"
    HELP = "help_and_documentation"


class UXIssueSeverity(Enum):
    """Severidad de problemas UX."""
    COSMETIC = "cosmetic"       # Problema estético menor
    MINOR = "minor"             # Problema menor, fácil de superar
    MAJOR = "major"             # Problema mayor, causa frustración
    CATASTROPHIC = "catastrophic"  # Impide completar tarea


class FrictionType(Enum):
    """Tipos de fricción en UX."""
    COGNITIVE = "cognitive"       # Carga mental alta
    INTERACTION = "interaction"   # Demasiados clicks/pasos
    VISUAL = "visual"            # Confusión visual
    EMOTIONAL = "emotional"       # Frustración/ansiedad
    TEMPORAL = "temporal"         # Esperas/demoras


@dataclass
class UXIssue:
    """Representa un problema de UX detectado."""
    id: str
    heuristic: HeuristicType
    severity: UXIssueSeverity
    friction_type: Optional[FrictionType]
    location: str
    title: str
    description: str
    impact: str
    recommendation: str
    user_story: Optional[str] = None
    affected_users: str = "all"
    effort_to_fix: str = "medium"
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'heuristic': self.heuristic.value,
            'severity': self.severity.value,
            'friction_type': self.friction_type.value if self.friction_type else None,
            'location': self.location,
            'title': self.title,
            'description': self.description,
            'impact': self.impact,
            'recommendation': self.recommendation,
            'user_story': self.user_story,
            'affected_users': self.affected_users,
            'effort_to_fix': self.effort_to_fix
        }


@dataclass
class UserFlow:
    """Representa un flujo de usuario."""
    name: str
    description: str
    steps: List[str]
    entry_points: List[str]
    exit_points: List[str]
    happy_path: bool = True
    friction_points: List[str] = field(default_factory=list)
    estimated_time_seconds: int = 0
    cognitive_load: str = "low"  # low, medium, high


@dataclass
class FormAnalysis:
    """Análisis de un formulario."""
    name: str
    location: str
    fields_count: int
    required_fields: int
    field_types: Dict[str, int]
    has_validation: bool
    has_error_messages: bool
    has_help_text: bool
    has_placeholders: bool
    estimated_completion_time: int  # segundos
    issues: List[UXIssue]
    score: float  # 0-100


@dataclass
class MicrointeractionAnalysis:
    """Análisis de microinteracciones."""
    element_type: str
    location: str
    has_hover_state: bool
    has_active_state: bool
    has_focus_state: bool
    has_loading_state: bool
    has_success_feedback: bool
    has_error_feedback: bool
    animation_duration_ms: Optional[int]
    issues: List[str]


@dataclass
class UXAuditReport:
    """Reporte completo de auditoría UX."""
    timestamp: str
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_heuristic: Dict[str, int]
    issues: List[UXIssue]
    user_flows: List[UserFlow]
    forms: List[FormAnalysis]
    microinteractions: List[MicrointeractionAnalysis]
    recommendations: List[str]
    usability_score: float  # 0-100

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'total_issues': self.total_issues,
            'issues_by_severity': self.issues_by_severity,
            'issues_by_heuristic': self.issues_by_heuristic,
            'usability_score': self.usability_score,
            'recommendations': self.recommendations
        }


class UXAnalystAgent:
    """
    Agente UX Analyst - Experto en Experiencia de Usuario

    Analiza y mejora la usabilidad de la aplicación:

    Capacidades:
    - Evaluación heurística (10 heurísticas de Nielsen)
    - Análisis de flujos de usuario
    - Detección de puntos de fricción
    - Análisis de formularios
    - Evaluación de microinteracciones
    - Análisis de feedback visual
    - Sugerencias de mejoras

    Ejemplo de uso:
    ```python
    ux = UXAnalystAgent()

    # Auditoría completa de UX
    report = ux.audit_ux()

    # Analizar un flujo específico
    flow = ux.analyze_user_flow("login")

    # Analizar formularios
    forms = ux.analyze_forms()

    # Evaluación heurística
    issues = ux.heuristic_evaluation()
    ```
    """

    # Patrones de problemas comunes
    FRICTION_PATTERNS = {
        'no_feedback': [
            r'onclick\s*=\s*["\'][^"\']*["\'](?!.*loading)',
            r'@click\s*=\s*["\'][^"\']*["\'](?!.*loading)',
        ],
        'no_error_handling': [
            r'\.catch\s*\(\s*\)',
            r'except\s*:\s*pass',
            r'\.catch\s*\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)',
        ],
        'no_confirmation': [
            r'(delete|remove|reset|clear).*(?!confirm)',
        ],
        'complex_form': [
            r'<form[^>]*>(?:[^<]*<input[^>]*>){10,}',
        ]
    }

    # Tiempo estimado por tipo de campo (segundos)
    FIELD_TIME_ESTIMATE = {
        'text': 5,
        'email': 8,
        'password': 10,
        'number': 4,
        'tel': 8,
        'date': 6,
        'select': 4,
        'checkbox': 2,
        'radio': 2,
        'textarea': 15,
        'file': 12
    }

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente UX Analyst.

        Args:
            project_root: Ruta raíz del proyecto
        """
        self.project_root = Path(project_root)
        self._issue_counter = 0

    def _generate_issue_id(self) -> str:
        """Genera un ID único para un issue."""
        self._issue_counter += 1
        return f"UX-{datetime.now().strftime('%Y%m%d')}-{self._issue_counter:04d}"

    # ========================================
    # EVALUACIÓN HEURÍSTICA
    # ========================================

    def heuristic_evaluation(self) -> List[UXIssue]:
        """
        Realiza una evaluación heurística completa basada en Nielsen.

        Returns:
            Lista de problemas UX encontrados
        """
        issues = []

        # Analizar archivos HTML
        html_files = list(self.project_root.glob("**/*.html"))
        for html_file in html_files:
            issues.extend(self._evaluate_html_file(str(html_file)))

        # Analizar archivos JavaScript
        js_files = list(self.project_root.glob("**/*.js"))
        for js_file in js_files:
            issues.extend(self._evaluate_js_file(str(js_file)))

        return issues

    def _evaluate_html_file(self, file_path: str) -> List[UXIssue]:
        """Evalúa un archivo HTML contra heurísticas."""
        issues = []
        path = Path(file_path)

        if not path.exists():
            return issues

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # H1: Visibility of System Status
            # Verificar indicadores de carga
            if 'loading' not in content.lower() and 'spinner' not in content.lower():
                issues.append(UXIssue(
                    id=self._generate_issue_id(),
                    heuristic=HeuristicType.VISIBILITY,
                    severity=UXIssueSeverity.MAJOR,
                    friction_type=FrictionType.COGNITIVE,
                    location=file_path,
                    title="Sin indicador de carga visible",
                    description="No se detectaron indicadores de carga (loading, spinner). "
                               "Los usuarios no sabrán si el sistema está procesando.",
                    impact="Los usuarios pueden pensar que la aplicación no responde y abandonar.",
                    recommendation="Añade spinners o skeleton screens para operaciones async. "
                                  "Usa aria-busy='true' para accesibilidad."
                ))

            # H3: User Control and Freedom
            # Verificar acciones destructivas sin confirmación
            destructive_pattern = r'(delete|remove|reset|clear|eliminar|borrar)'
            for i, line in enumerate(lines, 1):
                if re.search(destructive_pattern, line, re.IGNORECASE):
                    if 'confirm' not in line.lower() and 'modal' not in line.lower():
                        issues.append(UXIssue(
                            id=self._generate_issue_id(),
                            heuristic=HeuristicType.CONTROL,
                            severity=UXIssueSeverity.MAJOR,
                            friction_type=FrictionType.EMOTIONAL,
                            location=f"{file_path}:{i}",
                            title="Acción destructiva sin confirmación",
                            description="Se detectó una acción destructiva (delete/remove) sin diálogo de confirmación.",
                            impact="Los usuarios pueden perder datos accidentalmente, causando frustración.",
                            recommendation="Añade un modal de confirmación: '¿Estás seguro?' con opción de cancelar. "
                                          "Considera añadir funcionalidad de 'deshacer'."
                        ))

            # H4: Consistency and Standards
            # Verificar botones con estilos inconsistentes
            button_classes = re.findall(r'<button[^>]*class\s*=\s*["\']([^"\']+)["\']', content)
            if button_classes:
                unique_classes = set()
                for classes in button_classes:
                    unique_classes.update(classes.split())

                btn_variants = [c for c in unique_classes if 'btn' in c.lower() or 'button' in c.lower()]
                if len(btn_variants) > 5:
                    issues.append(UXIssue(
                        id=self._generate_issue_id(),
                        heuristic=HeuristicType.CONSISTENCY,
                        severity=UXIssueSeverity.MINOR,
                        friction_type=FrictionType.COGNITIVE,
                        location=file_path,
                        title="Demasiadas variantes de botones",
                        description=f"Se encontraron {len(btn_variants)} variantes de estilos de botón. "
                                   "Esto puede confundir a los usuarios.",
                        impact="Los usuarios no sabrán qué tipo de acción representa cada botón.",
                        recommendation="Estandariza a 3-4 variantes: primary, secondary, danger, ghost. "
                                       "Documenta cuándo usar cada una."
                    ))

            # H5: Error Prevention
            # Verificar formularios sin validación client-side
            forms = re.findall(r'<form[^>]*>(.*?)</form>', content, re.DOTALL | re.IGNORECASE)
            for form in forms:
                if 'required' not in form and 'pattern' not in form:
                    issues.append(UXIssue(
                        id=self._generate_issue_id(),
                        heuristic=HeuristicType.ERROR_PREVENTION,
                        severity=UXIssueSeverity.MAJOR,
                        friction_type=FrictionType.INTERACTION,
                        location=file_path,
                        title="Formulario sin validación client-side",
                        description="El formulario no tiene atributos de validación HTML5 (required, pattern, min, max).",
                        impact="Los usuarios descubrirán errores solo después de enviar, causando frustración.",
                        recommendation="Añade validación HTML5: required, type='email', pattern, min/max. "
                                       "Complementa con validación JavaScript en tiempo real."
                    ))

            # H6: Recognition Rather Than Recall
            # Verificar inputs sin labels o placeholders
            inputs = re.findall(r'<input[^>]*>', content, re.IGNORECASE)
            for inp in inputs:
                input_type = re.search(r'type\s*=\s*["\']([^"\']+)["\']', inp)
                if input_type and input_type.group(1) in ['hidden', 'submit', 'button']:
                    continue

                has_placeholder = 'placeholder=' in inp.lower()
                has_aria = 'aria-label' in inp.lower()

                if not has_placeholder and not has_aria:
                    issues.append(UXIssue(
                        id=self._generate_issue_id(),
                        heuristic=HeuristicType.RECOGNITION,
                        severity=UXIssueSeverity.MINOR,
                        friction_type=FrictionType.COGNITIVE,
                        location=file_path,
                        title="Campo sin pista visual",
                        description="El campo de entrada no tiene placeholder ni label visible.",
                        impact="Los usuarios deben recordar qué información se espera.",
                        recommendation="Añade placeholder con ejemplo: placeholder='ejemplo@email.com'. "
                                       "Mejor aún, usa labels visibles permanentes."
                    ))

            # H8: Aesthetic and Minimalist Design
            # Detectar demasiados elementos en un contenedor
            divs_with_many_children = re.findall(
                r'<div[^>]*>((?:[^<]*<[^/][^>]*>[^<]*</[^>]*>){10,})[^<]*</div>',
                content, re.DOTALL
            )
            if divs_with_many_children:
                issues.append(UXIssue(
                    id=self._generate_issue_id(),
                    heuristic=HeuristicType.AESTHETIC,
                    severity=UXIssueSeverity.MINOR,
                    friction_type=FrictionType.COGNITIVE,
                    location=file_path,
                    title="Posible sobrecarga de información",
                    description="Se detectaron contenedores con muchos elementos hijos (10+). "
                               "Esto puede abrumar al usuario.",
                    impact="Los usuarios pueden perderse o no encontrar lo que buscan.",
                    recommendation="Divide el contenido en secciones claras con headers. "
                                   "Considera usar progressive disclosure (mostrar más al hacer clic)."
                ))

            # H9: Help Users Recognize and Recover from Errors
            # Verificar mensajes de error genéricos
            error_patterns = [
                r'(error|failed|invalid)(?![^<]*class)',
                r'alert\s*\(\s*["\']error',
            ]
            for pattern in error_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        if 'específic' not in line and 'specific' not in line:
                            issues.append(UXIssue(
                                id=self._generate_issue_id(),
                                heuristic=HeuristicType.ERROR_RECOVERY,
                                severity=UXIssueSeverity.MINOR,
                                friction_type=FrictionType.COGNITIVE,
                                location=f"{file_path}:{i}",
                                title="Posible mensaje de error genérico",
                                description="Se detectó un mensaje de error que podría ser genérico.",
                                impact="Los usuarios no sabrán cómo corregir el error.",
                                recommendation="Usa mensajes específicos: 'El email debe tener formato válido' "
                                              "en lugar de 'Error en el campo'."
                            ))
                        break

        except Exception as e:
            logger.error(f"Error evaluando {file_path}: {e}")

        return issues

    def _evaluate_js_file(self, file_path: str) -> List[UXIssue]:
        """Evalúa un archivo JavaScript contra heurísticas."""
        issues = []
        path = Path(file_path)

        if not path.exists() or 'node_modules' in str(path):
            return issues

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Verificar falta de feedback en acciones async
            fetch_pattern = r'fetch\s*\([^)]+\)'
            for i, line in enumerate(lines, 1):
                if re.search(fetch_pattern, line):
                    # Buscar en las siguientes 10 líneas si hay feedback
                    context = '\n'.join(lines[i-1:i+10])
                    if 'loading' not in context.lower() and 'spinner' not in context.lower():
                        issues.append(UXIssue(
                            id=self._generate_issue_id(),
                            heuristic=HeuristicType.VISIBILITY,
                            severity=UXIssueSeverity.MAJOR,
                            friction_type=FrictionType.TEMPORAL,
                            location=f"{file_path}:{i}",
                            title="Fetch sin indicador de carga",
                            description="Se detectó una llamada fetch sin indicador de carga visible.",
                            impact="Los usuarios no sabrán que la operación está en progreso.",
                            recommendation="Muestra un spinner antes del fetch y ocúltalo en finally. "
                                          "Ejemplo: showLoading(); try { await fetch(...) } finally { hideLoading() }"
                        ))

            # Verificar catch vacíos (sin feedback de error)
            empty_catch_pattern = r'\.catch\s*\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)'
            for i, line in enumerate(lines, 1):
                if re.search(empty_catch_pattern, line):
                    issues.append(UXIssue(
                        id=self._generate_issue_id(),
                        heuristic=HeuristicType.ERROR_RECOVERY,
                        severity=UXIssueSeverity.MAJOR,
                        friction_type=FrictionType.COGNITIVE,
                        location=f"{file_path}:{i}",
                        title="Error silenciado sin feedback",
                        description="Se detectó un .catch() vacío que no muestra error al usuario.",
                        impact="Los usuarios no sabrán que algo falló y no podrán tomar acción.",
                        recommendation="Muestra un mensaje de error amigable. "
                                       "Ejemplo: .catch(err => showToast('No se pudo completar la acción'))"
                    ))

            # Verificar timeouts muy largos
            timeout_pattern = r'setTimeout\s*\([^,]+,\s*(\d+)\s*\)'
            for i, line in enumerate(lines, 1):
                match = re.search(timeout_pattern, line)
                if match:
                    delay = int(match.group(1))
                    if delay > 5000:
                        issues.append(UXIssue(
                            id=self._generate_issue_id(),
                            heuristic=HeuristicType.VISIBILITY,
                            severity=UXIssueSeverity.MINOR,
                            friction_type=FrictionType.TEMPORAL,
                            location=f"{file_path}:{i}",
                            title=f"Timeout largo: {delay}ms",
                            description=f"Se detectó un setTimeout de {delay}ms ({delay/1000}s). "
                                       "Las esperas largas pueden frustrar a los usuarios.",
                            impact="Los usuarios pueden pensar que algo no funciona.",
                            recommendation="Si es necesario esperar, muestra un indicador de progreso. "
                                          "Considera usar promesas o callbacks en lugar de timeouts."
                        ))

        except Exception as e:
            logger.error(f"Error evaluando JS {file_path}: {e}")

        return issues

    # ========================================
    # ANÁLISIS DE FORMULARIOS
    # ========================================

    def analyze_forms(self) -> List[FormAnalysis]:
        """
        Analiza todos los formularios del proyecto.

        Returns:
            Lista de análisis de formularios
        """
        forms = []

        html_files = list(self.project_root.glob("**/*.html"))

        for html_file in html_files:
            try:
                content = Path(html_file).read_text(encoding='utf-8')
                form_matches = re.findall(
                    r'<form[^>]*>(.*?)</form>',
                    content,
                    re.DOTALL | re.IGNORECASE
                )

                for i, form_content in enumerate(form_matches):
                    analysis = self._analyze_form(
                        form_content,
                        f"{html_file}:form_{i+1}"
                    )
                    if analysis:
                        forms.append(analysis)

            except Exception as e:
                logger.error(f"Error analizando formularios en {html_file}: {e}")

        return forms

    def _analyze_form(self, form_content: str, location: str) -> Optional[FormAnalysis]:
        """Analiza un formulario individual."""
        issues = []
        field_types = {}

        # Contar campos
        inputs = re.findall(r'<input[^>]*>', form_content, re.IGNORECASE)
        textareas = re.findall(r'<textarea[^>]*>', form_content, re.IGNORECASE)
        selects = re.findall(r'<select[^>]*>', form_content, re.IGNORECASE)

        total_fields = len(inputs) + len(textareas) + len(selects)

        if total_fields == 0:
            return None

        # Clasificar tipos de input
        for inp in inputs:
            inp_type = 'text'
            type_match = re.search(r'type\s*=\s*["\']([^"\']+)["\']', inp, re.IGNORECASE)
            if type_match:
                inp_type = type_match.group(1).lower()
            field_types[inp_type] = field_types.get(inp_type, 0) + 1

        field_types['textarea'] = len(textareas)
        field_types['select'] = len(selects)

        # Contar campos required
        required_count = len(re.findall(r'required', form_content, re.IGNORECASE))

        # Verificar características
        has_validation = bool(re.search(r'(pattern|min=|max=|minlength|maxlength)', form_content))
        has_error_messages = bool(re.search(r'(error|invalid|validation)', form_content, re.IGNORECASE))
        has_help_text = bool(re.search(r'(help|hint|description)', form_content, re.IGNORECASE))
        has_placeholders = bool(re.search(r'placeholder\s*=', form_content, re.IGNORECASE))

        # Estimar tiempo de completación
        estimated_time = 0
        for field_type, count in field_types.items():
            time_per_field = self.FIELD_TIME_ESTIMATE.get(field_type, 5)
            estimated_time += time_per_field * count

        # Detectar problemas
        if total_fields > 10:
            issues.append(UXIssue(
                id=self._generate_issue_id(),
                heuristic=HeuristicType.AESTHETIC,
                severity=UXIssueSeverity.MAJOR,
                friction_type=FrictionType.COGNITIVE,
                location=location,
                title="Formulario muy largo",
                description=f"El formulario tiene {total_fields} campos, lo cual puede abrumar al usuario.",
                impact="Los usuarios pueden abandonar el formulario sin completarlo.",
                recommendation="Divide el formulario en pasos (wizard) o usa progressive disclosure. "
                              "Agrupa campos relacionados y muestra solo los esenciales inicialmente."
            ))

        if not has_validation:
            issues.append(UXIssue(
                id=self._generate_issue_id(),
                heuristic=HeuristicType.ERROR_PREVENTION,
                severity=UXIssueSeverity.MAJOR,
                friction_type=FrictionType.INTERACTION,
                location=location,
                title="Sin validación HTML5",
                description="El formulario no usa atributos de validación HTML5.",
                impact="Los errores se descubren después de enviar, frustrando al usuario.",
                recommendation="Añade: required, pattern, minlength, maxlength, min, max, type='email'."
            ))

        if not has_placeholders and not has_help_text:
            issues.append(UXIssue(
                id=self._generate_issue_id(),
                heuristic=HeuristicType.RECOGNITION,
                severity=UXIssueSeverity.MINOR,
                friction_type=FrictionType.COGNITIVE,
                location=location,
                title="Sin pistas de entrada",
                description="Los campos no tienen placeholders ni texto de ayuda.",
                impact="Los usuarios deben adivinar el formato esperado.",
                recommendation="Añade placeholders con ejemplos: placeholder='ej: 東京都渋谷区...'."
            ))

        # Calcular score
        score = 100
        if total_fields > 10:
            score -= 20
        if not has_validation:
            score -= 25
        if not has_placeholders:
            score -= 10
        if not has_help_text:
            score -= 5
        if not has_error_messages:
            score -= 15
        if required_count == 0 and total_fields > 3:
            score -= 10

        return FormAnalysis(
            name=f"Form at {location}",
            location=location,
            fields_count=total_fields,
            required_fields=required_count,
            field_types=field_types,
            has_validation=has_validation,
            has_error_messages=has_error_messages,
            has_help_text=has_help_text,
            has_placeholders=has_placeholders,
            estimated_completion_time=estimated_time,
            issues=issues,
            score=max(0, score)
        )

    # ========================================
    # ANÁLISIS DE FLUJOS DE USUARIO
    # ========================================

    def analyze_user_flows(self) -> List[UserFlow]:
        """
        Analiza los flujos de usuario principales.

        Returns:
            Lista de flujos de usuario detectados
        """
        flows = []

        # Flujos comunes a detectar
        common_flows = {
            'login': {
                'patterns': ['login', 'signin', 'auth'],
                'steps': ['Abrir página', 'Ingresar credenciales', 'Click en login', 'Verificar acceso'],
                'description': 'Flujo de autenticación de usuario'
            },
            'register': {
                'patterns': ['register', 'signup', 'create.*account'],
                'steps': ['Abrir registro', 'Completar datos', 'Aceptar términos', 'Enviar', 'Verificar email'],
                'description': 'Flujo de registro de nuevo usuario'
            },
            'search': {
                'patterns': ['search', 'buscar', 'filter'],
                'steps': ['Ingresar término', 'Aplicar filtros', 'Ver resultados', 'Seleccionar item'],
                'description': 'Flujo de búsqueda'
            },
            'crud': {
                'patterns': ['create', 'edit', 'delete', 'update'],
                'steps': ['Abrir formulario', 'Completar datos', 'Validar', 'Guardar', 'Ver confirmación'],
                'description': 'Flujo de creación/edición de datos'
            }
        }

        html_files = list(self.project_root.glob("**/*.html"))
        js_files = list(self.project_root.glob("**/*.js"))
        all_files = html_files + js_files

        for flow_name, flow_config in common_flows.items():
            entry_points = []
            friction_points = []

            for file in all_files:
                try:
                    content = Path(file).read_text(encoding='utf-8')

                    for pattern in flow_config['patterns']:
                        if re.search(pattern, content, re.IGNORECASE):
                            entry_points.append(str(file))

                            # Detectar fricción en el flujo
                            if 'loading' not in content.lower():
                                friction_points.append(f"{file}: Sin indicador de carga")
                            if flow_name in ['login', 'register']:
                                if 'error' not in content.lower():
                                    friction_points.append(f"{file}: Sin manejo de errores visible")

                except Exception:
                    pass

            if entry_points:
                # Estimar tiempo basado en pasos
                estimated_time = len(flow_config['steps']) * 10  # 10 segundos por paso

                cognitive_load = 'low'
                if len(flow_config['steps']) > 5:
                    cognitive_load = 'medium'
                if len(flow_config['steps']) > 8 or len(friction_points) > 2:
                    cognitive_load = 'high'

                flows.append(UserFlow(
                    name=flow_name,
                    description=flow_config['description'],
                    steps=flow_config['steps'],
                    entry_points=list(set(entry_points))[:5],
                    exit_points=['Confirmación', 'Error', 'Cancelar'],
                    happy_path=len(friction_points) == 0,
                    friction_points=friction_points,
                    estimated_time_seconds=estimated_time,
                    cognitive_load=cognitive_load
                ))

        return flows

    # ========================================
    # ANÁLISIS DE MICROINTERACCIONES
    # ========================================

    def analyze_microinteractions(self) -> List[MicrointeractionAnalysis]:
        """
        Analiza las microinteracciones del proyecto.

        Returns:
            Lista de análisis de microinteracciones
        """
        interactions = []

        css_files = list(self.project_root.glob("**/*.css"))

        for css_file in css_files:
            try:
                content = Path(css_file).read_text(encoding='utf-8')

                # Detectar estados hover
                hover_matches = re.findall(r'([^{]+):hover\s*\{([^}]+)\}', content)
                for selector, styles in hover_matches:
                    interaction = MicrointeractionAnalysis(
                        element_type=selector.strip().split()[-1],
                        location=str(css_file),
                        has_hover_state=True,
                        has_active_state=':active' in content and selector in content,
                        has_focus_state=':focus' in content and selector in content,
                        has_loading_state=False,
                        has_success_feedback=False,
                        has_error_feedback=False,
                        animation_duration_ms=self._extract_animation_duration(styles),
                        issues=[]
                    )

                    # Verificar si tiene transición suave
                    if 'transition' not in styles and 'animation' not in styles:
                        interaction.issues.append(
                            "El hover no tiene transición suave. Añade: transition: all 0.2s ease"
                        )

                    interactions.append(interaction)

            except Exception as e:
                logger.error(f"Error analizando microinteracciones en {css_file}: {e}")

        return interactions

    def _extract_animation_duration(self, css_content: str) -> Optional[int]:
        """Extrae duración de animación en ms."""
        duration_match = re.search(r'(\d+(?:\.\d+)?)(ms|s)', css_content)
        if duration_match:
            value = float(duration_match.group(1))
            unit = duration_match.group(2)
            if unit == 's':
                return int(value * 1000)
            return int(value)
        return None

    # ========================================
    # AUDITORÍA COMPLETA
    # ========================================

    def audit_ux(self) -> UXAuditReport:
        """
        Realiza una auditoría completa de UX.

        Returns:
            UXAuditReport con todos los hallazgos
        """
        logger.info("🎯 Iniciando auditoría de UX...")

        # Evaluación heurística
        issues = self.heuristic_evaluation()

        # Análisis de formularios
        forms = self.analyze_forms()
        for form in forms:
            issues.extend(form.issues)

        # Análisis de flujos
        flows = self.analyze_user_flows()

        # Análisis de microinteracciones
        microinteractions = self.analyze_microinteractions()

        # Clasificar por severidad
        issues_by_severity = {}
        for issue in issues:
            sev = issue.severity.value
            issues_by_severity[sev] = issues_by_severity.get(sev, 0) + 1

        # Clasificar por heurística
        issues_by_heuristic = {}
        for issue in issues:
            h = issue.heuristic.value
            issues_by_heuristic[h] = issues_by_heuristic.get(h, 0) + 1

        # Calcular score de usabilidad
        usability_score = 100
        usability_score -= issues_by_severity.get('catastrophic', 0) * 25
        usability_score -= issues_by_severity.get('major', 0) * 10
        usability_score -= issues_by_severity.get('minor', 0) * 3
        usability_score -= issues_by_severity.get('cosmetic', 0) * 1
        usability_score = max(0, usability_score)

        # Generar recomendaciones
        recommendations = self._generate_recommendations(issues, forms, flows)

        report = UXAuditReport(
            timestamp=datetime.now().isoformat(),
            total_issues=len(issues),
            issues_by_severity=issues_by_severity,
            issues_by_heuristic=issues_by_heuristic,
            issues=issues,
            user_flows=flows,
            forms=forms,
            microinteractions=microinteractions,
            recommendations=recommendations,
            usability_score=usability_score
        )

        logger.info(f"✅ Auditoría UX completada: {len(issues)} problemas, "
                   f"score: {usability_score}%")

        return report

    def _generate_recommendations(
        self,
        issues: List[UXIssue],
        forms: List[FormAnalysis],
        flows: List[UserFlow]
    ) -> List[str]:
        """Genera recomendaciones basadas en la auditoría."""
        recommendations = []

        # Por heurísticas más afectadas
        heuristic_counts = {}
        for issue in issues:
            h = issue.heuristic.value
            heuristic_counts[h] = heuristic_counts.get(h, 0) + 1

        if heuristic_counts:
            top_heuristic = max(heuristic_counts, key=heuristic_counts.get)
            recommendations.append(
                f"🎯 Prioridad: La heurística '{top_heuristic.replace('_', ' ')}' tiene "
                f"{heuristic_counts[top_heuristic]} problemas. Enfócate en mejorar esta área."
            )

        # Por formularios
        low_score_forms = [f for f in forms if f.score < 70]
        if low_score_forms:
            recommendations.append(
                f"📝 Formularios: {len(low_score_forms)} formularios tienen score bajo (<70). "
                "Añade validación, placeholders y mensajes de error claros."
            )

        # Por flujos con fricción
        friction_flows = [f for f in flows if f.friction_points]
        if friction_flows:
            recommendations.append(
                f"🔄 Flujos: {len(friction_flows)} flujos tienen puntos de fricción. "
                "Revisa indicadores de carga y manejo de errores."
            )

        # Por severidad
        catastrophic = sum(1 for i in issues if i.severity == UXIssueSeverity.CATASTROPHIC)
        if catastrophic:
            recommendations.insert(0,
                f"⚠️ CRÍTICO: {catastrophic} problemas catastróficos que impiden completar tareas. "
                "¡Resolver inmediatamente!"
            )

        # Recomendaciones generales
        if not recommendations:
            recommendations.append(
                "✅ ¡Excelente! La experiencia de usuario está en buen estado. "
                "Continúa testeando con usuarios reales."
            )

        recommendations.append(
            "💡 Tip: Realiza pruebas de usabilidad con usuarios reales para "
            "identificar problemas que el análisis automático no detecta."
        )

        return recommendations


# Instancia singleton
_ux_analyst_instance: Optional[UXAnalystAgent] = None


def get_ux_analyst_agent(project_root: str = ".") -> UXAnalystAgent:
    """Obtiene la instancia global del Agente UX Analyst."""
    global _ux_analyst_instance
    if _ux_analyst_instance is None:
        _ux_analyst_instance = UXAnalystAgent(project_root)
    return _ux_analyst_instance
