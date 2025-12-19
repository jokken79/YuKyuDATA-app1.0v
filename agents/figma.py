"""
Figma Agent - Agente Especialista en Integración con Figma
==========================================================

Experto en flujos de trabajo Figma y Design Systems:
- Exportación de Design Tokens (variables Figma)
- Generación de especificaciones de componentes
- Sincronización de Design System CSS <-> Figma
- Análisis de consistencia de estilos
- Generación de documentación visual
- Conversión CSS a Figma Styles
- Exportación de iconos y assets
- Generación de Figma API payloads
"""

import logging
import re
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from colorsys import rgb_to_hls, hls_to_rgb

logger = logging.getLogger(__name__)


class FigmaTokenType(Enum):
    """Tipos de tokens de Figma."""
    COLOR = "color"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    BORDER_RADIUS = "borderRadius"
    SHADOW = "shadow"
    OPACITY = "opacity"
    SIZING = "sizing"
    FONT_FAMILY = "fontFamily"
    FONT_WEIGHT = "fontWeight"
    LINE_HEIGHT = "lineHeight"
    LETTER_SPACING = "letterSpacing"


class FigmaComponentType(Enum):
    """Tipos de componentes Figma."""
    BUTTON = "button"
    INPUT = "input"
    CARD = "card"
    MODAL = "modal"
    BADGE = "badge"
    TOAST = "toast"
    TABLE = "table"
    NAV = "navigation"
    ICON = "icon"
    AVATAR = "avatar"


@dataclass
class FigmaColor:
    """Representación de color compatible con Figma."""
    name: str
    hex: str
    rgba: Tuple[float, float, float, float]  # 0-1 normalized
    description: str = ""

    def to_figma_paint(self) -> Dict:
        """Convierte a formato Figma Paint."""
        r, g, b, a = self.rgba
        return {
            "type": "SOLID",
            "visible": True,
            "opacity": a,
            "blendMode": "NORMAL",
            "color": {"r": r, "g": g, "b": b}
        }

    def to_figma_variable(self) -> Dict:
        """Convierte a formato Figma Variable."""
        r, g, b, a = self.rgba
        return {
            "name": self.name,
            "resolvedType": "COLOR",
            "valuesByMode": {
                "default": {"r": r, "g": g, "b": b, "a": a}
            },
            "description": self.description
        }


@dataclass
class FigmaTypographyStyle:
    """Estilo de tipografía compatible con Figma."""
    name: str
    font_family: str
    font_weight: int
    font_size: float
    line_height: float
    letter_spacing: float
    description: str = ""

    def to_figma_style(self) -> Dict:
        """Convierte a formato Figma Text Style."""
        return {
            "name": self.name,
            "styleType": "TEXT",
            "fontName": {
                "family": self.font_family,
                "style": self._weight_to_style()
            },
            "fontSize": self.font_size,
            "lineHeight": {
                "unit": "PIXELS",
                "value": self.line_height
            },
            "letterSpacing": {
                "unit": "PIXELS",
                "value": self.letter_spacing
            },
            "description": self.description
        }

    def _weight_to_style(self) -> str:
        """Convierte peso numérico a estilo Figma."""
        weight_map = {
            100: "Thin",
            200: "ExtraLight",
            300: "Light",
            400: "Regular",
            500: "Medium",
            600: "SemiBold",
            700: "Bold",
            800: "ExtraBold",
            900: "Black"
        }
        return weight_map.get(self.font_weight, "Regular")


@dataclass
class FigmaComponent:
    """Especificación de componente para Figma."""
    name: str
    type: FigmaComponentType
    description: str
    properties: Dict[str, Any]
    variants: List[Dict[str, Any]] = field(default_factory=list)
    auto_layout: Optional[Dict] = None

    def to_figma_component(self) -> Dict:
        """Convierte a especificación de componente Figma."""
        component = {
            "name": self.name,
            "type": "COMPONENT",
            "description": self.description,
            "componentPropertyDefinitions": self.properties
        }

        if self.auto_layout:
            component["layoutMode"] = self.auto_layout.get("mode", "VERTICAL")
            component["primaryAxisSizingMode"] = self.auto_layout.get("primarySizing", "AUTO")
            component["counterAxisSizingMode"] = self.auto_layout.get("counterSizing", "AUTO")
            component["paddingLeft"] = self.auto_layout.get("paddingLeft", 0)
            component["paddingRight"] = self.auto_layout.get("paddingRight", 0)
            component["paddingTop"] = self.auto_layout.get("paddingTop", 0)
            component["paddingBottom"] = self.auto_layout.get("paddingBottom", 0)
            component["itemSpacing"] = self.auto_layout.get("itemSpacing", 0)

        return component


@dataclass
class FigmaDesignTokens:
    """Colección completa de tokens de diseño para Figma."""
    colors: Dict[str, FigmaColor] = field(default_factory=dict)
    typography: Dict[str, FigmaTypographyStyle] = field(default_factory=dict)
    spacing: Dict[str, float] = field(default_factory=dict)
    border_radius: Dict[str, float] = field(default_factory=dict)
    shadows: Dict[str, List[Dict]] = field(default_factory=dict)

    def to_tokens_studio_format(self) -> Dict:
        """Exporta en formato Tokens Studio (plugin Figma)."""
        tokens = {
            "$themes": [],
            "$metadata": {
                "tokenSetOrder": ["global", "light", "dark"]
            },
            "global": {}
        }

        # Colors
        if self.colors:
            tokens["global"]["color"] = {}
            for name, color in self.colors.items():
                tokens["global"]["color"][name] = {
                    "value": color.hex,
                    "type": "color",
                    "description": color.description
                }

        # Typography
        if self.typography:
            tokens["global"]["typography"] = {}
            for name, typo in self.typography.items():
                tokens["global"]["typography"][name] = {
                    "value": {
                        "fontFamily": typo.font_family,
                        "fontWeight": str(typo.font_weight),
                        "fontSize": f"{typo.font_size}px",
                        "lineHeight": f"{typo.line_height}px",
                        "letterSpacing": f"{typo.letter_spacing}px"
                    },
                    "type": "typography",
                    "description": typo.description
                }

        # Spacing
        if self.spacing:
            tokens["global"]["spacing"] = {}
            for name, value in self.spacing.items():
                tokens["global"]["spacing"][name] = {
                    "value": f"{value}px",
                    "type": "spacing"
                }

        # Border Radius
        if self.border_radius:
            tokens["global"]["borderRadius"] = {}
            for name, value in self.border_radius.items():
                tokens["global"]["borderRadius"][name] = {
                    "value": f"{value}px",
                    "type": "borderRadius"
                }

        # Shadows
        if self.shadows:
            tokens["global"]["shadow"] = {}
            for name, shadow_list in self.shadows.items():
                tokens["global"]["shadow"][name] = {
                    "value": shadow_list,
                    "type": "boxShadow"
                }

        return tokens


class FigmaAgent:
    """
    Agente especializado en integración con Figma.

    Capacidades:
    - Extracción de tokens de CSS
    - Generación de archivos de tokens para Tokens Studio
    - Especificación de componentes
    - Sincronización de estilos
    - Generación de documentación
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.tokens = FigmaDesignTokens()
        self.components: List[FigmaComponent] = []
        self.analysis_timestamp = None

        # Patrones para parsing CSS
        self._css_var_pattern = re.compile(r'--([a-zA-Z0-9-]+):\s*([^;]+);')
        self._color_hex_pattern = re.compile(r'#([0-9a-fA-F]{3,8})\b')
        self._color_rgb_pattern = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)')
        self._font_pattern = re.compile(r"font-family:\s*([^;]+);")
        self._size_pattern = re.compile(r'(\d+(?:\.\d+)?)(px|rem|em|%)')

    def extract_tokens_from_css(self, css_content: str, source_file: str = "") -> FigmaDesignTokens:
        """
        Extrae tokens de diseño de contenido CSS.

        Args:
            css_content: Contenido CSS a analizar
            source_file: Nombre del archivo fuente

        Returns:
            FigmaDesignTokens con los tokens extraídos
        """
        tokens = FigmaDesignTokens()

        # Extraer variables CSS
        for match in self._css_var_pattern.finditer(css_content):
            var_name = match.group(1)
            var_value = match.group(2).strip()

            # Detectar tipo de token
            if self._is_color(var_value):
                color = self._parse_color(var_value)
                if color:
                    tokens.colors[var_name] = FigmaColor(
                        name=var_name,
                        hex=color['hex'],
                        rgba=color['rgba'],
                        description=f"Extracted from {source_file}"
                    )

            elif 'px' in var_value or 'rem' in var_value:
                px_value = self._parse_size(var_value)
                if px_value:
                    if 'radius' in var_name.lower():
                        tokens.border_radius[var_name] = px_value
                    elif any(x in var_name.lower() for x in ['gap', 'space', 'padding', 'margin']):
                        tokens.spacing[var_name] = px_value

        self.tokens = tokens
        return tokens

    def analyze_css_files(self, css_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analiza archivos CSS del proyecto y extrae tokens.

        Args:
            css_paths: Lista de rutas CSS (si None, busca automáticamente)

        Returns:
            Diccionario con análisis completo
        """
        self.analysis_timestamp = datetime.now().isoformat()

        if css_paths is None:
            css_paths = list(self.project_root.rglob("*.css"))
        else:
            css_paths = [Path(p) for p in css_paths]

        all_tokens = FigmaDesignTokens()
        files_analyzed = []

        for css_path in css_paths:
            try:
                if not css_path.exists():
                    continue

                content = css_path.read_text(encoding='utf-8', errors='ignore')
                file_tokens = self.extract_tokens_from_css(content, str(css_path))

                # Merge tokens
                all_tokens.colors.update(file_tokens.colors)
                all_tokens.typography.update(file_tokens.typography)
                all_tokens.spacing.update(file_tokens.spacing)
                all_tokens.border_radius.update(file_tokens.border_radius)
                all_tokens.shadows.update(file_tokens.shadows)

                files_analyzed.append(str(css_path))

            except Exception as e:
                logger.error(f"Error analyzing {css_path}: {e}")

        self.tokens = all_tokens

        return {
            "timestamp": self.analysis_timestamp,
            "files_analyzed": files_analyzed,
            "token_counts": {
                "colors": len(all_tokens.colors),
                "typography": len(all_tokens.typography),
                "spacing": len(all_tokens.spacing),
                "border_radius": len(all_tokens.border_radius),
                "shadows": len(all_tokens.shadows)
            },
            "tokens": all_tokens
        }

    def generate_component_spec(
        self,
        component_type: FigmaComponentType,
        css_class: str,
        css_content: str
    ) -> FigmaComponent:
        """
        Genera especificación de componente Figma desde CSS.

        Args:
            component_type: Tipo de componente
            css_class: Clase CSS principal
            css_content: Contenido CSS del componente

        Returns:
            FigmaComponent con especificación
        """
        # Extraer propiedades del CSS
        properties = {}

        # Padding
        padding_match = re.search(r'padding:\s*([^;]+);', css_content)
        if padding_match:
            properties["padding"] = padding_match.group(1)

        # Border radius
        radius_match = re.search(r'border-radius:\s*([^;]+);', css_content)
        if radius_match:
            properties["borderRadius"] = radius_match.group(1)

        # Background
        bg_match = re.search(r'background(?:-color)?:\s*([^;]+);', css_content)
        if bg_match:
            properties["background"] = bg_match.group(1)

        # Border
        border_match = re.search(r'border:\s*([^;]+);', css_content)
        if border_match:
            properties["border"] = border_match.group(1)

        component = FigmaComponent(
            name=css_class.replace('.', '').replace('-', ' ').title(),
            type=component_type,
            description=f"Component based on CSS class: {css_class}",
            properties=properties,
            auto_layout={
                "mode": "HORIZONTAL",
                "primarySizing": "HUG",
                "counterSizing": "HUG",
                "paddingLeft": 16,
                "paddingRight": 16,
                "paddingTop": 12,
                "paddingBottom": 12,
                "itemSpacing": 8
            }
        )

        self.components.append(component)
        return component

    def export_tokens_studio(self, output_path: str = "tokens.json") -> str:
        """
        Exporta tokens en formato Tokens Studio para Figma.

        Args:
            output_path: Ruta de salida

        Returns:
            Ruta del archivo generado
        """
        output = Path(self.project_root) / output_path
        tokens_data = self.tokens.to_tokens_studio_format()

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(tokens_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Tokens exported to {output}")
        return str(output)

    def export_figma_variables(self, output_path: str = "figma-variables.json") -> str:
        """
        Exporta variables en formato nativo de Figma.

        Args:
            output_path: Ruta de salida

        Returns:
            Ruta del archivo generado
        """
        output = Path(self.project_root) / output_path

        variables = {
            "version": "1.0",
            "collections": [
                {
                    "name": "Design System",
                    "modes": ["Light", "Dark"],
                    "variables": []
                }
            ]
        }

        # Agregar colores
        for name, color in self.tokens.colors.items():
            variables["collections"][0]["variables"].append(
                color.to_figma_variable()
            )

        # Agregar spacing
        for name, value in self.tokens.spacing.items():
            variables["collections"][0]["variables"].append({
                "name": f"spacing/{name}",
                "resolvedType": "FLOAT",
                "valuesByMode": {"default": value},
                "description": f"Spacing: {value}px"
            })

        # Agregar border radius
        for name, value in self.tokens.border_radius.items():
            variables["collections"][0]["variables"].append({
                "name": f"radius/{name}",
                "resolvedType": "FLOAT",
                "valuesByMode": {"default": value},
                "description": f"Border radius: {value}px"
            })

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(variables, f, indent=2, ensure_ascii=False)

        logger.info(f"Figma variables exported to {output}")
        return str(output)

    def generate_style_dictionary(self, output_path: str = "style-dictionary.json") -> str:
        """
        Genera archivo Style Dictionary compatible con Figma.

        Args:
            output_path: Ruta de salida

        Returns:
            Ruta del archivo generado
        """
        output = Path(self.project_root) / output_path

        sd_tokens = {
            "color": {},
            "size": {},
            "font": {},
            "spacing": {},
            "borderRadius": {}
        }

        # Colores
        for name, color in self.tokens.colors.items():
            category = "primary" if "primary" in name else (
                "secondary" if "secondary" in name else (
                    "neutral" if any(x in name for x in ["text", "bg", "muted"]) else "other"
                )
            )
            if category not in sd_tokens["color"]:
                sd_tokens["color"][category] = {}
            sd_tokens["color"][category][name] = {
                "value": color.hex,
                "type": "color"
            }

        # Spacing
        for name, value in self.tokens.spacing.items():
            sd_tokens["spacing"][name] = {
                "value": f"{value}px",
                "type": "dimension"
            }

        # Border Radius
        for name, value in self.tokens.border_radius.items():
            sd_tokens["borderRadius"][name] = {
                "value": f"{value}px",
                "type": "dimension"
            }

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(sd_tokens, f, indent=2, ensure_ascii=False)

        logger.info(f"Style Dictionary exported to {output}")
        return str(output)

    def generate_component_documentation(self) -> Dict[str, Any]:
        """
        Genera documentación de componentes para Figma.

        Returns:
            Documentación estructurada de componentes
        """
        docs = {
            "generated_at": datetime.now().isoformat(),
            "components": []
        }

        for comp in self.components:
            docs["components"].append({
                "name": comp.name,
                "type": comp.type.value,
                "description": comp.description,
                "figma_spec": comp.to_figma_component(),
                "variants": comp.variants
            })

        return docs

    def sync_design_system(self, css_paths: List[str]) -> Dict[str, Any]:
        """
        Sincroniza Design System completo para Figma.

        Args:
            css_paths: Lista de archivos CSS

        Returns:
            Resultado de sincronización
        """
        # Analizar CSS
        analysis = self.analyze_css_files(css_paths)

        # Exportar tokens
        tokens_path = self.export_tokens_studio()
        variables_path = self.export_figma_variables()
        sd_path = self.generate_style_dictionary()

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "files_processed": len(analysis["files_analyzed"]),
                "tokens_extracted": analysis["token_counts"]
            },
            "exports": {
                "tokens_studio": tokens_path,
                "figma_variables": variables_path,
                "style_dictionary": sd_path
            },
            "recommendations": self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones para mejorar el Design System."""
        recommendations = []

        if len(self.tokens.colors) > 20:
            recommendations.append(
                f"Tienes {len(self.tokens.colors)} colores. Considera consolidar a 12-15 colores principales."
            )

        if len(self.tokens.colors) < 5:
            recommendations.append(
                "Pocos colores definidos. Añade variantes para estados (hover, active, disabled)."
            )

        if not self.tokens.typography:
            recommendations.append(
                "No se detectaron estilos de tipografía. Define font-family y tamaños en variables CSS."
            )

        if not self.tokens.spacing:
            recommendations.append(
                "No se detectaron tokens de espaciado. Usa una escala consistente (4, 8, 12, 16, 24, 32, 48)."
            )

        return recommendations

    def _is_color(self, value: str) -> bool:
        """Verifica si un valor es un color."""
        value = value.strip().lower()
        return (
            value.startswith('#') or
            value.startswith('rgb') or
            value.startswith('hsl') or
            value in ['transparent', 'inherit', 'currentcolor']
        )

    def _parse_color(self, value: str) -> Optional[Dict]:
        """Parsea un valor de color a formato normalizado."""
        value = value.strip()

        # HEX
        hex_match = self._color_hex_pattern.search(value)
        if hex_match:
            hex_color = hex_match.group(1)
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            if len(hex_color) == 6:
                hex_color += 'ff'

            r = int(hex_color[0:2], 16) / 255
            g = int(hex_color[2:4], 16) / 255
            b = int(hex_color[4:6], 16) / 255
            a = int(hex_color[6:8], 16) / 255 if len(hex_color) >= 8 else 1.0

            return {
                "hex": f"#{hex_color[:6]}",
                "rgba": (r, g, b, a)
            }

        # RGBA
        rgba_match = self._color_rgb_pattern.search(value)
        if rgba_match:
            r = int(rgba_match.group(1)) / 255
            g = int(rgba_match.group(2)) / 255
            b = int(rgba_match.group(3)) / 255
            a = float(rgba_match.group(4)) if rgba_match.group(4) else 1.0

            hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

            return {
                "hex": hex_color,
                "rgba": (r, g, b, a)
            }

        return None

    def _parse_size(self, value: str) -> Optional[float]:
        """Parsea un valor de tamaño a píxeles."""
        match = self._size_pattern.search(value)
        if match:
            num = float(match.group(1))
            unit = match.group(2)

            if unit == 'px':
                return num
            elif unit == 'rem':
                return num * 16
            elif unit == 'em':
                return num * 16
            elif unit == '%':
                return num

        return None


# Singleton para acceso global
_figma_agent_instance: Optional[FigmaAgent] = None


def get_figma_agent(project_root: str = ".") -> FigmaAgent:
    """Obtiene instancia singleton del FigmaAgent."""
    global _figma_agent_instance
    if _figma_agent_instance is None:
        _figma_agent_instance = FigmaAgent(project_root)
    return _figma_agent_instance


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Crear agente
    figma = FigmaAgent()

    # Analizar CSS
    result = figma.analyze_css_files([
        "static/css/main.css",
        "static/css/theme-override.css"
    ])

    print(f"Colores extraídos: {result['token_counts']['colors']}")
    print(f"Espaciados extraídos: {result['token_counts']['spacing']}")

    # Exportar tokens
    figma.export_tokens_studio("design-tokens.json")
    figma.export_figma_variables("figma-variables.json")

    print("Tokens exportados correctamente!")
