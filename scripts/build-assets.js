#!/usr/bin/env node
/**
 * build-assets.js
 * Script de minificacion de assets JS/CSS para produccion
 *
 * Uso:
 *   node scripts/build-assets.js --js      # Solo JavaScript
 *   node scripts/build-assets.js --css     # Solo CSS
 *   node scripts/build-assets.js           # Todo (JS + CSS)
 *   node scripts/build-assets.js --watch   # Watch mode
 *
 * Genera:
 *   - Archivos .min.js y .min.css
 *   - Sourcemaps (.map)
 *   - Reporte de compresion
 */

const fs = require('fs');
const path = require('path');

// ============================================
// CONFIGURACION
// ============================================
const CONFIG = {
    // Directorios
    jsDir: path.join(__dirname, '..', 'static', 'js'),
    cssDir: path.join(__dirname, '..', 'static', 'css'),
    modulesDir: path.join(__dirname, '..', 'static', 'js', 'modules'),

    // Archivos JS principales a minificar
    jsFiles: [
        'app.js',
        'app-refactored.js',
        'enhanced-app.js',
        'modern-ui.js',
        'error-boundary.js',
        'lazy-loader.js',
        'image-optimizer.js'
    ],

    // Modulos ES6 a minificar
    jsModules: [
        'accessibility.js',
        'animation-loader.js',
        'chart-manager.js',
        'data-service.js',
        'event-delegation.js',
        'export-service.js',
        'i18n.js',
        'lazy-loader.js',
        'leave-requests-manager.js',
        'offline-storage.js',
        'sanitizer.js',
        'theme-manager.js',
        'ui-enhancements.js',
        'ui-manager.js',
        'utils.js',
        'virtual-table.js'
    ],

    // Archivos CSS a minificar (Updated 2025-01: unified design system)
    cssFiles: [
        'unified-design-system.css',
        'yukyu-tokens.css',
        'login-modal.css'
    ],

    // Archivos CSS de nexus-theme
    nexusThemeFiles: [
        'nexus-theme/main.css',
        'nexus-theme/variables.css',
        'nexus-theme/global.css',
        'nexus-theme/layout.css',
        'nexus-theme/components.css',
        'nexus-theme/animations.css'
    ],

    // Opciones de terser (minificador JS)
    terserOptions: {
        compress: {
            dead_code: true,
            drop_console: true,       // Eliminar console.log en produccion
            drop_debugger: true,
            ecma: 2020,
            passes: 2,
            pure_funcs: ['console.log', 'console.debug', 'console.info']
        },
        mangle: {
            toplevel: false,          // No renombrar exports de modulos
            safari10: true
        },
        format: {
            comments: false,          // Eliminar comentarios
            ecma: 2020
        },
        sourceMap: true
    },

    // Opciones de cssnano (minificador CSS)
    cssnanoOptions: {
        preset: ['default', {
            discardComments: { removeAll: true },
            normalizeWhitespace: true,
            colormin: true,
            minifyFontValues: true,
            minifyGradients: true,
            minifyParams: true,
            minifySelectors: true,
            mergeLonghand: true,
            mergeRules: true,
            reduceInitial: true,
            reduceTransforms: true
        }]
    }
};

// ============================================
// UTILIDADES
// ============================================
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function calculateSavings(original, minified) {
    const savings = original - minified;
    const percentage = ((savings / original) * 100).toFixed(1);
    return { savings, percentage };
}

function fileExists(filePath) {
    try {
        return fs.existsSync(filePath);
    } catch {
        return false;
    }
}

// ============================================
// MINIFICACION JS CON TERSER
// ============================================
async function minifyJavaScript() {
    console.log('\n========================================');
    console.log(' Minificando JavaScript con Terser');
    console.log('========================================\n');

    let terser;
    try {
        terser = require('terser');
    } catch (e) {
        console.error('Error: terser no esta instalado.');
        console.error('Ejecuta: npm install terser');
        process.exit(1);
    }

    const results = [];
    const errors = [];

    // Procesar archivos JS principales
    for (const file of CONFIG.jsFiles) {
        const inputPath = path.join(CONFIG.jsDir, file);
        const outputPath = path.join(CONFIG.jsDir, file.replace('.js', '.min.js'));
        const mapPath = outputPath + '.map';

        if (!fileExists(inputPath)) {
            console.log(`  [SKIP] ${file} - no existe`);
            continue;
        }

        try {
            const code = fs.readFileSync(inputPath, 'utf8');
            const originalSize = Buffer.byteLength(code, 'utf8');

            const result = await terser.minify(code, {
                ...CONFIG.terserOptions,
                sourceMap: {
                    filename: path.basename(outputPath),
                    url: path.basename(mapPath)
                }
            });

            if (result.error) {
                throw result.error;
            }

            fs.writeFileSync(outputPath, result.code);
            if (result.map) {
                fs.writeFileSync(mapPath, result.map);
            }

            const minifiedSize = Buffer.byteLength(result.code, 'utf8');
            const { savings, percentage } = calculateSavings(originalSize, minifiedSize);

            results.push({
                file,
                originalSize,
                minifiedSize,
                savings,
                percentage
            });

            console.log(`  [OK] ${file}`);
            console.log(`       ${formatBytes(originalSize)} -> ${formatBytes(minifiedSize)} (-${percentage}%)`);

        } catch (err) {
            errors.push({ file, error: err.message });
            console.error(`  [ERROR] ${file}: ${err.message}`);
        }
    }

    // Procesar modulos ES6
    console.log('\n  --- Modulos ES6 ---\n');

    for (const file of CONFIG.jsModules) {
        const inputPath = path.join(CONFIG.modulesDir, file);
        const outputPath = path.join(CONFIG.modulesDir, file.replace('.js', '.min.js'));
        const mapPath = outputPath + '.map';

        if (!fileExists(inputPath)) {
            console.log(`  [SKIP] modules/${file} - no existe`);
            continue;
        }

        try {
            const code = fs.readFileSync(inputPath, 'utf8');
            const originalSize = Buffer.byteLength(code, 'utf8');

            // Para modulos ES6, mantener la estructura de exports
            const moduleOptions = {
                ...CONFIG.terserOptions,
                module: true,
                sourceMap: {
                    filename: path.basename(outputPath),
                    url: path.basename(mapPath)
                }
            };

            const result = await terser.minify(code, moduleOptions);

            if (result.error) {
                throw result.error;
            }

            fs.writeFileSync(outputPath, result.code);
            if (result.map) {
                fs.writeFileSync(mapPath, result.map);
            }

            const minifiedSize = Buffer.byteLength(result.code, 'utf8');
            const { savings, percentage } = calculateSavings(originalSize, minifiedSize);

            results.push({
                file: `modules/${file}`,
                originalSize,
                minifiedSize,
                savings,
                percentage
            });

            console.log(`  [OK] modules/${file}`);
            console.log(`       ${formatBytes(originalSize)} -> ${formatBytes(minifiedSize)} (-${percentage}%)`);

        } catch (err) {
            errors.push({ file: `modules/${file}`, error: err.message });
            console.error(`  [ERROR] modules/${file}: ${err.message}`);
        }
    }

    return { results, errors };
}

// ============================================
// MINIFICACION CSS CON CSSNANO
// ============================================
async function minifyCSS() {
    console.log('\n========================================');
    console.log(' Minificando CSS con cssnano');
    console.log('========================================\n');

    let postcss, cssnano;
    try {
        postcss = require('postcss');
        cssnano = require('cssnano');
    } catch (e) {
        console.error('Error: postcss o cssnano no estan instalados.');
        console.error('Ejecuta: npm install postcss cssnano');
        process.exit(1);
    }

    const results = [];
    const errors = [];

    const processor = postcss([cssnano(CONFIG.cssnanoOptions)]);

    for (const file of CONFIG.cssFiles) {
        const inputPath = path.join(CONFIG.cssDir, file);
        const outputPath = path.join(CONFIG.cssDir, file.replace('.css', '.min.css'));
        const mapPath = outputPath + '.map';

        if (!fileExists(inputPath)) {
            console.log(`  [SKIP] ${file} - no existe`);
            continue;
        }

        try {
            const css = fs.readFileSync(inputPath, 'utf8');
            const originalSize = Buffer.byteLength(css, 'utf8');

            const result = await processor.process(css, {
                from: inputPath,
                to: outputPath,
                map: {
                    inline: false,
                    annotation: path.basename(mapPath)
                }
            });

            fs.writeFileSync(outputPath, result.css);
            if (result.map) {
                fs.writeFileSync(mapPath, result.map.toString());
            }

            const minifiedSize = Buffer.byteLength(result.css, 'utf8');
            const { savings, percentage } = calculateSavings(originalSize, minifiedSize);

            results.push({
                file,
                originalSize,
                minifiedSize,
                savings,
                percentage
            });

            console.log(`  [OK] ${file}`);
            console.log(`       ${formatBytes(originalSize)} -> ${formatBytes(minifiedSize)} (-${percentage}%)`);

        } catch (err) {
            errors.push({ file, error: err.message });
            console.error(`  [ERROR] ${file}: ${err.message}`);
        }
    }

    return { results, errors };
}

// ============================================
// GENERAR BUNDLE COMBINADO (OPCIONAL)
// ============================================
async function generateBundle() {
    console.log('\n========================================');
    console.log(' Generando bundles combinados');
    console.log('========================================\n');

    // Bundle de CSS critico
    const criticalCssFiles = [
        'main.css',
        'utilities-consolidated.css',
        'layout-utilities.css'
    ];

    let cssBundle = '';
    for (const file of criticalCssFiles) {
        const filePath = path.join(CONFIG.cssDir, file.replace('.css', '.min.css'));
        if (fileExists(filePath)) {
            cssBundle += fs.readFileSync(filePath, 'utf8') + '\n';
        }
    }

    if (cssBundle) {
        const bundlePath = path.join(CONFIG.cssDir, 'bundle.min.css');
        fs.writeFileSync(bundlePath, cssBundle);
        console.log(`  [OK] Creado bundle.min.css (${formatBytes(Buffer.byteLength(cssBundle))})`);
    }

    // Bundle de JS core
    const coreJsFiles = [
        'app.js'
    ];

    let jsBundle = '';
    for (const file of coreJsFiles) {
        const filePath = path.join(CONFIG.jsDir, file.replace('.js', '.min.js'));
        if (fileExists(filePath)) {
            jsBundle += fs.readFileSync(filePath, 'utf8') + '\n';
        }
    }

    if (jsBundle) {
        const bundlePath = path.join(CONFIG.jsDir, 'bundle.min.js');
        fs.writeFileSync(bundlePath, jsBundle);
        console.log(`  [OK] Creado bundle.min.js (${formatBytes(Buffer.byteLength(jsBundle))})`);
    }
}

// ============================================
// LIMPIAR ARCHIVOS MINIFICADOS
// ============================================
function cleanMinified() {
    console.log('\n========================================');
    console.log(' Limpiando archivos minificados');
    console.log('========================================\n');

    const patterns = [
        { dir: CONFIG.jsDir, ext: '.min.js' },
        { dir: CONFIG.jsDir, ext: '.min.js.map' },
        { dir: CONFIG.modulesDir, ext: '.min.js' },
        { dir: CONFIG.modulesDir, ext: '.min.js.map' },
        { dir: CONFIG.cssDir, ext: '.min.css' },
        { dir: CONFIG.cssDir, ext: '.min.css.map' }
    ];

    let count = 0;

    for (const { dir, ext } of patterns) {
        if (!fileExists(dir)) continue;

        const files = fs.readdirSync(dir).filter(f => f.endsWith(ext));
        for (const file of files) {
            const filePath = path.join(dir, file);
            fs.unlinkSync(filePath);
            console.log(`  [DEL] ${path.relative(path.join(__dirname, '..'), filePath)}`);
            count++;
        }
    }

    // Eliminar bundles
    const bundles = [
        path.join(CONFIG.jsDir, 'bundle.min.js'),
        path.join(CONFIG.cssDir, 'bundle.min.css')
    ];

    for (const bundle of bundles) {
        if (fileExists(bundle)) {
            fs.unlinkSync(bundle);
            console.log(`  [DEL] ${path.relative(path.join(__dirname, '..'), bundle)}`);
            count++;
        }
    }

    console.log(`\n  Total: ${count} archivos eliminados`);
}

// ============================================
// REPORTE FINAL
// ============================================
function printReport(jsResults, cssResults) {
    console.log('\n========================================');
    console.log(' REPORTE DE MINIFICACION');
    console.log('========================================\n');

    let totalOriginal = 0;
    let totalMinified = 0;

    // Combinar resultados
    const allResults = [
        ...(jsResults?.results || []),
        ...(cssResults?.results || [])
    ];

    for (const r of allResults) {
        totalOriginal += r.originalSize;
        totalMinified += r.minifiedSize;
    }

    const totalSavings = totalOriginal - totalMinified;
    const totalPercentage = totalOriginal > 0
        ? ((totalSavings / totalOriginal) * 100).toFixed(1)
        : 0;

    console.log('  Resumen:');
    console.log(`    Archivos procesados: ${allResults.length}`);
    console.log(`    Tamano original:     ${formatBytes(totalOriginal)}`);
    console.log(`    Tamano minificado:   ${formatBytes(totalMinified)}`);
    console.log(`    Ahorro total:        ${formatBytes(totalSavings)} (-${totalPercentage}%)`);

    // Errores
    const allErrors = [
        ...(jsResults?.errors || []),
        ...(cssResults?.errors || [])
    ];

    if (allErrors.length > 0) {
        console.log('\n  Errores:');
        for (const e of allErrors) {
            console.log(`    - ${e.file}: ${e.error}`);
        }
    }

    console.log('\n========================================\n');
}

// ============================================
// WATCH MODE
// ============================================
function watchMode() {
    console.log('\n========================================');
    console.log(' Modo Watch - Observando cambios');
    console.log('========================================\n');
    console.log('  Presiona Ctrl+C para detener\n');

    const chokidar = require('chokidar');

    const watcher = chokidar.watch([
        path.join(CONFIG.jsDir, '*.js'),
        path.join(CONFIG.modulesDir, '*.js'),
        path.join(CONFIG.cssDir, '*.css')
    ], {
        ignored: /\.min\.(js|css)(\.map)?$/,
        persistent: true
    });

    watcher.on('change', async (filePath) => {
        const ext = path.extname(filePath);
        const fileName = path.basename(filePath);

        console.log(`  [CHANGE] ${fileName}`);

        if (ext === '.js') {
            await minifyJavaScript();
        } else if (ext === '.css') {
            await minifyCSS();
        }
    });
}

// ============================================
// MAIN
// ============================================
async function main() {
    const args = process.argv.slice(2);

    console.log('\n  YuKyuDATA - Asset Minification Script');
    console.log('  =====================================');

    // Parsear argumentos
    const doJS = args.includes('--js') || args.length === 0;
    const doCSS = args.includes('--css') || args.length === 0;
    const doClean = args.includes('--clean');
    const doWatch = args.includes('--watch');
    const doBundle = args.includes('--bundle');

    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
  Uso: node scripts/build-assets.js [opciones]

  Opciones:
    --js       Minificar solo JavaScript
    --css      Minificar solo CSS
    --bundle   Generar bundles combinados
    --watch    Observar cambios y re-minificar
    --clean    Eliminar archivos minificados
    --help     Mostrar esta ayuda

  Sin opciones, minifica JS y CSS.

  Ejemplos:
    node scripts/build-assets.js           # Todo
    node scripts/build-assets.js --js      # Solo JS
    node scripts/build-assets.js --css     # Solo CSS
    node scripts/build-assets.js --clean   # Limpiar
    node scripts/build-assets.js --watch   # Watch mode
`);
        process.exit(0);
    }

    if (doClean) {
        cleanMinified();
        process.exit(0);
    }

    if (doWatch) {
        // Primera compilacion
        if (doJS) await minifyJavaScript();
        if (doCSS) await minifyCSS();
        // Luego watch
        watchMode();
        return;
    }

    let jsResults = null;
    let cssResults = null;

    if (doJS) {
        jsResults = await minifyJavaScript();
    }

    if (doCSS) {
        cssResults = await minifyCSS();
    }

    if (doBundle) {
        await generateBundle();
    }

    printReport(jsResults, cssResults);

    // Exit con error si hubo problemas
    const allErrors = [
        ...(jsResults?.errors || []),
        ...(cssResults?.errors || [])
    ];

    if (allErrors.length > 0) {
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Error fatal:', err);
    process.exit(1);
});
