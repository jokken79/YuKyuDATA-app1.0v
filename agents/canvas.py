"""
Canvas Agent - Agente Especialista en Canvas/SVG y Gráficos
==========================================================

Experto en renderizado de gráficos y visualizaciones:
- Análisis de elementos Canvas HTML5
- Optimización de SVG
- Generación de gráficos y charts
- Análisis de performance de canvas
- Detección de problemas de rendering
- Conversión SVG <-> Canvas
- Animaciones Canvas
- Exportación de assets gráficos
- Integración con Chart.js/ApexCharts
"""

import logging
import re
import json
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class SVGElementType(Enum):
    """Tipos de elementos SVG."""
    PATH = "path"
    RECT = "rect"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    POLYGON = "polygon"
    POLYLINE = "polyline"
    TEXT = "text"
    GROUP = "g"
    DEFS = "defs"
    USE = "use"
    SYMBOL = "symbol"
    CLIPPATH = "clipPath"
    MASK = "mask"
    GRADIENT = "gradient"
    FILTER = "filter"


class ChartType(Enum):
    """Tipos de gráficos soportados."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    RADAR = "radar"
    POLAR = "polar"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    SPARKLINE = "sparkline"


class AnimationType(Enum):
    """Tipos de animación Canvas."""
    EASE_IN = "easeIn"
    EASE_OUT = "easeOut"
    EASE_IN_OUT = "easeInOut"
    LINEAR = "linear"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


@dataclass
class SVGAnalysis:
    """Resultado del análisis de SVG."""
    file_path: str
    file_size: int
    element_count: int
    elements_by_type: Dict[str, int]
    unique_colors: Set[str]
    has_animations: bool
    has_gradients: bool
    has_filters: bool
    has_text: bool
    viewbox: Optional[str]
    width: Optional[str]
    height: Optional[str]
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "file_path": self.file_path,
            "file_size": self.file_size,
            "element_count": self.element_count,
            "elements_by_type": self.elements_by_type,
            "unique_colors": list(self.unique_colors),
            "has_animations": self.has_animations,
            "has_gradients": self.has_gradients,
            "has_filters": self.has_filters,
            "has_text": self.has_text,
            "viewbox": self.viewbox,
            "dimensions": {"width": self.width, "height": self.height},
            "issues": self.issues,
            "recommendations": self.recommendations
        }


@dataclass
class CanvasAnalysis:
    """Resultado del análisis de código Canvas."""
    file_path: str
    canvas_count: int
    operations: Dict[str, int]
    uses_webgl: bool
    uses_2d: bool
    has_animations: bool
    has_event_handlers: bool
    estimated_complexity: str
    performance_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "file_path": self.file_path,
            "canvas_count": self.canvas_count,
            "operations": self.operations,
            "uses_webgl": self.uses_webgl,
            "uses_2d": self.uses_2d,
            "has_animations": self.has_animations,
            "has_event_handlers": self.has_event_handlers,
            "estimated_complexity": self.estimated_complexity,
            "performance_issues": self.performance_issues,
            "recommendations": self.recommendations
        }


@dataclass
class ChartConfig:
    """Configuración de gráfico."""
    type: ChartType
    data: Dict[str, Any]
    options: Dict[str, Any]
    colors: List[str] = field(default_factory=list)
    animation: bool = True
    responsive: bool = True

    def to_chartjs(self) -> Dict:
        """Convierte a formato Chart.js."""
        return {
            "type": self.type.value,
            "data": self.data,
            "options": {
                **self.options,
                "responsive": self.responsive,
                "animation": {"duration": 1000 if self.animation else 0}
            }
        }

    def to_apexcharts(self) -> Dict:
        """Convierte a formato ApexCharts."""
        apex_type_map = {
            ChartType.LINE: "line",
            ChartType.BAR: "bar",
            ChartType.PIE: "pie",
            ChartType.DOUGHNUT: "donut",
            ChartType.AREA: "area",
            ChartType.RADAR: "radar",
            ChartType.SCATTER: "scatter",
            ChartType.HEATMAP: "heatmap"
        }

        return {
            "chart": {
                "type": apex_type_map.get(self.type, "line"),
                "animations": {"enabled": self.animation}
            },
            "series": self.data.get("datasets", []),
            "xaxis": {"categories": self.data.get("labels", [])},
            "colors": self.colors if self.colors else None,
            **self.options
        }


class CanvasAgent:
    """
    Agente especializado en Canvas/SVG y visualizaciones.

    Capacidades:
    - Análisis de SVG
    - Optimización de SVG
    - Análisis de código Canvas
    - Generación de gráficos
    - Detección de problemas de performance
    - Conversión entre formatos
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.svg_analyses: List[SVGAnalysis] = []
        self.canvas_analyses: List[CanvasAnalysis] = []

        # Paleta de colores por defecto (cyan theme)
        self.default_colors = [
            "#06b6d4",  # cyan-500
            "#0891b2",  # cyan-600
            "#22d3ee",  # cyan-400
            "#67e8f9",  # cyan-300
            "#34d399",  # emerald-400
            "#fbbf24",  # amber-400
            "#f87171",  # red-400
            "#a78bfa",  # violet-400
        ]

        # Patrones de detección
        self._canvas_context_pattern = re.compile(r'getContext\([\'"]?(2d|webgl|webgl2)[\'"]?\)')
        self._canvas_draw_pattern = re.compile(
            r'\.(fillRect|strokeRect|clearRect|fillText|strokeText|drawImage|'
            r'arc|lineTo|moveTo|bezierCurveTo|quadraticCurveTo|fill|stroke)\('
        )
        self._animation_pattern = re.compile(r'requestAnimationFrame|setInterval|setTimeout.*draw')
        self._event_pattern = re.compile(r'addEventListener\([\'"]?(mouse|click|touch|pointer)')

    # ===============================
    # SVG ANALYSIS
    # ===============================

    def analyze_svg(self, svg_path: str) -> SVGAnalysis:
        """
        Analiza un archivo SVG.

        Args:
            svg_path: Ruta al archivo SVG

        Returns:
            SVGAnalysis con resultados
        """
        path = Path(svg_path)

        if not path.exists():
            return SVGAnalysis(
                file_path=svg_path,
                file_size=0,
                element_count=0,
                elements_by_type={},
                unique_colors=set(),
                has_animations=False,
                has_gradients=False,
                has_filters=False,
                has_text=False,
                viewbox=None,
                width=None,
                height=None,
                issues=["File not found"]
            )

        content = path.read_text(encoding='utf-8', errors='ignore')
        file_size = path.stat().st_size

        # Parse SVG
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            return SVGAnalysis(
                file_path=svg_path,
                file_size=file_size,
                element_count=0,
                elements_by_type={},
                unique_colors=set(),
                has_animations=False,
                has_gradients=False,
                has_filters=False,
                has_text=False,
                viewbox=None,
                width=None,
                height=None,
                issues=[f"Parse error: {e}"]
            )

        # Contar elementos
        elements_by_type = {}
        unique_colors = set()
        element_count = 0

        def count_elements(elem, depth=0):
            nonlocal element_count
            element_count += 1

            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            elements_by_type[tag] = elements_by_type.get(tag, 0) + 1

            # Extraer colores
            for attr in ['fill', 'stroke', 'stop-color', 'color']:
                if attr in elem.attrib:
                    color = elem.attrib[attr]
                    if color and color not in ['none', 'transparent', 'inherit', 'currentColor']:
                        unique_colors.add(color)

            for child in elem:
                count_elements(child, depth + 1)

        count_elements(root)

        # Detectar características
        has_animations = 'animate' in content.lower() or 'animateTransform' in content
        has_gradients = 'linearGradient' in content or 'radialGradient' in content
        has_filters = '<filter' in content
        has_text = '<text' in content

        # Atributos del root
        viewbox = root.attrib.get('viewBox')
        width = root.attrib.get('width')
        height = root.attrib.get('height')

        # Issues y recomendaciones
        issues = []
        recommendations = []

        if file_size > 50000:
            issues.append(f"SVG is large ({file_size / 1024:.1f}KB). Consider optimization.")
            recommendations.append("Use SVGO to optimize the file")

        if element_count > 500:
            issues.append(f"High element count ({element_count}). May affect rendering performance.")
            recommendations.append("Consider simplifying paths or using symbols")

        if not viewbox:
            issues.append("Missing viewBox attribute")
            recommendations.append("Add viewBox for proper scaling")

        if has_text and 'font-family' not in content:
            issues.append("Text elements without explicit font-family")
            recommendations.append("Specify font-family for consistent rendering")

        if len(unique_colors) > 10:
            recommendations.append(f"Consider reducing colors ({len(unique_colors)} unique colors found)")

        analysis = SVGAnalysis(
            file_path=svg_path,
            file_size=file_size,
            element_count=element_count,
            elements_by_type=elements_by_type,
            unique_colors=unique_colors,
            has_animations=has_animations,
            has_gradients=has_gradients,
            has_filters=has_filters,
            has_text=has_text,
            viewbox=viewbox,
            width=width,
            height=height,
            issues=issues,
            recommendations=recommendations
        )

        self.svg_analyses.append(analysis)
        return analysis

    def analyze_all_svgs(self) -> List[SVGAnalysis]:
        """Analiza todos los SVGs del proyecto."""
        svg_files = list(self.project_root.rglob("*.svg"))
        results = []

        for svg_file in svg_files:
            analysis = self.analyze_svg(str(svg_file))
            results.append(analysis)

        return results

    def optimize_svg(self, svg_content: str) -> str:
        """
        Optimiza contenido SVG (simplificado).

        Args:
            svg_content: Contenido SVG

        Returns:
            SVG optimizado
        """
        # Remover comentarios
        svg_content = re.sub(r'<!--.*?-->', '', svg_content, flags=re.DOTALL)

        # Remover metadata innecesaria
        svg_content = re.sub(r'<metadata>.*?</metadata>', '', svg_content, flags=re.DOTALL)

        # Remover espacios extra
        svg_content = re.sub(r'\s+', ' ', svg_content)

        # Remover atributos vacíos
        svg_content = re.sub(r'\s+\w+=""', '', svg_content)

        # Simplificar decimales largos
        def round_numbers(match):
            num = float(match.group(0))
            if num == int(num):
                return str(int(num))
            return f"{num:.2f}".rstrip('0').rstrip('.')

        svg_content = re.sub(r'\d+\.\d{3,}', round_numbers, svg_content)

        return svg_content.strip()

    # ===============================
    # CANVAS ANALYSIS
    # ===============================

    def analyze_canvas_code(self, js_path: str) -> CanvasAnalysis:
        """
        Analiza código JavaScript que usa Canvas.

        Args:
            js_path: Ruta al archivo JS

        Returns:
            CanvasAnalysis con resultados
        """
        path = Path(js_path)

        if not path.exists():
            return CanvasAnalysis(
                file_path=js_path,
                canvas_count=0,
                operations={},
                uses_webgl=False,
                uses_2d=False,
                has_animations=False,
                has_event_handlers=False,
                estimated_complexity="unknown",
                performance_issues=["File not found"]
            )

        content = path.read_text(encoding='utf-8', errors='ignore')

        # Detectar contextos
        context_matches = self._canvas_context_pattern.findall(content)
        uses_2d = '2d' in context_matches
        uses_webgl = 'webgl' in context_matches or 'webgl2' in context_matches

        # Contar operaciones de dibujo
        operations = {}
        for match in self._canvas_draw_pattern.finditer(content):
            op = match.group(1)
            operations[op] = operations.get(op, 0) + 1

        # Detectar animaciones
        has_animations = bool(self._animation_pattern.search(content))

        # Detectar eventos
        has_event_handlers = bool(self._event_pattern.search(content))

        # Contar canvas elements
        canvas_count = content.count('getElementById') + content.count('querySelector')

        # Estimar complejidad
        total_ops = sum(operations.values())
        if total_ops > 100:
            complexity = "high"
        elif total_ops > 30:
            complexity = "medium"
        else:
            complexity = "low"

        # Issues de performance
        performance_issues = []
        recommendations = []

        if 'getImageData' in content or 'putImageData' in content:
            performance_issues.append("Pixel manipulation detected - can be slow")
            recommendations.append("Consider using WebGL for heavy pixel operations")

        if has_animations and 'setInterval' in content:
            performance_issues.append("Using setInterval for animation")
            recommendations.append("Use requestAnimationFrame for smoother animations")

        if 'toDataURL' in content:
            performance_issues.append("Canvas export detected - can block main thread")
            recommendations.append("Consider using OffscreenCanvas for exports")

        if uses_2d and total_ops > 50 and not uses_webgl:
            recommendations.append("Consider WebGL for complex graphics")

        analysis = CanvasAnalysis(
            file_path=js_path,
            canvas_count=canvas_count,
            operations=operations,
            uses_webgl=uses_webgl,
            uses_2d=uses_2d,
            has_animations=has_animations,
            has_event_handlers=has_event_handlers,
            estimated_complexity=complexity,
            performance_issues=performance_issues,
            recommendations=recommendations
        )

        self.canvas_analyses.append(analysis)
        return analysis

    def analyze_all_canvas(self) -> List[CanvasAnalysis]:
        """Analiza todos los archivos JS con código Canvas."""
        js_files = list(self.project_root.rglob("*.js"))
        results = []

        for js_file in js_files:
            content = js_file.read_text(encoding='utf-8', errors='ignore')
            if 'canvas' in content.lower() or 'getContext' in content:
                analysis = self.analyze_canvas_code(str(js_file))
                results.append(analysis)

        return results

    # ===============================
    # CHART GENERATION
    # ===============================

    def create_chart_config(
        self,
        chart_type: ChartType,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        title: str = "",
        colors: Optional[List[str]] = None
    ) -> ChartConfig:
        """
        Crea configuración de gráfico.

        Args:
            chart_type: Tipo de gráfico
            labels: Etiquetas del eje X
            datasets: Datos del gráfico
            title: Título del gráfico
            colors: Colores personalizados

        Returns:
            ChartConfig configurado
        """
        chart_colors = colors or self.default_colors

        # Asignar colores a datasets
        for i, ds in enumerate(datasets):
            if 'backgroundColor' not in ds:
                if chart_type in [ChartType.PIE, ChartType.DOUGHNUT]:
                    ds['backgroundColor'] = chart_colors[:len(labels)]
                else:
                    ds['backgroundColor'] = chart_colors[i % len(chart_colors)]
            if 'borderColor' not in ds:
                ds['borderColor'] = ds.get('backgroundColor', chart_colors[i % len(chart_colors)])

        data = {
            "labels": labels,
            "datasets": datasets
        }

        options = {
            "plugins": {
                "legend": {"display": len(datasets) > 1 or chart_type in [ChartType.PIE, ChartType.DOUGHNUT]},
                "title": {"display": bool(title), "text": title}
            }
        }

        if chart_type in [ChartType.LINE, ChartType.AREA]:
            options["scales"] = {
                "y": {"beginAtZero": True}
            }

        return ChartConfig(
            type=chart_type,
            data=data,
            options=options,
            colors=chart_colors
        )

    def generate_progress_ring_svg(
        self,
        percentage: float,
        size: int = 80,
        stroke_width: int = 6,
        color: str = "#06b6d4",
        bg_color: str = "rgba(255,255,255,0.1)"
    ) -> str:
        """
        Genera SVG de anillo de progreso.

        Args:
            percentage: Porcentaje (0-100)
            size: Tamaño del SVG
            stroke_width: Grosor del trazo
            color: Color del progreso
            bg_color: Color de fondo

        Returns:
            Código SVG
        """
        radius = (size - stroke_width) / 2
        circumference = 2 * math.pi * radius
        offset = circumference - (percentage / 100 * circumference)

        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle
    cx="{size/2}" cy="{size/2}" r="{radius}"
    fill="none" stroke="{bg_color}" stroke-width="{stroke_width}"
  />
  <circle
    cx="{size/2}" cy="{size/2}" r="{radius}"
    fill="none" stroke="{color}" stroke-width="{stroke_width}"
    stroke-linecap="round"
    stroke-dasharray="{circumference}"
    stroke-dashoffset="{offset}"
    transform="rotate(-90 {size/2} {size/2})"
    style="transition: stroke-dashoffset 1s ease-out;"
  />
  <text x="50%" y="50%" text-anchor="middle" dy="0.35em"
    font-size="{size/5}px" font-weight="bold" fill="{color}">
    {percentage:.0f}%
  </text>
</svg>'''

    def generate_gauge_svg(
        self,
        value: float,
        max_value: float = 100,
        size: int = 200,
        color: str = "#06b6d4"
    ) -> str:
        """
        Genera SVG de gauge/velocímetro.

        Args:
            value: Valor actual
            max_value: Valor máximo
            size: Tamaño del SVG
            color: Color del indicador

        Returns:
            Código SVG
        """
        percentage = min(value / max_value * 100, 100)
        angle = (percentage / 100) * 180  # Semi-círculo

        cx, cy = size / 2, size * 0.6
        radius = size * 0.4
        stroke_width = size * 0.08

        # Calcular arco
        start_angle = 180
        end_angle = 180 + angle

        return f'''<svg width="{size}" height="{size*0.7}" viewBox="0 0 {size} {size*0.7}">
  <!-- Background arc -->
  <path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}"
    fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="{stroke_width}"
    stroke-linecap="round"/>
  <!-- Value arc -->
  <path d="M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius * math.cos(math.radians(180 - angle))} {cy - radius * math.sin(math.radians(180 - angle))}"
    fill="none" stroke="{color}" stroke-width="{stroke_width}"
    stroke-linecap="round"
    style="transition: all 1s ease-out;"/>
  <!-- Value text -->
  <text x="{cx}" y="{cy + 10}" text-anchor="middle"
    font-size="{size/5}px" font-weight="bold" fill="white">
    {value:.0f}
  </text>
  <text x="{cx}" y="{cy + 30}" text-anchor="middle"
    font-size="{size/12}px" fill="rgba(255,255,255,0.6)">
    / {max_value:.0f}
  </text>
</svg>'''

    def generate_sparkline_svg(
        self,
        values: List[float],
        width: int = 100,
        height: int = 30,
        color: str = "#06b6d4"
    ) -> str:
        """
        Genera SVG de sparkline (mini gráfico).

        Args:
            values: Lista de valores
            width: Ancho del SVG
            height: Alto del SVG
            color: Color de la línea

        Returns:
            Código SVG
        """
        if not values:
            return f'<svg width="{width}" height="{height}"></svg>'

        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val or 1

        points = []
        for i, v in enumerate(values):
            x = (i / (len(values) - 1)) * width if len(values) > 1 else width / 2
            y = height - ((v - min_val) / range_val * (height - 4)) - 2
            points.append(f"{x:.1f},{y:.1f}")

        path = "M " + " L ".join(points)
        area_path = path + f" L {width},{height} L 0,{height} Z"

        return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="sparkline-gradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <path d="{area_path}" fill="url(#sparkline-gradient)"/>
  <path d="{path}" fill="none" stroke="{color}" stroke-width="1.5"
    stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="2" fill="{color}"/>
</svg>'''

    # ===============================
    # FULL ANALYSIS
    # ===============================

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Ejecuta análisis completo de Canvas/SVG.

        Returns:
            Resultado completo del análisis
        """
        svg_results = self.analyze_all_svgs()
        canvas_results = self.analyze_all_canvas()

        total_svg_issues = sum(len(s.issues) for s in svg_results)
        total_canvas_issues = sum(len(c.performance_issues) for c in canvas_results)

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "svg_files": len(svg_results),
                "canvas_files": len(canvas_results),
                "total_svg_issues": total_svg_issues,
                "total_canvas_issues": total_canvas_issues
            },
            "svg_analysis": [s.to_dict() for s in svg_results],
            "canvas_analysis": [c.to_dict() for c in canvas_results],
            "recommendations": self._generate_global_recommendations(svg_results, canvas_results)
        }

    def _generate_global_recommendations(
        self,
        svg_results: List[SVGAnalysis],
        canvas_results: List[CanvasAnalysis]
    ) -> List[str]:
        """Genera recomendaciones globales."""
        recommendations = []

        # SVG recommendations
        large_svgs = [s for s in svg_results if s.file_size > 30000]
        if large_svgs:
            recommendations.append(
                f"{len(large_svgs)} SVG files are large. Consider running SVGO optimization."
            )

        # Canvas recommendations
        complex_canvas = [c for c in canvas_results if c.estimated_complexity == "high"]
        if complex_canvas:
            recommendations.append(
                f"{len(complex_canvas)} JS files have complex Canvas code. Consider performance optimization."
            )

        webgl_users = [c for c in canvas_results if c.uses_webgl]
        if not webgl_users and any(c.estimated_complexity == "high" for c in canvas_results):
            recommendations.append(
                "Consider using WebGL for heavy graphics rendering."
            )

        return recommendations


# Singleton para acceso global
_canvas_agent_instance: Optional[CanvasAgent] = None


def get_canvas_agent(project_root: str = ".") -> CanvasAgent:
    """Obtiene instancia singleton del CanvasAgent."""
    global _canvas_agent_instance
    if _canvas_agent_instance is None:
        _canvas_agent_instance = CanvasAgent(project_root)
    return _canvas_agent_instance


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Crear agente
    canvas = CanvasAgent()

    # Análisis completo
    result = canvas.run_full_analysis()

    print(f"SVG files analyzed: {result['summary']['svg_files']}")
    print(f"Canvas files analyzed: {result['summary']['canvas_files']}")
    print(f"Total issues: {result['summary']['total_svg_issues'] + result['summary']['total_canvas_issues']}")

    # Generar gráfico de ejemplo
    chart = canvas.create_chart_config(
        ChartType.BAR,
        labels=["Jan", "Feb", "Mar", "Apr"],
        datasets=[{"label": "Sales", "data": [10, 20, 30, 40]}],
        title="Monthly Sales"
    )
    print(f"\nChart.js config: {json.dumps(chart.to_chartjs(), indent=2)}")

    # Generar SVGs
    ring = canvas.generate_progress_ring_svg(75)
    print(f"\nProgress ring generated: {len(ring)} chars")
