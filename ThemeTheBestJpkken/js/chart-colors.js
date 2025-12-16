/**
 * ============================================
 * THEME CHART COLORS - Arari Style Vibrant
 * ============================================
 *
 * Colores vibrantes estilo Arari para gráficos
 * Cyan/Blue/Purple palette con efectos glow
 */

const ChartColors = {
    // ========================================
    // PRIMARY PALETTE - Colores principales
    // ========================================
    primary: {
        cyan: '#06b6d4',           // Cyan vibrante (principal)
        blue: '#3b82f6',           // Azul brillante
        purple: '#8b5cf6',         // Púrpura
        green: '#34d399',          // Verde éxito
        warning: '#fbbf24',        // Amarillo/dorado advertencia
        danger: '#f87171',         // Rojo peligro
        indigo: '#6366f1',         // Índigo
    },

    // ========================================
    // RGBA VARIANTS - Con transparencias
    // ========================================
    rgba: {
        // Cyan variants
        cyan10: 'rgba(6, 182, 212, 0.1)',
        cyan20: 'rgba(6, 182, 212, 0.2)',
        cyan30: 'rgba(6, 182, 212, 0.3)',
        cyan50: 'rgba(6, 182, 212, 0.5)',
        cyan70: 'rgba(6, 182, 212, 0.7)',

        // Blue variants
        blue10: 'rgba(59, 130, 246, 0.1)',
        blue20: 'rgba(59, 130, 246, 0.2)',
        blue30: 'rgba(59, 130, 246, 0.3)',
        blue50: 'rgba(59, 130, 246, 0.5)',

        // Purple variants
        purple10: 'rgba(139, 92, 246, 0.1)',
        purple20: 'rgba(139, 92, 246, 0.2)',
        purple50: 'rgba(139, 92, 246, 0.5)',

        // Green variants
        green10: 'rgba(52, 211, 153, 0.1)',
        green20: 'rgba(52, 211, 153, 0.2)',
        green50: 'rgba(52, 211, 153, 0.5)',

        // Warning variants
        warning10: 'rgba(251, 191, 36, 0.1)',
        warning20: 'rgba(251, 191, 36, 0.2)',
        warning30: 'rgba(251, 191, 36, 0.3)',
        warning70: 'rgba(251, 191, 36, 0.7)',

        // Danger variants
        danger10: 'rgba(248, 113, 113, 0.1)',
        danger20: 'rgba(248, 113, 113, 0.2)',
        danger30: 'rgba(248, 113, 113, 0.3)',

        // Indigo variants
        indigo10: 'rgba(99, 102, 241, 0.1)',
        indigo20: 'rgba(99, 102, 241, 0.2)',

        // White/Gray variants
        white05: 'rgba(255, 255, 255, 0.05)',
        white10: 'rgba(255, 255, 255, 0.1)',
        white15: 'rgba(56, 189, 248, 0.15)',
    },

    // ========================================
    // CHART PRESETS - Configuraciones listas
    // ========================================

    // Para gráficos de barras (usage distribution, trends)
    bars: {
        background: 'rgba(251, 191, 36, 0.7)',  // Warning con transparencia
        border: '#fbbf24',
        grid: 'rgba(255, 255, 255, 0.05)',
    },

    // Para gráficos de tipo pie/donut (tipos de empleados)
    pie: {
        colors: ['#06b6d4', '#8b5cf6', '#34d399'],  // Cyan, Purple, Green
    },

    // Para gráficos de área con gradientes
    area: {
        gradient: {
            from: '#06b6d4',         // Cyan
            to: '#8b5cf6',           // Purple
        },
        fill: {
            opacity: 0.5,
        }
    },

    // Para gráficos de departamentos
    department: {
        background: 'rgba(6, 182, 212, 0.5)',
        border: '#06b6d4',
    },

    // ========================================
    // GRADIENTS - Degradados predefinidos
    // ========================================
    gradients: {
        // Gradient principal Cyan -> Blue -> Purple
        primary: 'linear-gradient(135deg, #06b6d4, #3b82f6, #8b5cf6)',

        // Gradient Cyan -> Blue
        cyanBlue: 'linear-gradient(135deg, #06b6d4, #3b82f6)',

        // Gradient para botones
        button: 'linear-gradient(135deg, #06b6d4, #3b82f6)',

        // Gradient para bordes de stat cards
        statCard: 'linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3))',
    },

    // ========================================
    // GLOW EFFECTS - Efectos de brillo
    // ========================================
    glow: {
        cyan: '0 0 20px rgba(6, 182, 212, 0.4), 0 0 40px rgba(6, 182, 212, 0.2)',
        cyanHover: '0 0 30px rgba(6, 182, 212, 0.6), 0 0 60px rgba(6, 182, 212, 0.3)',
        success: '0 0 10px rgba(52, 211, 153, 0.3)',
        warning: '0 0 10px rgba(251, 191, 36, 0.3)',
        danger: '0 0 10px rgba(248, 113, 113, 0.3)',
    },

    // ========================================
    // APEXCHARTS CONFIG - Configuración base
    // ========================================
    apexDefaults: {
        theme: {
            mode: 'dark',
        },
        chart: {
            background: 'transparent',
            foreColor: '#94a3b8',
            toolbar: {
                show: false,
            },
        },
        grid: {
            borderColor: 'rgba(255, 255, 255, 0.05)',
            strokeDashArray: 4,
        },
        dataLabels: {
            enabled: false,
        },
        tooltip: {
            theme: 'dark',
        },
    },

    // ========================================
    // CHART.JS CONFIG - Configuración base
    // ========================================
    chartJsDefaults: {
        plugins: {
            legend: {
                labels: {
                    color: '#94a3b8',
                }
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: '#94a3b8',
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: '#94a3b8',
                }
            }
        }
    },

    // ========================================
    // HELPERS - Funciones auxiliares
    // ========================================

    /**
     * Convierte hex a rgba
     * @param {string} hex - Color hexadecimal (#RRGGBB)
     * @param {number} alpha - Transparencia (0-1)
     * @returns {string} Color en formato rgba
     */
    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    /**
     * Genera array de colores con gradiente
     * @param {string} startColor - Color inicial
     * @param {string} endColor - Color final
     * @param {number} steps - Número de pasos
     * @returns {Array} Array de colores
     */
    generateGradient(startColor, endColor, steps) {
        // Esta es una implementación simple
        // Para gradientes más complejos, usar librerías como chroma.js
        const colors = [];
        for (let i = 0; i < steps; i++) {
            const ratio = i / (steps - 1);
            colors.push(this.interpolateColor(startColor, endColor, ratio));
        }
        return colors;
    },

    /**
     * Interpola entre dos colores
     */
    interpolateColor(color1, color2, ratio) {
        // Implementación básica
        // Para producción, usar una librería más robusta
        return ratio < 0.5 ? color1 : color2;
    }
};

// Export para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartColors;
}
