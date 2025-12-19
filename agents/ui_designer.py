"""
UI Designer Agent - Agente Especialista en Diseño Visual
=========================================================

Experto en diseño de interfaces y sistemas visuales:
- Análisis de estilos CSS/SCSS
- Detección de inconsistencias visuales
- Auditoría de Design System
- Análisis de accesibilidad visual (contraste, tamaños)
- Generación de paletas de colores
- Análisis de tipografía
- Sugerencias de mejoras visuales
- Exportación de especificaciones para Figma
- Análisis de Canvas/SVG
"""

import logging
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from colorsys import rgb_to_hls, hls_to_rgb

logger = logging.getLogger(__name__)


class DesignIssueType(Enum):
    """Tipos de problemas de diseño."""
    CONTRAST = "contrast"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    COLOR = "color"
    CONSISTENCY = "consistency"
    ACCESSIBILITY = "accessibility"
    RESPONSIVENESS = "responsiveness"
    ANIMATION = "animation"


class IssueSeverity(Enum):
    """Niveles de severidad."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ColorInfo:
    """Información sobre un color."""
    hex: str
    rgb: Tuple[int, int, int]
    hsl: Tuple[float, float, float]
    name: Optional[str] = None
    usage_count: int = 0
    locations: List[str] = field(default_factory=list)

    @property
    def luminance(self) -> float:
        """Calcula luminancia relativa (WCAG)."""
        r, g, b = [x / 255.0 for x in self.rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def contrast_ratio(self, other: 'ColorInfo') -> float:
        """Calcula ratio de contraste con otro color."""
        l1 = max(self.luminance, other.luminance)
        l2 = min(self.luminance, other.luminance)
        return (l1 + 0.05) / (l2 + 0.05)


@dataclass
class DesignIssue:
    """Representa un problema de diseño detectado."""
    id: str
    type: DesignIssueType
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int]
    title: str
    description: str
    suggestion: str
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    wcag_level: Optional[str] = None
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'title': self.title,
            'description': self.description,
            'suggestion': self.suggestion,
            'current_value': self.current_value,
            'suggested_value': self.suggested_value,
            'wcag_level': self.wcag_level
        }


@dataclass
class FontInfo:
    """Información sobre una fuente."""
    family: str
    weights: Set[str]
    sizes: Set[str]
    line_heights: Set[str]
    usage_count: int = 0


@dataclass
class SpacingInfo:
    """Información sobre espaciados."""
    value: str
    pixels: float
    usage_count: int = 0
    locations: List[str] = field(default_factory=list)


@dataclass
class DesignSystemSpec:
    """Especificación de Design System extraída."""
    colors: Dict[str, ColorInfo]
    fonts: Dict[str, FontInfo]
    spacings: List[SpacingInfo]
    breakpoints: Dict[str, str]
    shadows: List[str]
    border_radius: List[str]
    animations: List[str]
    z_indexes: List[int]

    def to_figma_tokens(self) -> Dict:
        """Exporta tokens compatibles con Figma."""
        return {
            'color': {
                name: {'value': color.hex, 'type': 'color'}
                for name, color in self.colors.items()
            },
            'typography': {
                font.family: {
                    'fontFamily': {'value': font.family, 'type': 'fontFamilies'},
                    'fontWeights': list(font.weights),
                    'fontSizes': list(font.sizes)
                }
                for font in self.fonts.values()
            },
            'spacing': {
                f'space-{i}': {'value': s.value, 'type': 'spacing'}
                for i, s in enumerate(sorted(self.spacings, key=lambda x: x.pixels))
            },
            'borderRadius': {
                f'radius-{i}': {'value': r, 'type': 'borderRadius'}
                for i, r in enumerate(self.border_radius)
            }
        }


@dataclass
class UIAuditReport:
    """Reporte de auditoría de UI."""
    timestamp: str
    files_analyzed: int
    total_issues: int
    issues_by_type: Dict[str, int]
    issues: List[DesignIssue]
    design_system: DesignSystemSpec
    recommendations: List[str]
    accessibility_score: float

    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'files_analyzed': self.files_analyzed,
            'total_issues': self.total_issues,
            'issues_by_type': self.issues_by_type,
            'accessibility_score': self.accessibility_score,
            'recommendations': self.recommendations
        }


class UIDesignerAgent:
    """
    Agente UI Designer - Especialista en Diseño Visual

    El experto en diseño de interfaces que:
    - Analiza CSS/SCSS para extraer Design System
    - Detecta inconsistencias visuales
    - Audita accesibilidad (WCAG 2.1)
    - Genera paletas de colores optimizadas
    - Analiza tipografía y espaciados
    - Exporta especificaciones para Figma
    - Sugiere mejoras visuales

    Ejemplo de uso:
    ```python
    ui = UIDesignerAgent()

    # Auditoría completa de UI
    report = ui.audit_ui()

    # Extraer Design System
    ds = ui.extract_design_system()

    # Exportar tokens para Figma
    tokens = ui.export_figma_tokens()

    # Analizar contraste de colores
    issues = ui.check_color_contrast("#ffffff", "#000000")

    # Generar paleta armonizada
    palette = ui.generate_color_palette("#3498db")
    ```
    """

    # Breakpoints estándar
    STANDARD_BREAKPOINTS = {
        'mobile': '320px',
        'tablet': '768px',
        'desktop': '1024px',
        'large': '1440px'
    }

    # WCAG contrast requirements
    WCAG_CONTRAST = {
        'AA_normal': 4.5,
        'AA_large': 3.0,
        'AAA_normal': 7.0,
        'AAA_large': 4.5
    }

    # Escala tipográfica armónica (Major Third)
    TYPE_SCALE = [0.75, 0.875, 1, 1.125, 1.25, 1.5, 1.875, 2.25, 3, 3.75, 4.5]

    # Escala de espaciado (8pt grid)
    SPACING_SCALE = [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]

    def __init__(self, project_root: str = "."):
        """
        Inicializa el Agente UI Designer.

        Args:
            project_root: Ruta raíz del proyecto
        """
        self.project_root = Path(project_root)
        self._issue_counter = 0
        self._colors_cache: Dict[str, ColorInfo] = {}

    def _generate_issue_id(self) -> str:
        """Genera un ID único para un issue."""
        self._issue_counter += 1
        return f"UI-{datetime.now().strftime('%Y%m%d')}-{self._issue_counter:04d}"

    # ========================================
    # ANÁLISIS DE COLORES
    # ========================================

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convierte color hex a RGB."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convierte RGB a hex."""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def parse_color(self, color_str: str) -> Optional[ColorInfo]:
        """
        Parsea un string de color a ColorInfo.

        Args:
            color_str: Color en formato hex, rgb, rgba, hsl

        Returns:
            ColorInfo o None si no es válido
        """
        color_str = color_str.strip().lower()

        # Hex color
        hex_match = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', color_str)
        if hex_match:
            rgb = self.hex_to_rgb(color_str)
            r, g, b = [x / 255.0 for x in rgb]
            h, l, s = rgb_to_hls(r, g, b)
            return ColorInfo(
                hex=color_str,
                rgb=rgb,
                hsl=(h * 360, s * 100, l * 100)
            )

        # RGB/RGBA
        rgb_match = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
        if rgb_match:
            rgb = (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)))
            r, g, b = [x / 255.0 for x in rgb]
            h, l, s = rgb_to_hls(r, g, b)
            return ColorInfo(
                hex=self.rgb_to_hex(rgb),
                rgb=rgb,
                hsl=(h * 360, s * 100, l * 100)
            )

        return None

    def check_color_contrast(
        self,
        foreground: str,
        background: str
    ) -> Tuple[float, Dict[str, bool]]:
        """
        Verifica el contraste entre dos colores según WCAG.

        Args:
            foreground: Color del texto
            background: Color del fondo

        Returns:
            Tupla (ratio, {AA_normal, AA_large, AAA_normal, AAA_large})
        """
        fg = self.parse_color(foreground)
        bg = self.parse_color(background)

        if not fg or not bg:
            return 0, {}

        ratio = fg.contrast_ratio(bg)

        compliance = {
            'AA_normal': ratio >= self.WCAG_CONTRAST['AA_normal'],
            'AA_large': ratio >= self.WCAG_CONTRAST['AA_large'],
            'AAA_normal': ratio >= self.WCAG_CONTRAST['AAA_normal'],
            'AAA_large': ratio >= self.WCAG_CONTRAST['AAA_large']
        }

        return ratio, compliance

    def generate_color_palette(
        self,
        base_color: str,
        scheme: str = 'complementary'
    ) -> List[ColorInfo]:
        """
        Genera una paleta de colores armónica.

        Args:
            base_color: Color base en hex
            scheme: Tipo de esquema (complementary, triadic, analogous, split)

        Returns:
            Lista de ColorInfo con la paleta
        """
        base = self.parse_color(base_color)
        if not base:
            return []

        h, s, l = base.hsl
        h = h / 360  # Normalizar a 0-1

        palette = [base]

        if scheme == 'complementary':
            # Color complementario (opuesto)
            comp_h = (h + 0.5) % 1.0
            palette.append(self._create_color_from_hsl(comp_h, s / 100, l / 100))

        elif scheme == 'triadic':
            # Tres colores equidistantes
            for offset in [1/3, 2/3]:
                new_h = (h + offset) % 1.0
                palette.append(self._create_color_from_hsl(new_h, s / 100, l / 100))

        elif scheme == 'analogous':
            # Colores adyacentes
            for offset in [-1/12, 1/12]:
                new_h = (h + offset) % 1.0
                palette.append(self._create_color_from_hsl(new_h, s / 100, l / 100))

        elif scheme == 'split':
            # Split complementary
            for offset in [5/12, 7/12]:
                new_h = (h + offset) % 1.0
                palette.append(self._create_color_from_hsl(new_h, s / 100, l / 100))

        # Añadir variantes de luminosidad
        for variant_l in [0.2, 0.4, 0.6, 0.8]:
            palette.append(self._create_color_from_hsl(h, s / 100, variant_l))

        return palette

    def _create_color_from_hsl(self, h: float, s: float, l: float) -> ColorInfo:
        """Crea ColorInfo desde valores HSL normalizados."""
        r, g, b = hls_to_rgb(h, l, s)
        rgb = (int(r * 255), int(g * 255), int(b * 255))
        return ColorInfo(
            hex=self.rgb_to_hex(rgb),
            rgb=rgb,
            hsl=(h * 360, s * 100, l * 100)
        )

    # ========================================
    # ANÁLISIS DE CSS
    # ========================================

    def analyze_css_file(self, file_path: str) -> Tuple[List[DesignIssue], Dict]:
        """
        Analiza un archivo CSS para extraer información de diseño.

        Args:
            file_path: Ruta al archivo CSS

        Returns:
            Tupla (issues, extracted_data)
        """
        issues = []
        extracted = {
            'colors': {},
            'fonts': {},
            'spacings': [],
            'breakpoints': {},
            'shadows': [],
            'border_radius': [],
            'animations': [],
            'z_indexes': []
        }

        path = Path(file_path)
        if not path.exists():
            return issues, extracted

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Extraer colores
            color_patterns = [
                r'#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b',
                r'rgba?\s*\([^)]+\)',
                r'hsla?\s*\([^)]+\)'
            ]

            for i, line in enumerate(lines, 1):
                for pattern in color_patterns:
                    matches = re.findall(pattern, line)
                    for match in matches:
                        color_str = match if match.startswith('#') or match.startswith('rgb') else f'#{match}'
                        color = self.parse_color(color_str)
                        if color:
                            if color.hex not in extracted['colors']:
                                color.locations = []
                                extracted['colors'][color.hex] = color
                            extracted['colors'][color.hex].usage_count += 1
                            extracted['colors'][color.hex].locations.append(f"{file_path}:{i}")

            # Extraer font-families
            font_pattern = r'font-family\s*:\s*([^;]+)'
            for i, line in enumerate(lines, 1):
                match = re.search(font_pattern, line)
                if match:
                    fonts = match.group(1).strip()
                    primary_font = fonts.split(',')[0].strip().strip('"\'')
                    if primary_font not in extracted['fonts']:
                        extracted['fonts'][primary_font] = FontInfo(
                            family=primary_font,
                            weights=set(),
                            sizes=set(),
                            line_heights=set()
                        )
                    extracted['fonts'][primary_font].usage_count += 1

            # Extraer font-sizes
            size_pattern = r'font-size\s*:\s*([^;]+)'
            for line in lines:
                match = re.search(size_pattern, line)
                if match:
                    size = match.group(1).strip()
                    for font in extracted['fonts'].values():
                        font.sizes.add(size)

            # Extraer espaciados (margin, padding)
            spacing_pattern = r'(margin|padding)(?:-\w+)?\s*:\s*([^;]+)'
            for i, line in enumerate(lines, 1):
                match = re.search(spacing_pattern, line)
                if match:
                    values = match.group(2).strip().split()
                    for val in values:
                        if val != '0' and val != 'auto':
                            pixels = self._parse_to_pixels(val)
                            if pixels is not None:
                                extracted['spacings'].append(SpacingInfo(
                                    value=val,
                                    pixels=pixels,
                                    usage_count=1,
                                    locations=[f"{file_path}:{i}"]
                                ))

            # Extraer border-radius
            radius_pattern = r'border-radius\s*:\s*([^;]+)'
            for line in lines:
                match = re.search(radius_pattern, line)
                if match:
                    radius = match.group(1).strip()
                    if radius not in extracted['border_radius']:
                        extracted['border_radius'].append(radius)

            # Extraer box-shadow
            shadow_pattern = r'box-shadow\s*:\s*([^;]+)'
            for line in lines:
                match = re.search(shadow_pattern, line)
                if match:
                    shadow = match.group(1).strip()
                    if shadow not in extracted['shadows']:
                        extracted['shadows'].append(shadow)

            # Extraer media queries (breakpoints)
            bp_pattern = r'@media[^{]*\((?:min|max)-width\s*:\s*(\d+(?:px|em|rem))\)'
            for line in lines:
                match = re.search(bp_pattern, line)
                if match:
                    bp = match.group(1)
                    if bp not in extracted['breakpoints'].values():
                        bp_name = f"breakpoint_{len(extracted['breakpoints'])}"
                        extracted['breakpoints'][bp_name] = bp

            # Extraer z-index
            z_pattern = r'z-index\s*:\s*(\d+)'
            for line in lines:
                match = re.search(z_pattern, line)
                if match:
                    z = int(match.group(1))
                    if z not in extracted['z_indexes']:
                        extracted['z_indexes'].append(z)

            # Detectar animaciones
            anim_pattern = r'(animation|transition)\s*:\s*([^;]+)'
            for line in lines:
                match = re.search(anim_pattern, line)
                if match:
                    anim = match.group(2).strip()
                    if anim not in extracted['animations']:
                        extracted['animations'].append(anim)

            # ========================================
            # DETECCIÓN DE PROBLEMAS
            # ========================================

            # Verificar demasiados colores
            if len(extracted['colors']) > 20:
                issues.append(DesignIssue(
                    id=self._generate_issue_id(),
                    type=DesignIssueType.CONSISTENCY,
                    severity=IssueSeverity.WARNING,
                    file_path=file_path,
                    line_number=None,
                    title="Demasiados colores definidos",
                    description=f"Se encontraron {len(extracted['colors'])} colores únicos. "
                               "Un Design System típico usa 5-10 colores base.",
                    suggestion="Consolida los colores en variables CSS (--color-*) "
                              "y reduce la paleta a colores esenciales."
                ))

            # Verificar inconsistencia en espaciados
            unique_spacings = set(s.pixels for s in extracted['spacings'])
            if len(unique_spacings) > 15:
                issues.append(DesignIssue(
                    id=self._generate_issue_id(),
                    type=DesignIssueType.SPACING,
                    severity=IssueSeverity.WARNING,
                    file_path=file_path,
                    line_number=None,
                    title="Espaciados inconsistentes",
                    description=f"Se encontraron {len(unique_spacings)} valores de espaciado únicos. "
                               "Esto puede causar inconsistencia visual.",
                    suggestion="Usa una escala de espaciado basada en 4px u 8px: "
                              "4, 8, 12, 16, 24, 32, 48, 64px."
                ))

            # Verificar z-index caóticos
            if extracted['z_indexes'] and max(extracted['z_indexes']) > 9999:
                issues.append(DesignIssue(
                    id=self._generate_issue_id(),
                    type=DesignIssueType.CONSISTENCY,
                    severity=IssueSeverity.WARNING,
                    file_path=file_path,
                    line_number=None,
                    title="z-index muy altos",
                    description=f"Se encontraron z-index hasta {max(extracted['z_indexes'])}. "
                               "Los valores muy altos indican 'z-index wars'.",
                    suggestion="Define una escala de z-index: 1-10 (base), 100 (dropdown), "
                              "1000 (modal), 9999 (toast)."
                ))

            # Verificar fuentes sin fallback
            for font_name, font in extracted['fonts'].items():
                if len(font.family.split(',')) == 1 and font.family not in ['inherit', 'system-ui']:
                    issues.append(DesignIssue(
                        id=self._generate_issue_id(),
                        type=DesignIssueType.TYPOGRAPHY,
                        severity=IssueSeverity.INFO,
                        file_path=file_path,
                        line_number=None,
                        title=f"Fuente sin fallback: {font_name}",
                        description="La fuente no tiene familia de respaldo (fallback).",
                        suggestion=f"Usa: '{font_name}', -apple-system, BlinkMacSystemFont, "
                                  "'Segoe UI', Roboto, sans-serif"
                    ))

        except Exception as e:
            logger.error(f"Error analizando CSS {file_path}: {e}")

        return issues, extracted

    def _parse_to_pixels(self, value: str) -> Optional[float]:
        """Convierte un valor CSS a píxeles."""
        value = value.strip().lower()

        if value.endswith('px'):
            return float(value[:-2])
        elif value.endswith('rem'):
            return float(value[:-3]) * 16
        elif value.endswith('em'):
            return float(value[:-2]) * 16
        elif value.endswith('%'):
            return None  # Porcentaje relativo
        elif value.isdigit():
            return float(value)

        return None

    # ========================================
    # ANÁLISIS DE ACCESIBILIDAD VISUAL
    # ========================================

    def audit_accessibility(self, css_files: List[str] = None) -> List[DesignIssue]:
        """
        Audita accesibilidad visual del proyecto.

        Args:
            css_files: Lista de archivos CSS a analizar

        Returns:
            Lista de problemas de accesibilidad
        """
        issues = []

        if css_files is None:
            css_files = list(self.project_root.glob("**/*.css"))

        all_colors = {}

        # Recopilar todos los colores
        for css_file in css_files:
            _, extracted = self.analyze_css_file(str(css_file))
            all_colors.update(extracted.get('colors', {}))

        # Verificar contrastes comunes
        light_bg = ['#ffffff', '#f5f5f5', '#fafafa', '#fff', '#f8f9fa']
        dark_text = []
        light_text = []

        for hex_color, color in all_colors.items():
            if color.hsl[2] < 40:  # Luminosidad baja = oscuro
                dark_text.append(color)
            elif color.hsl[2] > 70:  # Luminosidad alta = claro
                light_text.append(color)

        # Verificar contrastes texto oscuro sobre fondo claro
        white = self.parse_color('#ffffff')
        for dark in dark_text:
            ratio, compliance = self.check_color_contrast(dark.hex, '#ffffff')
            if not compliance.get('AA_normal', False):
                issues.append(DesignIssue(
                    id=self._generate_issue_id(),
                    type=DesignIssueType.CONTRAST,
                    severity=IssueSeverity.ERROR,
                    file_path="global",
                    line_number=None,
                    title=f"Contraste insuficiente: {dark.hex}",
                    description=f"El color {dark.hex} sobre blanco tiene ratio {ratio:.2f}. "
                               f"WCAG AA requiere mínimo 4.5:1 para texto normal.",
                    suggestion="Oscurece el color o usa una variante con mayor contraste.",
                    current_value=f"{ratio:.2f}:1",
                    suggested_value="≥4.5:1",
                    wcag_level="AA"
                ))

        # Verificar tamaños de texto mínimos
        for css_file in css_files:
            content = Path(css_file).read_text(encoding='utf-8') if Path(css_file).exists() else ""
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                size_match = re.search(r'font-size\s*:\s*(\d+(?:\.\d+)?)(px|pt)', line)
                if size_match:
                    size = float(size_match.group(1))
                    unit = size_match.group(2)

                    # Convertir a px si es pt
                    if unit == 'pt':
                        size = size * 1.333

                    if size < 12:
                        issues.append(DesignIssue(
                            id=self._generate_issue_id(),
                            type=DesignIssueType.ACCESSIBILITY,
                            severity=IssueSeverity.WARNING,
                            file_path=str(css_file),
                            line_number=i,
                            title=f"Tamaño de fuente muy pequeño: {size}{unit}",
                            description="Los tamaños menores a 12px pueden ser difíciles de leer.",
                            suggestion="Usa mínimo 14px para texto de cuerpo, 12px solo para labels secundarios.",
                            current_value=f"{size}{unit}",
                            suggested_value="≥14px"
                        ))

        return issues

    # ========================================
    # EXTRACCIÓN DE DESIGN SYSTEM
    # ========================================

    def extract_design_system(self) -> DesignSystemSpec:
        """
        Extrae el Design System completo del proyecto.

        Returns:
            DesignSystemSpec con todos los tokens de diseño
        """
        all_colors = {}
        all_fonts = {}
        all_spacings = []
        all_breakpoints = {}
        all_shadows = []
        all_radius = []
        all_animations = []
        all_z_indexes = []

        # Analizar todos los archivos CSS
        css_files = list(self.project_root.glob("**/*.css"))

        for css_file in css_files:
            _, extracted = self.analyze_css_file(str(css_file))

            all_colors.update(extracted.get('colors', {}))
            all_fonts.update(extracted.get('fonts', {}))
            all_spacings.extend(extracted.get('spacings', []))
            all_breakpoints.update(extracted.get('breakpoints', {}))
            all_shadows.extend(extracted.get('shadows', []))
            all_radius.extend(extracted.get('border_radius', []))
            all_animations.extend(extracted.get('animations', []))
            all_z_indexes.extend(extracted.get('z_indexes', []))

        # Deduplicar y ordenar
        unique_shadows = list(set(all_shadows))
        unique_radius = list(set(all_radius))
        unique_animations = list(set(all_animations))
        unique_z = sorted(list(set(all_z_indexes)))

        # Consolidar espaciados
        spacing_map = {}
        for spacing in all_spacings:
            if spacing.pixels not in spacing_map:
                spacing_map[spacing.pixels] = spacing
            else:
                spacing_map[spacing.pixels].usage_count += spacing.usage_count

        return DesignSystemSpec(
            colors=all_colors,
            fonts=all_fonts,
            spacings=list(spacing_map.values()),
            breakpoints=all_breakpoints,
            shadows=unique_shadows,
            border_radius=unique_radius,
            animations=unique_animations,
            z_indexes=unique_z
        )

    def export_figma_tokens(self, output_path: str = "design-tokens.json") -> str:
        """
        Exporta tokens de diseño en formato compatible con Figma.

        Args:
            output_path: Ruta para guardar el archivo JSON

        Returns:
            Ruta al archivo generado
        """
        ds = self.extract_design_system()
        tokens = ds.to_figma_tokens()

        output = self.project_root / output_path
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)

        logger.info(f"📐 Tokens exportados a {output}")
        return str(output)

    # ========================================
    # AUDITORÍA COMPLETA DE UI
    # ========================================

    def audit_ui(self) -> UIAuditReport:
        """
        Realiza una auditoría completa de UI del proyecto.

        Returns:
            UIAuditReport con todos los hallazgos
        """
        logger.info("🎨 Iniciando auditoría de UI...")

        all_issues = []
        files_analyzed = 0

        # Analizar archivos CSS
        css_files = list(self.project_root.glob("**/*.css"))
        for css_file in css_files:
            issues, _ = self.analyze_css_file(str(css_file))
            all_issues.extend(issues)
            files_analyzed += 1

        # Auditoría de accesibilidad
        a11y_issues = self.audit_accessibility([str(f) for f in css_files])
        all_issues.extend(a11y_issues)

        # Extraer Design System
        design_system = self.extract_design_system()

        # Clasificar issues por tipo
        issues_by_type = {}
        for issue in all_issues:
            type_name = issue.type.value
            issues_by_type[type_name] = issues_by_type.get(type_name, 0) + 1

        # Calcular score de accesibilidad
        critical_a11y = sum(1 for i in all_issues
                          if i.type in [DesignIssueType.CONTRAST, DesignIssueType.ACCESSIBILITY]
                          and i.severity in [IssueSeverity.ERROR, IssueSeverity.CRITICAL])
        a11y_score = max(0, 100 - (critical_a11y * 10))

        # Generar recomendaciones
        recommendations = self._generate_ui_recommendations(all_issues, design_system)

        report = UIAuditReport(
            timestamp=datetime.now().isoformat(),
            files_analyzed=files_analyzed,
            total_issues=len(all_issues),
            issues_by_type=issues_by_type,
            issues=all_issues,
            design_system=design_system,
            recommendations=recommendations,
            accessibility_score=a11y_score
        )

        logger.info(f"✅ Auditoría completada: {files_analyzed} archivos, "
                   f"{len(all_issues)} problemas, A11Y score: {a11y_score}%")

        return report

    def _generate_ui_recommendations(
        self,
        issues: List[DesignIssue],
        ds: DesignSystemSpec
    ) -> List[str]:
        """Genera recomendaciones basadas en la auditoría."""
        recommendations = []

        # Verificar cantidad de colores
        if len(ds.colors) > 20:
            recommendations.append(
                f"🎨 Paleta de colores: Tienes {len(ds.colors)} colores. "
                "Considera consolidar a 8-12 colores base con variantes."
            )

        # Verificar fuentes
        if len(ds.fonts) > 3:
            recommendations.append(
                f"📝 Tipografía: Tienes {len(ds.fonts)} familias de fuente. "
                "Limita a 2-3 familias máximo para consistencia."
            )

        # Verificar contraste
        contrast_issues = [i for i in issues if i.type == DesignIssueType.CONTRAST]
        if contrast_issues:
            recommendations.append(
                f"👁️ Accesibilidad: {len(contrast_issues)} problemas de contraste. "
                "Revisa los colores para cumplir WCAG AA (4.5:1)."
            )

        # Verificar espaciados
        if len(ds.spacings) > 15:
            recommendations.append(
                "📐 Espaciados: Demasiados valores únicos. "
                "Adopta una escala de 8pt: 8, 16, 24, 32, 48, 64px."
            )

        # Verificar variables CSS
        recommendations.append(
            "💡 Tip: Usa CSS Custom Properties (--var) para colores, "
            "espaciados y tipografía para facilitar temas y mantenimiento."
        )

        if not issues:
            recommendations.append(
                "✅ ¡Excelente! No se encontraron problemas críticos de diseño."
            )

        return recommendations

    # ========================================
    # ANÁLISIS DE HTML/CANVAS
    # ========================================

    def analyze_html_structure(self, file_path: str) -> List[DesignIssue]:
        """
        Analiza estructura HTML para problemas de UI.

        Args:
            file_path: Ruta al archivo HTML

        Returns:
            Lista de problemas encontrados
        """
        issues = []
        path = Path(file_path)

        if not path.exists():
            return issues

        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Verificar imágenes sin alt
            img_pattern = r'<img[^>]*>'
            alt_pattern = r'alt\s*=\s*["\'][^"\']*["\']'

            for i, line in enumerate(lines, 1):
                imgs = re.findall(img_pattern, line, re.IGNORECASE)
                for img in imgs:
                    if not re.search(alt_pattern, img):
                        issues.append(DesignIssue(
                            id=self._generate_issue_id(),
                            type=DesignIssueType.ACCESSIBILITY,
                            severity=IssueSeverity.ERROR,
                            file_path=file_path,
                            line_number=i,
                            title="Imagen sin atributo alt",
                            description="Las imágenes deben tener texto alternativo para accesibilidad.",
                            suggestion="Añade alt='descripción de la imagen' a la etiqueta <img>.",
                            wcag_level="A"
                        ))

            # Verificar botones sin texto accesible
            button_pattern = r'<button[^>]*>[^<]*</button>'
            for i, line in enumerate(lines, 1):
                buttons = re.findall(button_pattern, line, re.IGNORECASE)
                for btn in buttons:
                    # Verificar si tiene texto o aria-label
                    inner = re.search(r'>([^<]*)<', btn)
                    has_aria = 'aria-label' in btn.lower()
                    has_text = inner and inner.group(1).strip()

                    if not has_text and not has_aria:
                        issues.append(DesignIssue(
                            id=self._generate_issue_id(),
                            type=DesignIssueType.ACCESSIBILITY,
                            severity=IssueSeverity.ERROR,
                            file_path=file_path,
                            line_number=i,
                            title="Botón sin texto accesible",
                            description="Los botones deben tener texto visible o aria-label.",
                            suggestion="Añade texto al botón o usa aria-label='acción del botón'.",
                            wcag_level="A"
                        ))

            # Verificar inputs sin labels
            input_pattern = r'<input[^>]*>'
            for i, line in enumerate(lines, 1):
                inputs = re.findall(input_pattern, line, re.IGNORECASE)
                for inp in inputs:
                    input_type = re.search(r'type\s*=\s*["\']([^"\']+)["\']', inp)
                    if input_type and input_type.group(1) in ['hidden', 'submit', 'button']:
                        continue

                    has_id = 'id=' in inp.lower()
                    has_aria = 'aria-label' in inp.lower() or 'aria-labelledby' in inp.lower()

                    if not has_id and not has_aria:
                        issues.append(DesignIssue(
                            id=self._generate_issue_id(),
                            type=DesignIssueType.ACCESSIBILITY,
                            severity=IssueSeverity.WARNING,
                            file_path=file_path,
                            line_number=i,
                            title="Input sin label asociado",
                            description="Los campos de formulario deben tener labels asociados.",
                            suggestion="Usa <label for='id'> o aria-label en el input.",
                            wcag_level="A"
                        ))

        except Exception as e:
            logger.error(f"Error analizando HTML {file_path}: {e}")

        return issues


# Instancia singleton
_ui_designer_instance: Optional[UIDesignerAgent] = None


def get_ui_designer_agent(project_root: str = ".") -> UIDesignerAgent:
    """Obtiene la instancia global del Agente UI Designer."""
    global _ui_designer_instance
    if _ui_designer_instance is None:
        _ui_designer_instance = UIDesignerAgent(project_root)
    return _ui_designer_instance
