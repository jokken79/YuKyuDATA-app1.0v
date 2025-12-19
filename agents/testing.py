"""
Testing Agent - Agente de QA y Testing Automatizado
=====================================================

Experto en calidad y testing:
- Análisis de cobertura de tests
- Detección de código sin tests
- Generación de sugerencias de tests
- Análisis de calidad de tests existentes
- Detección de tests frágiles
- Análisis de test doubles (mocks, stubs)
- Sugerencias de mejora de testabilidad
"""

import logging
import re
import ast
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TestIssueSeverity(Enum):
    """Severidad de problemas de testing."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TestIssueCategory(Enum):
    """Categorías de problemas de testing."""
    COVERAGE = "coverage"
    QUALITY = "quality"
    FRAGILITY = "fragility"
    TESTABILITY = "testability"
    MAINTENANCE = "maintenance"
    MISSING = "missing"


@dataclass
class TestIssue:
    """Representa un problema de testing."""
    id: str
    category: TestIssueCategory
    severity: TestIssueSeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    affected_code: Optional[str]
    suggestion: str
    test_example: Optional[str] = None
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'suggestion': self.suggestion,
            'test_example': self.test_example
        }


@dataclass
class FunctionInfo:
    """Información sobre una función."""
    name: str
    file_path: str
    line_number: int
    params: List[str]
    return_type: Optional[str]
    has_test: bool
    complexity: int
    docstring: Optional[str]


@dataclass
class TestFileInfo:
    """Información sobre un archivo de tests."""
    file_path: str
    test_count: int
    test_names: List[str]
    uses_mocks: bool
    uses_fixtures: bool
    has_setup_teardown: bool
    avg_test_length: float
    longest_test: Tuple[str, int]


@dataclass
class CoverageAnalysis:
    """Análisis de cobertura."""
    total_functions: int
    tested_functions: int
    untested_functions: List[FunctionInfo]
    coverage_percentage: float
    critical_untested: List[FunctionInfo]


@dataclass
class TestSuggestion:
    """Sugerencia de test."""
    target_function: str
    target_file: str
    test_type: str  # unit, integration, e2e
    description: str
    example_code: str
    priority: str  # high, medium, low


@dataclass
class TestingReport:
    """Reporte completo de testing."""
    timestamp: str
    source_files_count: int
    test_files_count: int
    total_tests: int
    issues: List[TestIssue]
    coverage: CoverageAnalysis
    test_files: List[TestFileInfo]
    suggestions: List[TestSuggestion]
    recommendations: List[str]
    testing_score: float  # 0-100

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'source_files_count': self.source_files_count,
            'test_files_count': self.test_files_count,
            'total_tests': self.total_tests,
            'coverage_percentage': self.coverage.coverage_percentage,
            'issues_count': len(self.issues),
            'suggestions_count': len(self.suggestions),
            'testing_score': self.testing_score,
            'recommendations': self.recommendations
        }


class TestingAgent:
    """
    Agente de Testing - Experto en QA

    Analiza y mejora la calidad de los tests:

    Capacidades:
    - Análisis de cobertura (sin ejecutar tests)
    - Detección de código sin tests
    - Análisis de calidad de tests
    - Detección de tests frágiles
    - Generación de sugerencias de tests
    - Análisis de testabilidad del código

    Ejemplo de uso:
    ```python
    qa = TestingAgent()

    # Análisis completo
    report = qa.analyze_testing()

    # Analizar cobertura
    coverage = qa.analyze_coverage()

    # Generar sugerencias de tests
    suggestions = qa.generate_test_suggestions()

    # Analizar calidad de tests
    quality = qa.analyze_test_quality()
    ```
    """

    # Patrones de tests frágiles
    FRAGILE_PATTERNS = {
        'time_dependent': [
            r'datetime\.now\(\)',
            r'time\.time\(\)',
            r'Date\.now\(\)',
        ],
        'order_dependent': [
            r'test_\d+_',  # Tests numerados
        ],
        'external_dependency': [
            r'requests\.(get|post)',
            r'fetch\(',
            r'\.connect\(',
        ],
        'random_values': [
            r'random\.',
            r'uuid\.',
            r'Math\.random\(\)',
        ],
        'sleep_wait': [
            r'time\.sleep\(',
            r'setTimeout\(',
            r'asyncio\.sleep\(',
        ]
    }

    # Patrones de buenas prácticas
    GOOD_PRACTICES = {
        'uses_fixtures': r'@pytest\.fixture|@fixture|setUp\s*\(',
        'uses_parametrize': r'@pytest\.mark\.parametrize|@parameterized',
        'uses_mocks': r'@patch|mock\.|Mock\(|MagicMock',
        'has_assertions': r'assert|expect\(|should\.',
        'has_docstring': r'"""[^"]+"""',
    }

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente de Testing.

        Args:
            project_root: Ruta raíz del proyecto
        """
        self.project_root = Path(project_root)
        self._issue_counter = 0

    def _generate_issue_id(self) -> str:
        """Genera un ID único para un issue."""
        self._issue_counter += 1
        return f"TEST-{datetime.now().strftime('%Y%m%d')}-{self._issue_counter:04d}"

    # ========================================
    # ANÁLISIS DE COBERTURA
    # ========================================

    def analyze_coverage(self) -> CoverageAnalysis:
        """
        Analiza la cobertura de tests (análisis estático).

        Returns:
            CoverageAnalysis con los resultados
        """
        all_functions = []
        tested_functions = set()

        # Obtener todas las funciones del código fuente
        source_files = list(self.project_root.glob("**/*.py"))
        test_files = []

        for file in source_files:
            if 'venv' in str(file) or '__pycache__' in str(file):
                continue

            if 'test' in file.name.lower():
                test_files.append(file)
                continue

            functions = self._extract_functions(file)
            all_functions.extend(functions)

        # Analizar archivos de test para ver qué funciones se testean
        for test_file in test_files:
            try:
                content = test_file.read_text(encoding='utf-8')

                # Extraer nombres de funciones testeadas (heurística)
                # Buscar imports y usos
                imports = re.findall(r'from\s+\S+\s+import\s+(\w+)', content)
                for imp in imports:
                    tested_functions.add(imp)

                # Buscar llamadas a funciones
                calls = re.findall(r'(\w+)\s*\(', content)
                for call in calls:
                    tested_functions.add(call)

            except Exception as e:
                logger.warning(f"Error analizando test {test_file}: {e}")

        # Marcar funciones testeadas
        for func in all_functions:
            if func.name in tested_functions:
                func.has_test = True

        # Calcular estadísticas
        tested_count = sum(1 for f in all_functions if f.has_test)
        untested = [f for f in all_functions if not f.has_test]

        # Identificar críticas sin test (públicas, complejas)
        critical_untested = [
            f for f in untested
            if not f.name.startswith('_') and f.complexity > 3
        ]

        coverage_pct = (tested_count / len(all_functions) * 100) if all_functions else 0

        return CoverageAnalysis(
            total_functions=len(all_functions),
            tested_functions=tested_count,
            untested_functions=untested,
            coverage_percentage=coverage_pct,
            critical_untested=critical_untested[:20]
        )

    def _extract_functions(self, file_path: Path) -> List[FunctionInfo]:
        """Extrae información de funciones de un archivo Python."""
        functions = []

        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calcular complejidad simplificada
                    complexity = self._calculate_complexity(node)

                    # Obtener parámetros
                    params = [arg.arg for arg in node.args.args]

                    # Obtener docstring
                    docstring = ast.get_docstring(node)

                    functions.append(FunctionInfo(
                        name=node.name,
                        file_path=str(file_path),
                        line_number=node.lineno,
                        params=params,
                        return_type=None,  # Podría extraerse de annotations
                        has_test=False,
                        complexity=complexity,
                        docstring=docstring
                    ))

        except Exception as e:
            logger.warning(f"Error extrayendo funciones de {file_path}: {e}")

        return functions

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calcula complejidad ciclomática simplificada."""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    # ========================================
    # ANÁLISIS DE CALIDAD DE TESTS
    # ========================================

    def analyze_test_quality(self) -> Tuple[List[TestIssue], List[TestFileInfo]]:
        """
        Analiza la calidad de los tests existentes.

        Returns:
            Tupla (issues, test_files_info)
        """
        issues = []
        test_files_info = []

        test_files = list(self.project_root.glob("**/test_*.py"))
        test_files.extend(self.project_root.glob("**/*_test.py"))
        test_files.extend(self.project_root.glob("**/tests/*.py"))

        for test_file in test_files:
            if 'venv' in str(test_file) or '__pycache__' in str(test_file):
                continue

            file_issues, file_info = self._analyze_test_file(test_file)
            issues.extend(file_issues)
            if file_info:
                test_files_info.append(file_info)

        return issues, test_files_info

    def _analyze_test_file(self, file_path: Path) -> Tuple[List[TestIssue], Optional[TestFileInfo]]:
        """Analiza un archivo de test individual."""
        issues = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Contar tests
            test_pattern = r'def\s+(test_\w+)\s*\('
            test_matches = re.findall(test_pattern, content)
            test_count = len(test_matches)

            if test_count == 0:
                return issues, None

            # Verificar buenas prácticas
            uses_mocks = bool(re.search(self.GOOD_PRACTICES['uses_mocks'], content))
            uses_fixtures = bool(re.search(self.GOOD_PRACTICES['uses_fixtures'], content))
            has_setup = bool(re.search(r'def\s+setUp\s*\(|@pytest\.fixture', content))

            # Detectar tests frágiles
            for fragile_type, patterns in self.FRAGILE_PATTERNS.items():
                for pattern in patterns:
                    matches = list(re.finditer(pattern, content))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(TestIssue(
                            id=self._generate_issue_id(),
                            category=TestIssueCategory.FRAGILITY,
                            severity=TestIssueSeverity.MEDIUM,
                            title=f"Test frágil: {fragile_type}",
                            description=f"Se detectó un patrón que puede hacer el test frágil: {fragile_type}",
                            file_path=str(file_path),
                            line_number=line_num,
                            affected_code=lines[line_num-1].strip()[:60],
                            suggestion=self._get_fragile_suggestion(fragile_type)
                        ))

            # Verificar assertions
            for test_name in test_matches:
                test_pattern = rf'def\s+{test_name}\s*\([^)]*\):([\s\S]*?)(?=def\s+\w|$)'
                test_match = re.search(test_pattern, content)
                if test_match:
                    test_body = test_match.group(1)
                    if not re.search(r'assert|expect|should', test_body):
                        issues.append(TestIssue(
                            id=self._generate_issue_id(),
                            category=TestIssueCategory.QUALITY,
                            severity=TestIssueSeverity.HIGH,
                            title=f"Test sin assertions: {test_name}",
                            description="El test no tiene assertions explícitas.",
                            file_path=str(file_path),
                            line_number=None,
                            affected_code=test_name,
                            suggestion="Añade assertions para verificar el comportamiento esperado. "
                                       "Un test sin assertions no verifica nada."
                        ))

            # Calcular longitudes de tests
            test_lengths = []
            for test_name in test_matches:
                test_pattern = rf'def\s+{test_name}\s*\([^)]*\):([\s\S]*?)(?=def\s+\w|$)'
                test_match = re.search(test_pattern, content)
                if test_match:
                    test_body = test_match.group(1)
                    length = len([l for l in test_body.split('\n') if l.strip()])
                    test_lengths.append((test_name, length))

            avg_length = sum(l for _, l in test_lengths) / len(test_lengths) if test_lengths else 0
            longest = max(test_lengths, key=lambda x: x[1]) if test_lengths else ('', 0)

            # Tests muy largos
            if longest[1] > 50:
                issues.append(TestIssue(
                    id=self._generate_issue_id(),
                    category=TestIssueCategory.MAINTENANCE,
                    severity=TestIssueSeverity.LOW,
                    title=f"Test muy largo: {longest[0]} ({longest[1]} líneas)",
                    description="Los tests largos son difíciles de mantener y entender.",
                    file_path=str(file_path),
                    line_number=None,
                    affected_code=longest[0],
                    suggestion="Divide el test en tests más pequeños y enfocados. "
                              "Usa fixtures para reducir código repetido."
                ))

            file_info = TestFileInfo(
                file_path=str(file_path),
                test_count=test_count,
                test_names=test_matches,
                uses_mocks=uses_mocks,
                uses_fixtures=uses_fixtures,
                has_setup_teardown=has_setup,
                avg_test_length=avg_length,
                longest_test=longest
            )

            return issues, file_info

        except Exception as e:
            logger.warning(f"Error analizando {file_path}: {e}")
            return issues, None

    def _get_fragile_suggestion(self, fragile_type: str) -> str:
        """Obtiene sugerencia para un tipo de test frágil."""
        suggestions = {
            'time_dependent': "Usa freezegun o mock para congelar el tiempo: "
                             "@freeze_time('2024-01-01')",
            'order_dependent': "Los tests no deben depender del orden. "
                              "Usa fixtures con scope apropiado.",
            'external_dependency': "Mockea las dependencias externas: "
                                  "@patch('requests.get') o usa responses/httpretty",
            'random_values': "Fija el seed para reproducibilidad: random.seed(42) "
                            "o mockea el generador.",
            'sleep_wait': "Evita sleeps en tests. Usa mocks de tiempo "
                         "o polling con timeout corto."
        }
        return suggestions.get(fragile_type, "Revisa este patrón para evitar tests frágiles.")

    # ========================================
    # GENERACIÓN DE SUGERENCIAS
    # ========================================

    def generate_test_suggestions(self) -> List[TestSuggestion]:
        """
        Genera sugerencias de tests para código sin cobertura.

        Returns:
            Lista de sugerencias de tests
        """
        suggestions = []
        coverage = self.analyze_coverage()

        # Priorizar funciones críticas sin test
        for func in coverage.critical_untested[:10]:
            suggestion = self._generate_test_for_function(func)
            if suggestion:
                suggestions.append(suggestion)

        # Sugerir tests de integración para endpoints
        main_file = self.project_root / "main.py"
        if main_file.exists():
            api_suggestions = self._suggest_api_tests(main_file)
            suggestions.extend(api_suggestions)

        return suggestions

    def _generate_test_for_function(self, func: FunctionInfo) -> Optional[TestSuggestion]:
        """Genera una sugerencia de test para una función."""
        # Determinar tipo de test
        test_type = "unit"
        if 'api' in func.name.lower() or 'endpoint' in func.name.lower():
            test_type = "integration"
        if 'db' in func.name.lower() or 'database' in func.name.lower():
            test_type = "integration"

        # Generar ejemplo de código
        params_str = ", ".join(func.params) if func.params else ""
        mock_params = ", ".join([f"mock_{p}" for p in func.params]) if func.params else ""

        example = f'''
def test_{func.name}_success():
    """Test that {func.name} works correctly."""
    # Arrange
    {mock_params if func.params else "# No params needed"}

    # Act
    result = {func.name}({params_str})

    # Assert
    assert result is not None
    # TODO: Add specific assertions


def test_{func.name}_edge_case():
    """Test {func.name} with edge case."""
    # Test con valores límite o casos especiales
    pass
'''

        priority = "high" if func.complexity > 5 else "medium" if func.complexity > 2 else "low"

        return TestSuggestion(
            target_function=func.name,
            target_file=func.file_path,
            test_type=test_type,
            description=f"Función {'compleja' if func.complexity > 5 else 'sin cobertura'} "
                       f"que necesita tests ({func.complexity} complejidad ciclomática)",
            example_code=example,
            priority=priority
        )

    def _suggest_api_tests(self, main_file: Path) -> List[TestSuggestion]:
        """Sugiere tests para endpoints de API."""
        suggestions = []

        try:
            content = main_file.read_text(encoding='utf-8')

            # Detectar endpoints
            endpoint_pattern = r'@app\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']'
            endpoints = re.findall(endpoint_pattern, content)

            for method, path in endpoints[:5]:
                example = f'''
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_{method}_{path.replace("/", "_").strip("_")}():
    """Test {method.upper()} {path}."""
    response = client.{method}("{path}")

    assert response.status_code == 200
    # Verificar estructura de respuesta
    data = response.json()
    assert "data" in data or "message" in data


def test_{method}_{path.replace("/", "_").strip("_")}_error():
    """Test error handling for {method.upper()} {path}."""
    # Test con datos inválidos
    response = client.{method}("{path}", json={{"invalid": "data"}})

    assert response.status_code in [400, 422]
'''

                suggestions.append(TestSuggestion(
                    target_function=f"{method.upper()} {path}",
                    target_file=str(main_file),
                    test_type="integration",
                    description=f"Endpoint API que necesita tests de integración",
                    example_code=example,
                    priority="high"
                ))

        except Exception as e:
            logger.warning(f"Error analizando endpoints: {e}")

        return suggestions

    # ========================================
    # ANÁLISIS DE TESTABILIDAD
    # ========================================

    def analyze_testability(self) -> List[TestIssue]:
        """
        Analiza la testabilidad del código fuente.

        Returns:
            Lista de problemas de testabilidad
        """
        issues = []

        source_files = list(self.project_root.glob("**/*.py"))

        for file in source_files:
            if 'venv' in str(file) or '__pycache__' in str(file) or 'test' in file.name.lower():
                continue

            try:
                content = file.read_text(encoding='utf-8')
                lines = content.split('\n')

                # Detectar dependencias hardcodeadas
                hardcoded_patterns = [
                    (r'open\s*\(["\'][^"\']+["\']', "archivo hardcodeado"),
                    (r'connect\s*\(["\'][^"\']+["\']', "conexión hardcodeada"),
                    (r'requests\.(get|post)\s*\(["\'][^"\']+["\']', "URL hardcodeada"),
                ]

                for pattern, desc in hardcoded_patterns:
                    matches = list(re.finditer(pattern, content))
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        issues.append(TestIssue(
                            id=self._generate_issue_id(),
                            category=TestIssueCategory.TESTABILITY,
                            severity=TestIssueSeverity.MEDIUM,
                            title=f"Dependencia hardcodeada: {desc}",
                            description="Las dependencias hardcodeadas son difíciles de mockear en tests.",
                            file_path=str(file),
                            line_number=line_num,
                            affected_code=lines[line_num-1].strip()[:60],
                            suggestion="Inyecta la dependencia como parámetro. "
                                       "Ejemplo: def process(file_path: str) en lugar de path fijo."
                        ))

                # Detectar funciones muy largas (difíciles de testear)
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if hasattr(node, 'end_lineno'):
                            length = node.end_lineno - node.lineno
                            if length > 100:
                                issues.append(TestIssue(
                                    id=self._generate_issue_id(),
                                    category=TestIssueCategory.TESTABILITY,
                                    severity=TestIssueSeverity.LOW,
                                    title=f"Función muy larga: {node.name} ({length} líneas)",
                                    description="Las funciones largas son difíciles de testear completamente.",
                                    file_path=str(file),
                                    line_number=node.lineno,
                                    affected_code=node.name,
                                    suggestion="Divide la función en funciones más pequeñas "
                                               "con responsabilidades únicas. Cada una será más fácil de testear."
                                ))

                # Detectar uso de globals
                if re.search(r'\bglobal\s+\w+', content):
                    issues.append(TestIssue(
                        id=self._generate_issue_id(),
                        category=TestIssueCategory.TESTABILITY,
                        severity=TestIssueSeverity.MEDIUM,
                        title="Uso de variables globales",
                        description="Las variables globales hacen los tests impredecibles.",
                        file_path=str(file),
                        line_number=None,
                        affected_code=None,
                        suggestion="Pasa el estado como parámetro o usa inyección de dependencias. "
                                   "Evita modificar estado global en funciones."
                    ))

            except Exception as e:
                logger.warning(f"Error analizando testabilidad de {file}: {e}")

        return issues

    # ========================================
    # ANÁLISIS COMPLETO
    # ========================================

    def analyze_testing(self) -> TestingReport:
        """
        Realiza un análisis completo de testing.

        Returns:
            TestingReport con todos los hallazgos
        """
        logger.info("🧪 Iniciando análisis de testing...")

        all_issues = []

        # Análisis de cobertura
        coverage = self.analyze_coverage()

        # Análisis de calidad de tests
        quality_issues, test_files = self.analyze_test_quality()
        all_issues.extend(quality_issues)

        # Análisis de testabilidad
        testability_issues = self.analyze_testability()
        all_issues.extend(testability_issues)

        # Generar sugerencias
        suggestions = self.generate_test_suggestions()

        # Issues por cobertura baja
        if coverage.coverage_percentage < 50:
            all_issues.append(TestIssue(
                id=self._generate_issue_id(),
                category=TestIssueCategory.COVERAGE,
                severity=TestIssueSeverity.HIGH,
                title=f"Cobertura baja: {coverage.coverage_percentage:.1f}%",
                description="Menos del 50% de las funciones tienen tests asociados.",
                file_path="proyecto completo",
                line_number=None,
                affected_code=None,
                suggestion="Prioriza añadir tests para funciones críticas. "
                           "Objetivo recomendado: 80%+ cobertura."
            ))

        # Contar archivos
        source_files = len([f for f in self.project_root.glob("**/*.py")
                           if 'venv' not in str(f) and 'test' not in f.name.lower()])
        test_files_count = len(test_files)
        total_tests = sum(tf.test_count for tf in test_files)

        # Calcular score
        score = 50  # Base

        # Bonus por cobertura
        score += min(30, coverage.coverage_percentage * 0.3)

        # Penalizar por issues
        for issue in all_issues:
            if issue.severity == TestIssueSeverity.HIGH:
                score -= 5
            elif issue.severity == TestIssueSeverity.MEDIUM:
                score -= 2

        # Bonus por buenas prácticas
        if any(tf.uses_fixtures for tf in test_files):
            score += 5
        if any(tf.uses_mocks for tf in test_files):
            score += 5

        score = max(0, min(100, score))

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            all_issues, coverage, test_files, suggestions
        )

        report = TestingReport(
            timestamp=datetime.now().isoformat(),
            source_files_count=source_files,
            test_files_count=test_files_count,
            total_tests=total_tests,
            issues=all_issues,
            coverage=coverage,
            test_files=test_files,
            suggestions=suggestions,
            recommendations=recommendations,
            testing_score=score
        )

        logger.info(f"✅ Análisis completado: {total_tests} tests, "
                   f"cobertura: {coverage.coverage_percentage:.1f}%, score: {score}%")

        return report

    def _generate_recommendations(
        self,
        issues: List[TestIssue],
        coverage: CoverageAnalysis,
        test_files: List[TestFileInfo],
        suggestions: List[TestSuggestion]
    ) -> List[str]:
        """Genera recomendaciones de testing."""
        recs = []

        # Por cobertura
        if coverage.coverage_percentage < 50:
            recs.append(
                f"📊 Cobertura: {coverage.coverage_percentage:.1f}% es bajo. "
                f"Hay {len(coverage.untested_functions)} funciones sin tests. "
                "Objetivo: 80%+."
            )

        # Por funciones críticas
        if coverage.critical_untested:
            recs.append(
                f"🎯 Prioridad: {len(coverage.critical_untested)} funciones críticas sin tests. "
                "Enfócate en testear estas primero."
            )

        # Por tests frágiles
        fragile = [i for i in issues if i.category == TestIssueCategory.FRAGILITY]
        if fragile:
            recs.append(
                f"⚠️ Tests frágiles: {len(fragile)} tests pueden fallar intermitentemente. "
                "Mockea tiempo, random y dependencias externas."
            )

        # Por calidad
        quality = [i for i in issues if i.category == TestIssueCategory.QUALITY]
        if quality:
            recs.append(
                f"✏️ Calidad: {len(quality)} tests tienen problemas. "
                "Asegúrate de que todos los tests tengan assertions claras."
            )

        # Por testabilidad
        testability = [i for i in issues if i.category == TestIssueCategory.TESTABILITY]
        if testability:
            recs.append(
                f"🔧 Testabilidad: {len(testability)} problemas en el código. "
                "Refactoriza para facilitar el testing."
            )

        # Sugerencias
        if suggestions:
            high_priority = [s for s in suggestions if s.priority == "high"]
            recs.append(
                f"💡 Sugerencias: {len(high_priority)} tests de alta prioridad sugeridos. "
                "Revisa las sugerencias generadas."
            )

        # Buenas prácticas
        uses_fixtures = any(tf.uses_fixtures for tf in test_files)
        uses_mocks = any(tf.uses_mocks for tf in test_files)

        if not uses_fixtures:
            recs.append(
                "🔄 Fixtures: No se detectaron fixtures. "
                "Usa @pytest.fixture para reducir código repetido."
            )

        if not uses_mocks:
            recs.append(
                "🎭 Mocks: No se detectaron mocks. "
                "Usa unittest.mock para aislar tests de dependencias externas."
            )

        if not recs:
            recs.append(
                "✅ ¡Excelente! El testing está en buen estado. "
                "Continúa añadiendo tests para nuevas funcionalidades."
            )

        return recs


# Instancia singleton
_testing_instance: Optional[TestingAgent] = None


def get_testing_agent(project_root: str = ".") -> TestingAgent:
    """Obtiene la instancia global del Agente de Testing."""
    global _testing_instance
    if _testing_instance is None:
        _testing_instance = TestingAgent(project_root)
    return _testing_instance
