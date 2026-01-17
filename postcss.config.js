/**
 * PostCSS Configuration
 * Usado para minificacion CSS con cssnano
 *
 * Este archivo es leido por postcss-cli si se usa directamente.
 * El script build-assets.js usa su propia configuracion.
 */

module.exports = {
    plugins: [
        require('cssnano')({
            preset: ['default', {
                // Eliminar todos los comentarios
                discardComments: {
                    removeAll: true,
                },
                // Normalizar espacios en blanco
                normalizeWhitespace: true,
                // Optimizar colores
                colormin: true,
                // Optimizar fuentes
                minifyFontValues: true,
                // Optimizar gradientes
                minifyGradients: true,
                // Optimizar parametros
                minifyParams: true,
                // Optimizar selectores
                minifySelectors: true,
                // Combinar propiedades
                mergeLonghand: true,
                // Combinar reglas
                mergeRules: true,
                // Reducir initial
                reduceInitial: true,
                // Reducir transforms
                reduceTransforms: true,
                // Eliminar duplicados
                discardDuplicates: true,
                // Eliminar reglas vacias
                discardEmpty: true,
                // Normalizar charset
                normalizeCharset: true,
                // Ordenar media queries
                cssDeclarationSorter: {
                    order: 'smacss'
                },
                // Calc - evaluar donde sea posible
                calc: true,
            }]
        })
    ],
    // Generar sourcemaps
    map: {
        inline: false,
        annotation: true
    }
};
