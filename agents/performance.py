"""
Performance Agent - Agente de Optimización de Rendimiento
==========================================================

Experto en análisis y optimización de rendimiento:
- Detección de queries N+1
- Análisis de complejidad algorítmica
- Detección de memory leaks
- Análisis de bundle size (JS)
- Optimización de assets
- Análisis de carga de página
- Sugerencias de caché
- Profiling de funciones
"""

import logging
import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceIssueSeverity(Enum):
    """Severidad de problemas de rendimiento."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceCategory(Enum):
    """Categorías de problemas de rendimiento."""
    DATABASE = "database"
    ALGORITHM = "algorithm"
    MEMORY = "memory"
    NETWORK = "network"
    ASSETS = "assets"
    RENDERING = "rendering"
    CACHING = "caching"
    BUNDLE = "bundle"


@dataclass
class PerformanceIssue:
    """Representa un problema de rendimiento."""
    id: str
    category: PerformanceCategory
    severity: PerformanceIssueSeverity
    title: str
    description: str
    file_path: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    impact: str
    optimization: str
    estimated_improvement: str
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
            'impact': self.impact,
            'optimization': self.optimization,
            'estimated_improvement': self.estimated_improvement
        }


@dataclass
class DatabaseMetrics:
    """Métricas de base de datos."""
    total_queries: int
    queries_without_index: List[str]
    potential_n_plus_1: List[str]
    slow_query_patterns: List[str]
    missing_indexes: List[str]


@dataclass
class BundleMetrics:
    """Métricas de bundle JavaScript."""
    total_js_files: int
    total_js_size_kb: float
    total_css_files: int
    total_css_size_kb: float
    largest_files: List[Tuple[str, float]]
    unused_imports: List[str]
    duplicate_code_patterns: List[str]


@dataclass
class AssetMetrics:
    """Métricas de assets."""
    total_images: int
    total_images_size_mb: float
    unoptimized_images: List[str]
    large_images: List[Tuple[str, float]]
    missing_lazy_load: int


@dataclass
class PerformanceReport:
    """Reporte completo de rendimiento."""
    timestamp: str
    files_analyzed: int
    total_issues: int
    issues_by_category: Dict[str, int]
    issues: List[PerformanceIssue]
    database_metrics: DatabaseMetrics
    bundle_metrics: BundleMetrics
    asset_metrics: AssetMetrics
    recommendations: List[str]
    performance_score: float  # 0-100

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'files_analyzed': self.files_analyzed,
            'total_issues': self.total_issues,
            'issues_by_category': self.issues_by_category,
            'performance_score': self.performance_score,
            'recommendations': self.recommendations
        }


class PerformanceAgent:
    """
    Agente de Performance - Experto en Optimización

    Analiza y optimiza el rendimiento de la aplicación:

    Capacidades:
    - Detección de queries N+1
    - Análisis de complejidad O(n²)+
    - Detección de memory leaks
    - Análisis de bundle size
    - Optimización de imágenes
    - Sugerencias de caché
    - Análisis de loops ineficientes

    Ejemplo de uso:
    ```python
    perf = PerformanceAgent()

    # Análisis completo
    report = perf.analyze_performance()

    # Analizar queries
    db_issues = perf.analyze_database_performance()

    # Analizar bundle
    bundle = perf.analyze_bundle_size()

    # Analizar assets
    assets = perf.analyze_assets()
    ```
    """

    # Patrones de problemas de rendimiento
    PERFORMANCE_PATTERNS = {
        'n_plus_1': [
            r'for\s+\w+\s+in\s+\w+:.*?(?:execute|query|select|find)',
            r'\.forEach\s*\([^)]*\)\s*{[^}]*fetch',
        ],
        'nested_loops': [
            r'for\s+\w+\s+in\s+\w+:[\s\S]*?for\s+\w+\s+in\s+\w+:',
            r'\.forEach\s*\([^}]*\.forEach\s*\(',
        ],
        'inefficient_string': [
            r'\+=\s*["\'][^"\']*["\']',  # Concatenación en loop
            r'str\s*\([^)]+\)\s*\+\s*str',
        ],
        'blocking_io': [
            r'(?<!async\s)def\s+\w+.*?\.read\s*\(',
            r'requests\.(?:get|post)\s*\(',  # Sin async
        ],
        'memory_leak': [
            r'global\s+\w+.*?=\s*\[\]',  # Listas globales que crecen
            r'setInterval\s*\([^)]+\)',  # Intervals sin cleanup
        ],
        'no_cache': [
            r'def\s+get_\w+.*?return\s+.*?query',  # Getters sin cache
        ]
    }

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente de Performance.

        Args:
            project_root: Ruta raíz del proyecto
        """
        self.project_root = Path(project_root)
        self._issue_counter = 0

    def _generate_issue_id(self) -> str:
        """Genera un ID único para un issue."""
        self._issue_counter += 1
        return f"PERF-{datetime.now().strftime('%Y%m%d')}-{self._issue_counter:04d}"

    # ========================================
    # ANÁLISIS DE BASE DE DATOS
    # ========================================

    def analyze_database_performance(self) -> Tuple[List[PerformanceIssue], DatabaseMetrics]:
        """
        Analiza el rendimiento de las operaciones de base de datos.

        Returns:
            Tupla (issues, metrics)
        """
        issues = []
        queries_without_index = []
        potential_n_plus_1 = []
        slow_patterns = []
        missing_indexes = []
        total_queries = 0

        py_files = list(self.project_root.glob("**/*.py"))

        for py_file in py_files:
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                content = Path(py_file).read_text(encoding='utf-8')
                lines = content.split('\n')

                # Detectar N+1
                for i, line in enumerate(lines, 1):
                    # Query en loop
                    if re.search(r'for\s+\w+\s+in', line):
                        # Buscar query en las siguientes 5 líneas
                        context = '\n'.join(lines[i-1:i+5])
                        if re.search(r'(execute|query|select|find|get_)', context, re.IGNORECASE):
                            potential_n_plus_1.append(f"{py_file}:{i}")
                            issues.append(PerformanceIssue(
                                id=self._generate_issue_id(),
                                category=PerformanceCategory.DATABASE,
                                severity=PerformanceIssueSeverity.HIGH,
                                title="Posible Query N+1",
                                description="Se detectó una query dentro de un loop, lo cual puede "
                                           "generar N+1 queries a la base de datos.",
                                file_path=str(py_file),
                                line_number=i,
                                code_snippet=line.strip()[:80],
                                impact="Puede multiplicar las queries por el número de iteraciones, "
                                      "causando lentitud severa.",
                                optimization="Usa JOINs o batch queries. Ejemplo: "
                                            "SELECT * FROM t WHERE id IN (...) en lugar de queries individuales.",
                                estimated_improvement="10x-100x mejora en tiempo de respuesta"
                            ))

                # Detectar SELECT *
                select_star = re.findall(r'SELECT\s+\*\s+FROM', content, re.IGNORECASE)
                for match in select_star:
                    slow_patterns.append(f"SELECT * en {py_file}")
                    total_queries += 1

                # Detectar queries sin WHERE
                select_all = re.findall(r'SELECT\s+.+\s+FROM\s+\w+(?!\s+WHERE)', content, re.IGNORECASE)
                for match in select_all:
                    if 'LIMIT' not in match.upper():
                        queries_without_index.append(f"Query sin filtro en {py_file}")
                        total_queries += 1

                # Detectar tablas sin índice potencial
                if 'CREATE TABLE' in content:
                    tables = re.findall(r'CREATE TABLE\s+(\w+)', content, re.IGNORECASE)
                    for table in tables:
                        if f'CREATE INDEX' not in content or table not in content:
                            missing_indexes.append(table)

            except Exception as e:
                logger.warning(f"Error analizando {py_file}: {e}")

        # Issue por SELECT *
        if slow_patterns:
            issues.append(PerformanceIssue(
                id=self._generate_issue_id(),
                category=PerformanceCategory.DATABASE,
                severity=PerformanceIssueSeverity.MEDIUM,
                title=f"SELECT * detectado ({len(slow_patterns)} casos)",
                description="SELECT * trae todas las columnas, incluyendo las que no necesitas.",
                file_path="múltiples archivos",
                line_number=None,
                code_snippet=None,
                impact="Aumenta el tráfico de red y uso de memoria innecesariamente.",
                optimization="Especifica solo las columnas necesarias: SELECT id, name FROM users.",
                estimated_improvement="20-50% mejora en memoria y tiempo"
            ))

        metrics = DatabaseMetrics(
            total_queries=total_queries,
            queries_without_index=queries_without_index,
            potential_n_plus_1=potential_n_plus_1,
            slow_query_patterns=slow_patterns,
            missing_indexes=missing_indexes
        )

        return issues, metrics

    # ========================================
    # ANÁLISIS DE CÓDIGO
    # ========================================

    def analyze_code_performance(self) -> List[PerformanceIssue]:
        """
        Analiza el código para problemas de rendimiento algorítmico.

        Returns:
            Lista de problemas encontrados
        """
        issues = []

        py_files = list(self.project_root.glob("**/*.py"))
        js_files = list(self.project_root.glob("**/*.js"))

        all_files = [(f, 'python') for f in py_files] + [(f, 'javascript') for f in js_files]

        for file_path, lang in all_files:
            if 'venv' in str(file_path) or 'node_modules' in str(file_path):
                continue
            if '__pycache__' in str(file_path):
                continue

            try:
                content = Path(file_path).read_text(encoding='utf-8')
                lines = content.split('\n')

                # Detectar loops anidados (O(n²))
                nested_loop_pattern = r'for\s+\w+\s+in\s+\w+:[\s\S]*?for\s+\w+\s+in\s+\w+:'
                if re.search(nested_loop_pattern, content):
                    issues.append(PerformanceIssue(
                        id=self._generate_issue_id(),
                        category=PerformanceCategory.ALGORITHM,
                        severity=PerformanceIssueSeverity.MEDIUM,
                        title="Loop anidado detectado (O(n²))",
                        description="Los loops anidados tienen complejidad cuadrática, "
                                   "lo cual puede ser muy lento con datasets grandes.",
                        file_path=str(file_path),
                        line_number=None,
                        code_snippet=None,
                        impact="Con 1000 elementos, ejecutará 1,000,000 iteraciones.",
                        optimization="Considera usar un diccionario/set para lookup O(1), "
                                    "o algoritmos más eficientes como hash maps.",
                        estimated_improvement="Potencialmente 100x+ mejora"
                    ))

                # Detectar concatenación de strings en loop
                for i, line in enumerate(lines, 1):
                    if re.search(r'\+=\s*["\']', line) and 'for' in '\n'.join(lines[max(0,i-5):i]):
                        issues.append(PerformanceIssue(
                            id=self._generate_issue_id(),
                            category=PerformanceCategory.MEMORY,
                            severity=PerformanceIssueSeverity.MEDIUM,
                            title="Concatenación de strings en loop",
                            description="Concatenar strings con += en un loop es O(n²) en memoria.",
                            file_path=str(file_path),
                            line_number=i,
                            code_snippet=line.strip()[:80],
                            impact="Crea nuevos objetos string en cada iteración.",
                            optimization="Usa una lista y ''.join() al final: "
                                        "parts = []; for x in y: parts.append(x); result = ''.join(parts)",
                            estimated_improvement="10x mejora para strings grandes"
                        ))
                        break  # Solo reportar una vez por archivo

                # Detectar I/O síncrono
                sync_io_pattern = r'(?<!async\s)def\s+\w+.*?(?:\.read|\.write|requests\.)'
                if lang == 'python' and re.search(sync_io_pattern, content, re.DOTALL):
                    issues.append(PerformanceIssue(
                        id=self._generate_issue_id(),
                        category=PerformanceCategory.NETWORK,
                        severity=PerformanceIssueSeverity.MEDIUM,
                        title="I/O síncrono detectado",
                        description="Las operaciones de I/O síncronas bloquean el event loop.",
                        file_path=str(file_path),
                        line_number=None,
                        code_snippet=None,
                        impact="Reduce el throughput del servidor significativamente.",
                        optimization="Usa async/await con aiohttp, aiofiles o httpx async.",
                        estimated_improvement="2x-10x mejora en concurrencia"
                    ))

                # Detectar global mutable (memory leak potential)
                if re.search(r'^\s*\w+\s*=\s*\[\s*\]', content, re.MULTILINE):
                    if '.append' in content:
                        issues.append(PerformanceIssue(
                            id=self._generate_issue_id(),
                            category=PerformanceCategory.MEMORY,
                            severity=PerformanceIssueSeverity.LOW,
                            title="Lista global mutable",
                            description="Las listas globales que se modifican pueden crecer sin límite.",
                            file_path=str(file_path),
                            line_number=None,
                            code_snippet=None,
                            impact="Posible memory leak si no se limpian periódicamente.",
                            optimization="Usa collections.deque con maxlen, o limpia periódicamente. "
                                        "Considera mover a una base de datos.",
                            estimated_improvement="Previene memory leak"
                        ))

            except Exception as e:
                logger.warning(f"Error analizando {file_path}: {e}")

        return issues

    # ========================================
    # ANÁLISIS DE BUNDLE
    # ========================================

    def analyze_bundle_size(self) -> Tuple[List[PerformanceIssue], BundleMetrics]:
        """
        Analiza el tamaño del bundle JavaScript y CSS.

        Returns:
            Tupla (issues, metrics)
        """
        issues = []
        largest_files = []
        unused_imports = []
        duplicate_patterns = []

        js_files = list(self.project_root.glob("**/*.js"))
        css_files = list(self.project_root.glob("**/*.css"))

        # Filtrar node_modules y otros
        js_files = [f for f in js_files if 'node_modules' not in str(f)]
        css_files = [f for f in css_files if 'node_modules' not in str(f)]

        total_js_size = 0
        total_css_size = 0

        # Analizar JS
        for js_file in js_files:
            try:
                size_kb = js_file.stat().st_size / 1024
                total_js_size += size_kb
                largest_files.append((str(js_file), size_kb))

                # Detectar archivos muy grandes
                if size_kb > 100:
                    issues.append(PerformanceIssue(
                        id=self._generate_issue_id(),
                        category=PerformanceCategory.BUNDLE,
                        severity=PerformanceIssueSeverity.MEDIUM,
                        title=f"Archivo JS grande: {js_file.name} ({size_kb:.0f}KB)",
                        description="Los archivos JavaScript grandes aumentan el tiempo de carga.",
                        file_path=str(js_file),
                        line_number=None,
                        code_snippet=None,
                        impact="Aumenta el First Contentful Paint (FCP) y Time to Interactive (TTI).",
                        optimization="Divide el código con code splitting. "
                                    "Usa import() dinámico para cargar bajo demanda.",
                        estimated_improvement="50% mejora en tiempo de carga"
                    ))

                # Detectar imports no usados (simplificado)
                content = js_file.read_text(encoding='utf-8')
                imports = re.findall(r'import\s+{?\s*(\w+)', content)
                for imp in imports:
                    # Verificar si el import se usa
                    pattern = rf'\b{imp}\b'
                    uses = len(re.findall(pattern, content))
                    if uses == 1:  # Solo el import
                        unused_imports.append(f"{imp} en {js_file.name}")

            except Exception as e:
                logger.warning(f"Error analizando {js_file}: {e}")

        # Analizar CSS
        for css_file in css_files:
            try:
                size_kb = css_file.stat().st_size / 1024
                total_css_size += size_kb

                if size_kb > 50:
                    issues.append(PerformanceIssue(
                        id=self._generate_issue_id(),
                        category=PerformanceCategory.BUNDLE,
                        severity=PerformanceIssueSeverity.LOW,
                        title=f"Archivo CSS grande: {css_file.name} ({size_kb:.0f}KB)",
                        description="Los archivos CSS grandes bloquean el renderizado.",
                        file_path=str(css_file),
                        line_number=None,
                        code_snippet=None,
                        impact="Bloquea el First Contentful Paint.",
                        optimization="Usa critical CSS inline, carga el resto async. "
                                    "Elimina CSS no usado con PurgeCSS.",
                        estimated_improvement="30% mejora en FCP"
                    ))

            except Exception as e:
                logger.warning(f"Error analizando {css_file}: {e}")

        # Ordenar por tamaño
        largest_files.sort(key=lambda x: x[1], reverse=True)

        metrics = BundleMetrics(
            total_js_files=len(js_files),
            total_js_size_kb=total_js_size,
            total_css_files=len(css_files),
            total_css_size_kb=total_css_size,
            largest_files=largest_files[:10],
            unused_imports=unused_imports[:10],
            duplicate_code_patterns=duplicate_patterns
        )

        return issues, metrics

    # ========================================
    # ANÁLISIS DE ASSETS
    # ========================================

    def analyze_assets(self) -> Tuple[List[PerformanceIssue], AssetMetrics]:
        """
        Analiza los assets (imágenes, fuentes, etc.).

        Returns:
            Tupla (issues, metrics)
        """
        issues = []
        unoptimized = []
        large_images = []
        missing_lazy = 0

        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg']
        total_size = 0
        total_images = 0

        for ext in image_extensions:
            for img_file in self.project_root.glob(f"**/{ext}"):
                if 'node_modules' in str(img_file):
                    continue

                try:
                    size_mb = img_file.stat().st_size / (1024 * 1024)
                    total_size += size_mb
                    total_images += 1

                    # Imágenes grandes
                    if size_mb > 0.5:  # > 500KB
                        large_images.append((str(img_file), size_mb))

                        if size_mb > 2:  # > 2MB
                            issues.append(PerformanceIssue(
                                id=self._generate_issue_id(),
                                category=PerformanceCategory.ASSETS,
                                severity=PerformanceIssueSeverity.HIGH,
                                title=f"Imagen muy grande: {img_file.name} ({size_mb:.1f}MB)",
                                description="Las imágenes grandes ralentizan significativamente la carga.",
                                file_path=str(img_file),
                                line_number=None,
                                code_snippet=None,
                                impact="Aumenta el tiempo de carga y consume datos del usuario.",
                                optimization="Comprime con TinyPNG/ImageOptim. "
                                            "Usa WebP con fallback. Implementa srcset para responsive.",
                                estimated_improvement="80% reducción de tamaño"
                            ))

                    # Detectar formatos no optimizados
                    if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                        unoptimized.append(str(img_file))

                except Exception as e:
                    logger.warning(f"Error analizando {img_file}: {e}")

        # Verificar lazy loading en HTML
        html_files = list(self.project_root.glob("**/*.html"))
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8')
                imgs = re.findall(r'<img[^>]*>', content, re.IGNORECASE)

                for img in imgs:
                    if 'loading="lazy"' not in img.lower() and 'data-src' not in img.lower():
                        missing_lazy += 1

            except Exception:
                pass

        if missing_lazy > 5:
            issues.append(PerformanceIssue(
                id=self._generate_issue_id(),
                category=PerformanceCategory.ASSETS,
                severity=PerformanceIssueSeverity.MEDIUM,
                title=f"{missing_lazy} imágenes sin lazy loading",
                description="Las imágenes sin lazy loading se cargan todas al inicio.",
                file_path="múltiples archivos HTML",
                line_number=None,
                code_snippet=None,
                impact="Aumenta el tiempo de carga inicial innecesariamente.",
                optimization="Añade loading='lazy' a las imágenes below-the-fold. "
                            "Ejemplo: <img src='...' loading='lazy'>",
                estimated_improvement="40% mejora en carga inicial"
            ))

        # Issue general por formatos
        if len(unoptimized) > 5:
            issues.append(PerformanceIssue(
                id=self._generate_issue_id(),
                category=PerformanceCategory.ASSETS,
                severity=PerformanceIssueSeverity.MEDIUM,
                title=f"{len(unoptimized)} imágenes en formato no óptimo",
                description="PNG/JPG pueden ser reemplazados por WebP para mejor compresión.",
                file_path="múltiples archivos",
                line_number=None,
                code_snippet=None,
                impact="WebP ofrece 25-35% mejor compresión que PNG/JPG.",
                optimization="Convierte a WebP con: cwebp -q 80 input.png -o output.webp. "
                            "Usa <picture> para fallback a navegadores antiguos.",
                estimated_improvement="30% reducción en tamaño de imágenes"
            ))

        large_images.sort(key=lambda x: x[1], reverse=True)

        metrics = AssetMetrics(
            total_images=total_images,
            total_images_size_mb=total_size,
            unoptimized_images=unoptimized[:10],
            large_images=large_images[:10],
            missing_lazy_load=missing_lazy
        )

        return issues, metrics

    # ========================================
    # ANÁLISIS COMPLETO
    # ========================================

    def analyze_performance(self) -> PerformanceReport:
        """
        Realiza un análisis completo de rendimiento.

        Returns:
            PerformanceReport con todos los hallazgos
        """
        logger.info("⚡ Iniciando análisis de rendimiento...")

        all_issues = []

        # Análisis de base de datos
        db_issues, db_metrics = self.analyze_database_performance()
        all_issues.extend(db_issues)

        # Análisis de código
        code_issues = self.analyze_code_performance()
        all_issues.extend(code_issues)

        # Análisis de bundle
        bundle_issues, bundle_metrics = self.analyze_bundle_size()
        all_issues.extend(bundle_issues)

        # Análisis de assets
        asset_issues, asset_metrics = self.analyze_assets()
        all_issues.extend(asset_issues)

        # Clasificar por categoría
        issues_by_category = {}
        for issue in all_issues:
            cat = issue.category.value
            issues_by_category[cat] = issues_by_category.get(cat, 0) + 1

        # Contar archivos
        files_analyzed = len(list(self.project_root.glob("**/*.py")))
        files_analyzed += len(list(self.project_root.glob("**/*.js")))
        files_analyzed += len(list(self.project_root.glob("**/*.css")))

        # Calcular score
        score = 100
        for issue in all_issues:
            if issue.severity == PerformanceIssueSeverity.CRITICAL:
                score -= 20
            elif issue.severity == PerformanceIssueSeverity.HIGH:
                score -= 10
            elif issue.severity == PerformanceIssueSeverity.MEDIUM:
                score -= 5
            else:
                score -= 2
        score = max(0, score)

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            all_issues, db_metrics, bundle_metrics, asset_metrics
        )

        report = PerformanceReport(
            timestamp=datetime.now().isoformat(),
            files_analyzed=files_analyzed,
            total_issues=len(all_issues),
            issues_by_category=issues_by_category,
            issues=all_issues,
            database_metrics=db_metrics,
            bundle_metrics=bundle_metrics,
            asset_metrics=asset_metrics,
            recommendations=recommendations,
            performance_score=score
        )

        logger.info(f"✅ Análisis completado: {len(all_issues)} problemas, score: {score}%")

        return report

    def _generate_recommendations(
        self,
        issues: List[PerformanceIssue],
        db: DatabaseMetrics,
        bundle: BundleMetrics,
        assets: AssetMetrics
    ) -> List[str]:
        """Genera recomendaciones de rendimiento."""
        recs = []

        # Por N+1
        if db.potential_n_plus_1:
            recs.append(
                f"🔴 Base de datos: {len(db.potential_n_plus_1)} posibles queries N+1. "
                "Esto puede ser la causa principal de lentitud. Prioriza corregirlo."
            )

        # Por bundle
        if bundle.total_js_size_kb > 500:
            recs.append(
                f"📦 Bundle JS: {bundle.total_js_size_kb:.0f}KB total. "
                "Considera code splitting y lazy loading de módulos."
            )

        # Por assets
        if assets.total_images_size_mb > 5:
            recs.append(
                f"🖼️ Imágenes: {assets.total_images_size_mb:.1f}MB total. "
                "Comprime imágenes y usa WebP."
            )

        if assets.missing_lazy_load > 5:
            recs.append(
                f"🔄 Lazy loading: {assets.missing_lazy_load} imágenes sin lazy load. "
                "Añade loading='lazy' para mejorar la carga inicial."
            )

        # Por categoría más afectada
        category_counts = {}
        for issue in issues:
            cat = issue.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        if category_counts:
            top_cat = max(category_counts, key=category_counts.get)
            recs.append(
                f"🎯 Prioridad: {category_counts[top_cat]} problemas en '{top_cat}'. "
                "Enfócate en esta categoría primero."
            )

        # Recomendaciones generales
        recs.append(
            "💡 Tip: Usa herramientas de profiling como Chrome DevTools, "
            "Lighthouse, o py-spy para medir el impacto real."
        )

        if not issues:
            recs.insert(0,
                "✅ ¡Excelente! No se encontraron problemas críticos de rendimiento. "
                "Continúa monitoreando con herramientas de APM."
            )

        return recs


# Instancia singleton
_performance_instance: Optional[PerformanceAgent] = None


def get_performance_agent(project_root: str = ".") -> PerformanceAgent:
    """Obtiene la instancia global del Agente de Performance."""
    global _performance_instance
    if _performance_instance is None:
        _performance_instance = PerformanceAgent(project_root)
    return _performance_instance
