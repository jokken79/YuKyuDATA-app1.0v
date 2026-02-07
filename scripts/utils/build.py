#!/usr/bin/env python3
"""
Build Script - Minificación y optimización de assets
Versión simple sin dependencias externas complejas
"""

import os
import re
import sys
from pathlib import Path
import gzip
import shutil

# Directorios
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / 'static'
CSS_DIR = STATIC_DIR / 'css'
JS_DIR = STATIC_DIR / 'js'
BUILD_DIR = BASE_DIR / 'build'


def minify_css(css_content):
    """
    Minifica CSS simple sin dependencias externas
    - Elimina comentarios
    - Elimina espacios en blanco excesivos
    - Elimina líneas vacías
    """
    # Eliminar comentarios /* ... */
    css_content = re.sub(r'/\*[\s\S]*?\*/', '', css_content)

    # Eliminar espacios múltiples
    css_content = re.sub(r'\s+', ' ', css_content)

    # Eliminar espacios alrededor de caracteres especiales
    css_content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', css_content)

    # Eliminar espacio antes de !important
    css_content = re.sub(r'\s*!\s*important', '!important', css_content)

    # Eliminar último ;
    css_content = re.sub(r';}', '}', css_content)

    return css_content.strip()


def minify_js_simple(js_content):
    """
    Minifica JS de manera simple
    - Elimina comentarios de línea
    - Elimina comentarios de bloque
    - Elimina espacios en blanco excesivos (preservando strings)
    """
    # Eliminar comentarios de bloque /* ... */
    js_content = re.sub(r'/\*[\s\S]*?\*/', '', js_content)

    # Eliminar comentarios de línea // ... (pero no URLs como https://)
    js_content = re.sub(r'(?<!:)//[^\n]*', '', js_content)

    # Eliminar líneas vacías
    js_content = re.sub(r'\n\s*\n', '\n', js_content)

    # Eliminar espacios al inicio y fin de línea
    js_content = re.sub(r'^\s+|\s+$', '', js_content, flags=re.MULTILINE)

    # Eliminar espacios múltiples (excepto en strings)
    # Esto es una aproximación simple
    lines = []
    for line in js_content.split('\n'):
        # Si la línea parece tener strings, preservarla
        if '"' in line or "'" in line:
            lines.append(line)
        else:
            # Reducir espacios múltiples
            line = re.sub(r'\s+', ' ', line)
            lines.append(line)

    return '\n'.join(lines)


def create_gzip(file_path):
    """Crea versión gzip del archivo para servidores que lo soporten"""
    gz_path = str(file_path) + '.gz'
    with open(file_path, 'rb') as f_in:
        with gzip.open(gz_path, 'wb', compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
    return gz_path


def calculate_savings(original_size, minified_size):
    """Calcula el ahorro de tamaño"""
    savings = original_size - minified_size
    percentage = (savings / original_size * 100) if original_size > 0 else 0
    return savings, percentage


def format_size(size_bytes):
    """Formatea tamaño en bytes a KB"""
    return f"{size_bytes / 1024:.2f} KB"


def build_css():
    """Construye y minifica archivos CSS"""
    print("\n📦 Minificando CSS...")

    css_files = list(CSS_DIR.glob('**/*.css'))

    if not css_files:
        print("⚠️  No se encontraron archivos CSS")
        return

    total_original = 0
    total_minified = 0

    for css_file in css_files:
        # Leer archivo original
        with open(css_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_size = len(original_content.encode('utf-8'))
        total_original += original_size

        # Minificar
        minified_content = minify_css(original_content)
        minified_size = len(minified_content.encode('utf-8'))
        total_minified += minified_size

        # Guardar versión minificada
        relative_path = css_file.relative_to(CSS_DIR)
        output_path = BUILD_DIR / 'css' / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar con .min.css
        min_output_path = output_path.with_name(
            output_path.stem + '.min' + output_path.suffix
        )

        with open(min_output_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)

        # Crear versión gzip
        gz_path = create_gzip(min_output_path)
        gz_size = os.path.getsize(gz_path)

        # Calcular ahorros
        savings, percentage = calculate_savings(original_size, minified_size)

        print(f"  ✓ {css_file.name}")
        print(f"    Original:  {format_size(original_size)}")
        print(f"    Minified:  {format_size(minified_size)} (-{percentage:.1f}%)")
        print(f"    Gzipped:   {format_size(gz_size)}")

    total_savings, total_percentage = calculate_savings(total_original, total_minified)
    print(f"\n  📊 Total CSS: {format_size(total_original)} → {format_size(total_minified)} (-{total_percentage:.1f}%)")


def build_js():
    """Construye y minifica archivos JavaScript"""
    print("\n📦 Minificando JavaScript...")

    # Solo minificar archivos principales, no módulos (para preservar imports)
    js_files = [
        JS_DIR / 'app.js',
        JS_DIR / 'modern-ui.js',
    ]

    # Filtrar archivos que existen
    js_files = [f for f in js_files if f.exists()]

    if not js_files:
        print("⚠️  No se encontraron archivos JS principales")
        return

    total_original = 0
    total_minified = 0

    for js_file in js_files:
        # Leer archivo original
        with open(js_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_size = len(original_content.encode('utf-8'))
        total_original += original_size

        # Minificar
        minified_content = minify_js_simple(original_content)
        minified_size = len(minified_content.encode('utf-8'))
        total_minified += minified_size

        # Guardar versión minificada
        output_path = BUILD_DIR / 'js' / js_file.name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Guardar con .min.js
        min_output_path = output_path.with_name(
            output_path.stem + '.min' + output_path.suffix
        )

        with open(min_output_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)

        # Crear versión gzip
        gz_path = create_gzip(min_output_path)
        gz_size = os.path.getsize(gz_path)

        # Calcular ahorros
        savings, percentage = calculate_savings(original_size, minified_size)

        print(f"  ✓ {js_file.name}")
        print(f"    Original:  {format_size(original_size)}")
        print(f"    Minified:  {format_size(minified_size)} (-{percentage:.1f}%)")
        print(f"    Gzipped:   {format_size(gz_size)}")

    total_savings, total_percentage = calculate_savings(total_original, total_minified)
    print(f"\n  📊 Total JS: {format_size(total_original)} → {format_size(total_minified)} (-{total_percentage:.1f}%)")


def build_modules():
    """Copia módulos JS sin minificar (preservar ESM)"""
    print("\n📦 Copiando módulos JavaScript...")

    modules_dir = JS_DIR / 'modules'
    if not modules_dir.exists():
        print("⚠️  No se encontró directorio de módulos")
        return

    module_files = list(modules_dir.glob('*.js'))
    output_modules_dir = BUILD_DIR / 'js' / 'modules'
    output_modules_dir.mkdir(parents=True, exist_ok=True)

    for module_file in module_files:
        # Copiar sin minificar para preservar imports/exports
        output_path = output_modules_dir / module_file.name
        shutil.copy2(module_file, output_path)

        # Crear versión gzip
        create_gzip(output_path)

        file_size = os.path.getsize(module_file)
        print(f"  ✓ {module_file.name} ({format_size(file_size)})")


def clean_build_dir():
    """Limpia el directorio de build"""
    if BUILD_DIR.exists():
        print("🧹 Limpiando directorio de build...")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(exist_ok=True)


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 YuKyuDATA Build Script")
    print("=" * 60)

    # Verificar directorios
    if not STATIC_DIR.exists():
        print("❌ Error: No se encontró el directorio static/")
        sys.exit(1)

    # Limpiar build anterior
    clean_build_dir()

    # Construir assets
    try:
        build_css()
        build_js()
        build_modules()

        print("\n" + "=" * 60)
        print("✅ Build completado exitosamente")
        print("=" * 60)
        print(f"\n📁 Archivos generados en: {BUILD_DIR}")
        print("\n💡 Uso:")
        print("   - Los archivos .min.* son las versiones minificadas")
        print("   - Los archivos .gz son para servidores con gzip habilitado")
        print("   - Los módulos están en build/js/modules/")

    except Exception as e:
        print(f"\n❌ Error durante el build: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
