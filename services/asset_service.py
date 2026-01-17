"""
Asset Service - Gestiona la carga de assets minificados/originales

Este servicio determina si usar assets minificados (.min.js, .min.css)
o los originales basandose en la variable de entorno USE_MINIFIED_ASSETS.

Uso:
    from services.asset_service import get_asset_url, get_all_css, get_all_js

    # Obtener URL de un asset individual
    js_url = get_asset_url('js/app.js')
    # Retorna 'js/app.min.js' en produccion

    # Obtener lista de CSS para el head
    css_files = get_all_css()

    # Obtener lista de JS para el body
    js_files = get_all_js()
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from functools import lru_cache


# Configuracion
USE_MINIFIED = os.environ.get('USE_MINIFIED_ASSETS', 'false').lower() == 'true'
STATIC_DIR = Path(__file__).parent.parent / 'static'


def get_asset_url(path: str, force_minified: Optional[bool] = None) -> str:
    """
    Retorna la URL del asset, minificada o no segun configuracion.

    Args:
        path: Ruta relativa del asset (ej: 'js/app.js')
        force_minified: Si se especifica, ignora la configuracion global

    Returns:
        URL del asset con o sin .min segun corresponda
    """
    use_min = force_minified if force_minified is not None else USE_MINIFIED

    if not use_min:
        return f'/static/{path}'

    # Determinar si es JS o CSS
    if path.endswith('.js') and not path.endswith('.min.js'):
        minified_path = path.replace('.js', '.min.js')
        # Verificar que el archivo minificado existe
        if (STATIC_DIR / minified_path.replace('/', os.sep)).exists():
            return f'/static/{minified_path}'

    elif path.endswith('.css') and not path.endswith('.min.css'):
        minified_path = path.replace('.css', '.min.css')
        if (STATIC_DIR / minified_path.replace('/', os.sep)).exists():
            return f'/static/{minified_path}'

    return f'/static/{path}'


@lru_cache(maxsize=1)
def get_all_css() -> List[Dict[str, str]]:
    """
    Retorna la lista de archivos CSS para cargar.

    Returns:
        Lista de diccionarios con 'href' y 'id' opcionales
    """
    css_files = [
        {'href': 'css/main.css', 'id': 'main-css'},
        {'href': 'css/utilities-consolidated.css'},
        {'href': 'css/layout-utilities.css'},
        {'href': 'css/ui-enhancements.css'},
        {'href': 'css/modern-2025.css'},
        {'href': 'css/responsive-enhancements.css'},
        {'href': 'css/premium-enhancements.css'},
        {'href': 'css/light-mode-premium.css'},
        {'href': 'css/premium-corporate.css'},
        {'href': 'css/sidebar-premium.css'},
        {'href': 'css/arari-glow.css'},
        {'href': 'css/theme-override.css'},
    ]

    result = []
    for css in css_files:
        url = get_asset_url(css['href'])
        item = {'href': url}
        if 'id' in css:
            item['id'] = css['id']
        result.append(item)

    return result


@lru_cache(maxsize=1)
def get_all_js() -> List[Dict[str, str]]:
    """
    Retorna la lista de archivos JS para cargar.

    Returns:
        Lista de diccionarios con 'src', 'type', 'defer', etc.
    """
    # JS principal
    main_js = [
        {'src': 'js/app.js', 'type': 'text/javascript', 'defer': True},
    ]

    # Modulos ES6
    modules = [
        {'src': 'js/modules/utils.js', 'type': 'module'},
        {'src': 'js/modules/sanitizer.js', 'type': 'module'},
        {'src': 'js/modules/data-service.js', 'type': 'module'},
        {'src': 'js/modules/chart-manager.js', 'type': 'module'},
        {'src': 'js/modules/ui-manager.js', 'type': 'module'},
        {'src': 'js/modules/ui-enhancements.js', 'type': 'module'},
        {'src': 'js/modules/theme-manager.js', 'type': 'module'},
        {'src': 'js/modules/i18n.js', 'type': 'module'},
        {'src': 'js/modules/accessibility.js', 'type': 'module'},
        {'src': 'js/modules/offline-storage.js', 'type': 'module'},
        {'src': 'js/modules/virtual-table.js', 'type': 'module'},
        {'src': 'js/modules/lazy-loader.js', 'type': 'module'},
        {'src': 'js/modules/event-delegation.js', 'type': 'module'},
        {'src': 'js/modules/leave-requests-manager.js', 'type': 'module'},
        {'src': 'js/modules/export-service.js', 'type': 'module'},
    ]

    result = []

    for js in main_js:
        item = {'src': get_asset_url(js['src'])}
        if 'type' in js:
            item['type'] = js['type']
        if js.get('defer'):
            item['defer'] = True
        result.append(item)

    for js in modules:
        item = {'src': get_asset_url(js['src'])}
        if 'type' in js:
            item['type'] = js['type']
        result.append(item)

    return result


def get_asset_manifest() -> Dict[str, str]:
    """
    Lee el manifest de assets generado durante el build.

    Returns:
        Diccionario con checksums de archivos
    """
    manifest_path = STATIC_DIR / 'asset-manifest.txt'
    manifest = {}

    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        checksum = parts[0]
                        filepath = ' '.join(parts[1:])
                        manifest[filepath] = checksum

    return manifest


def get_cache_busting_url(path: str) -> str:
    """
    Genera URL con query string para cache busting.

    Args:
        path: Ruta del asset

    Returns:
        URL con ?v=checksum para invalidar cache
    """
    url = get_asset_url(path)
    manifest = get_asset_manifest()

    # Buscar checksum en manifest
    full_path = STATIC_DIR / path.replace('/', os.sep)
    if str(full_path) in manifest:
        checksum = manifest[str(full_path)][:8]
        return f'{url}?v={checksum}'

    return url


def is_minified_mode() -> bool:
    """Retorna True si estamos usando assets minificados."""
    return USE_MINIFIED


def get_environment_info() -> Dict[str, any]:
    """
    Retorna informacion sobre la configuracion de assets.

    Returns:
        Diccionario con informacion del entorno
    """
    return {
        'use_minified': USE_MINIFIED,
        'static_dir': str(STATIC_DIR),
        'manifest_exists': (STATIC_DIR / 'asset-manifest.txt').exists(),
        'css_count': len(get_all_css()),
        'js_count': len(get_all_js()),
    }
