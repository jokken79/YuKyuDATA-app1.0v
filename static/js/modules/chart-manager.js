/**
 * Chart Manager Module
 * Gestiona gráficos y visualizaciones (ApexCharts, Chart.js)
 * Incluye animaciones SVG y visualizaciones avanzadas
 * @module chart-manager
 */

/**
 * Clase para gestionar visualizaciones y animaciones
 */
export class Visualizations {
    /**
     * Anima un anillo de progreso SVG
     * @param {string} elementId - ID del elemento SVG circle
     * @param {string} valueId - ID del elemento para el valor numérico
     * @param {number} value - Valor actual
     * @param {number} maxValue - Valor máximo
     * @param {number} duration - Duración de la animación en ms
     */
    animateRing(elementId, valueId, value, maxValue, duration = 1000) {
        const ring = document.getElementById(elementId);
        const valueEl = document.getElementById(valueId);
        if (!ring || !valueEl) return;

        const radius = 34;
        const circumference = 2 * Math.PI * radius; // 213.6
        const percent = Math.min(value / maxValue, 1);
        const offset = circumference - (percent * circumference);

        // Animar el anillo
        ring.style.strokeDasharray = circumference;
        ring.style.strokeDashoffset = circumference;

        setTimeout(() => {
            ring.style.strokeDashoffset = offset;
        }, 100);

        // Animar el número
        this.animateNumber(valueEl, 0, value, duration);
    }

    /**
     * Anima un contador de número
     * @param {HTMLElement} element - Elemento DOM donde mostrar el número
     * @param {number} start - Número inicial
     * @param {number} end - Número final
     * @param {number} duration - Duración en ms
     */
    animateNumber(element, start, end, duration) {
        const startTime = performance.now();
        const isFloat = !Number.isInteger(end);

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = start + (end - start) * easeOut;

            if (isFloat) {
                element.textContent = current.toFixed(1);
            } else {
                element.textContent = Math.round(current).toLocaleString();
            }

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    /**
     * Actualiza el gauge de cumplimiento (semi-círculo)
     * @param {number} complianceRate - Porcentaje de cumplimiento
     * @param {number} compliant - Número de empleados que cumplen
     * @param {number} total - Total de empleados
     */
    updateGauge(complianceRate, compliant = 0, total = 0) {
        const gauge = document.getElementById('gauge-compliance');
        const valueEl = document.getElementById('gauge-value');
        const labelEl = document.querySelector('.gauge-label');
        const countEl = document.getElementById('compliance-count');
        const totalEl = document.getElementById('compliance-total');
        if (!gauge) return;

        // Longitud del arco semi-circular ~251.2 (π * 80)
        const arcLength = Math.PI * 80;
        const percent = Math.min(complianceRate / 100, 1);
        const offset = arcLength - (percent * arcLength);

        // Color según cumplimiento
        let color = 'var(--danger)';
        if (complianceRate >= 80) color = 'var(--success)';
        else if (complianceRate >= 50) color = 'var(--warning)';

        gauge.style.stroke = color;
        gauge.style.strokeDasharray = arcLength;
        gauge.style.strokeDashoffset = arcLength;

        setTimeout(() => {
            gauge.style.strokeDashoffset = offset;
        }, 200);

        if (valueEl) {
            this.animateNumber(valueEl, 0, complianceRate, 1500);
            setTimeout(() => {
                valueEl.textContent = Math.round(complianceRate) + '%';
            }, 1600);
        }

        if (countEl) countEl.textContent = compliant;
        if (totalEl) totalEl.textContent = total;

        if (labelEl) {
            if (complianceRate >= 80) {
                labelEl.textContent = '優秀 - Excelente';
                labelEl.style.color = 'var(--success)';
            } else if (complianceRate >= 50) {
                labelEl.textContent = '注愁E- Atención';
                labelEl.style.color = 'var(--warning)';
            } else {
                labelEl.textContent = '要改喁E- Mejorar';
                labelEl.style.color = 'var(--danger)';
            }
        }
    }

    /**
     * Actualiza el contador de días por vencer
     * @param {Array} data - Array de empleados
     */
    updateExpiringDays(data) {
        const countdownContainer = document.getElementById('countdown-container');
        const noExpiring = document.getElementById('no-expiring');
        const expiringDays = document.getElementById('expiring-days');
        const expiringDetail = document.getElementById('expiring-detail');
        const criticalCount = document.getElementById('critical-count');
        const warningCount = document.getElementById('warning-count');
        const healthyCount = document.getElementById('healthy-count');

        // Calcular categorías
        const critical = data.filter(e => e.balance <= 0).length;
        const warning = data.filter(e => e.balance > 0 && e.balance < 3).length;
        const healthy = data.filter(e => e.balance >= 5).length;

        // Actualizar contadores con animación
        if (criticalCount) this.animateNumber(criticalCount, 0, critical, 800);
        if (warningCount) this.animateNumber(warningCount, 0, warning, 800);
        if (healthyCount) this.animateNumber(healthyCount, 0, healthy, 800);

        // Filtrar empleados con balance bajo
        const expiring = data
            .filter(e => e.balance < 5 && e.balance > 0)
            .sort((a, b) => a.balance - b.balance);

        const totalExpiringDays = expiring.reduce((sum, e) => sum + e.balance, 0);

        if (expiring.length === 0) {
            if (countdownContainer) countdownContainer.style.display = 'none';
            if (noExpiring) noExpiring.style.display = 'block';
        } else {
            if (countdownContainer) countdownContainer.style.display = 'flex';
            if (noExpiring) noExpiring.style.display = 'none';
            if (expiringDays) expiringDays.textContent = totalExpiringDays.toFixed(1) + ' days';
            if (expiringDetail) expiringDetail.textContent = `from ${expiring.length} employees`;
        }
    }

    /**
     * Muestra confetti de celebración
     */
    showConfetti() {
        const colors = ['#00d4ff', '#ff6b6b', '#ffd93d', '#6bcb77', '#c56cf0'];
        const confettiCount = 50;

        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 0.5 + 's';
            confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
            document.body.appendChild(confetti);

            // Eliminar después de la animación
            setTimeout(() => confetti.remove(), 3500);
        }
    }

    /**
     * Actualiza estadísticas rápidas de tipos de empleados
     * @param {number} hakenCount - Número de empleados派遣
     * @param {number} ukeoiCount - Número de empleados請負
     * @param {number} staffCount - Número de empleados staff
     */
    updateQuickStats(hakenCount, ukeoiCount, staffCount) {
        const hakenEl = document.getElementById('quick-haken');
        const ukeoiEl = document.getElementById('quick-ukeoi');
        const staffEl = document.getElementById('quick-staff');

        if (hakenEl) this.animateNumber(hakenEl, 0, hakenCount, 800);
        if (ukeoiEl) this.animateNumber(ukeoiEl, 0, ukeoiCount, 800);
        if (staffEl) this.animateNumber(staffEl, 0, staffCount, 800);
    }
}

/**
 * Clase para gestionar gráficos
 */
export class ChartManager {
    /**
     * Crea una nueva instancia de ChartManager
     * @param {Object} state - Objeto de estado con charts
     * @param {string} apiBase - URL base del API
     */
    constructor(state = null, apiBase = '/api') {
        /** @type {Object} Objeto de estado para almacenar instancias de charts */
        this.state = state || { charts: {} };

        /** @type {string} URL base del API */
        this.apiBase = apiBase;
    }

    /**
     * Destruye un gráfico existente
     * @param {string} id - ID del gráfico
     */
    destroy(id) {
        if (this.state.charts[id]) {
            this.state.charts[id].destroy();
        }
    }

    /**
     * Renderiza gráfico de distribución de uso
     * @param {Array} data - Datos de empleados
     */
    renderDistribution(data) {
        const container = document.getElementById('chart-distribution');
        if (!container) return;

        this.destroy('distribution');

        const ranges = [0, 0, 0, 0]; // 0-25, 26-50, 51-75, 76-100

        data.forEach(e => {
            if (e.usageRate <= 25) ranges[0]++;
            else if (e.usageRate <= 50) ranges[1]++;
            else if (e.usageRate <= 75) ranges[2]++;
            else ranges[3]++;
        });

        const options = {
            series: ranges,
            chart: {
                type: 'donut',
                height: 320,
                background: 'transparent',
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: { enabled: true, delay: 150 },
                    dynamicAnimation: { enabled: true, speed: 350 }
                },
                dropShadow: {
                    enabled: true,
                    top: 3,
                    left: 0,
                    blur: 10,
                    opacity: 0.3,
                    color: '#000'
                }
            },
            labels: ['0-25%', '26-50%', '51-75%', '76-100%'],
            colors: ['#cbd5e1', '#93c5fd', '#2563eb', '#1e40af'],
            legend: {
                position: 'right',
                labels: { colors: '#64748b' },
                markers: { width: 12, height: 12, radius: 3 }
            },
            plotOptions: {
                pie: {
                    donut: {
                        size: '70%',
                        labels: {
                            show: true,
                            total: {
                                show: true,
                                label: 'Total',
                                color: '#94a3b8',
                                formatter: () => data.length
                            },
                            value: { color: '#e2e8f0', fontSize: '22px', fontWeight: 600 }
                        }
                    }
                }
            },
            dataLabels: {
                enabled: true,
                style: { fontSize: '14px', fontWeight: 'bold' },
                dropShadow: { enabled: true, blur: 3, opacity: 0.8 }
            },
            stroke: { width: 0 },
            tooltip: {
                theme: 'dark',
                y: { formatter: (value) => value + ' employees' }
            }
        };

        this.state.charts['distribution'] = new ApexCharts(container, options);
        this.state.charts['distribution'].render();
    }

    /**
     * Renderiza gráfico de tendencias mensuales
     * @param {number} year - Año para consultar
     */
    async renderTrends(year) {
        const container = document.getElementById('chart-trends');
        if (!container) return;
        this.destroy('trends');

        let trendsData = Array(12).fill(0);
        try {
            if (year) {
                const res = await fetch(`${this.apiBase}/yukyu/monthly-summary/${year}`);
                const json = await res.json();
                if (json.data) {
                    json.data.forEach(m => {
                        if (m.month >= 1 && m.month <= 12) {
                            trendsData[m.month - 1] = m.total_days;
                        }
                    });
                }
            }
        } catch (e) {
            console.error("Trend fetch error", e);
        }

        const options = {
            series: [{ name: 'Days Used', data: trendsData }],
            chart: {
                type: 'area',
                height: 320,
                background: 'transparent',
                toolbar: {
                    show: true,
                    tools: { download: true, zoom: true, zoomin: true, zoomout: true, pan: false }
                },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: { enabled: true, delay: 150 },
                    dynamicAnimation: { enabled: true, speed: 350 }
                },
                dropShadow: {
                    enabled: true,
                    top: 3,
                    left: 0,
                    blur: 15,
                    opacity: 0.2,
                    color: '#2563eb'
                }
            },
            colors: ['#2563eb'],
            fill: {
                type: 'gradient',
                gradient: {
                    shade: 'dark',
                    type: 'vertical',
                    shadeIntensity: 0.5,
                    gradientToColors: ['#1e40af'],
                    opacityFrom: 0.7,
                    opacityTo: 0.2,
                    stops: [0, 100]
                }
            },
            stroke: { curve: 'smooth', width: 3, colors: ['#2563eb'] },
            dataLabels: { enabled: false },
            markers: {
                size: 5,
                colors: ['#2563eb'],
                strokeColors: '#fff',
                strokeWidth: 2,
                hover: { size: 7 }
            },
            xaxis: {
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                labels: { style: { colors: '#94a3b8' } },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: {
                labels: {
                    style: { colors: '#94a3b8' },
                    formatter: (value) => Math.round(value)
                }
            },
            grid: {
                borderColor: 'rgba(255,255,255,0.05)',
                strokeDashArray: 4,
                xaxis: { lines: { show: false } }
            },
            tooltip: {
                theme: 'dark',
                y: { formatter: (value) => value.toFixed(1) + ' days' }
            }
        };

        this.state.charts['trends'] = new ApexCharts(container, options);
        this.state.charts['trends'].render();
    }

    /**
     * Renderiza gráfico por tipo de empleado
     * @param {number} year - Año para consultar
     */
    async renderTypes(year) {
        const ctx = document.getElementById('chart-types');
        if (!ctx) return;
        this.destroy('types');

        let typeData = { labels: ['Haken', 'Ukeoi', 'Staff'], data: [0, 0, 0] };
        try {
            if (year) {
                const res = await fetch(`${this.apiBase}/yukyu/by-employee-type/${year}`);
                const json = await res.json();

                if (json.data) {
                    typeData.data = [
                        json.data.hakenshain?.total_used || 0,
                        json.data.ukeoi?.total_used || 0,
                        json.data.staff?.total_used || 0
                    ];
                } else if (json.breakdown) {
                    typeData.data = [
                        json.breakdown.hakenshain?.total_used || 0,
                        json.breakdown.ukeoi?.total_used || 0,
                        json.breakdown.staff?.total_used || 0
                    ];
                }
            }
        } catch (e) {
            console.error("Type fetch error", e);
        }

        this.state.charts['types'] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Haken (Dispatch)', 'Ukeoi (Contract)', 'Staff'],
                datasets: [{
                    data: typeData.data,
                    backgroundColor: ['#2563eb', '#1d4ed8', '#1e40af'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#64748b' } }
                }
            }
        });
    }

    /**
     * Renderiza Top 10 empleados que más usaron vacaciones
     * @param {number} year - Año para consultar
     * @param {Array} fallbackData - Datos de fallback si el API falla
     */
    async renderTop10(year, fallbackData = []) {
        const ctx = document.getElementById('chart-top10');
        if (!ctx) return;
        this.destroy('top10');

        let sorted = [];
        try {
            const res = await fetch(`${this.apiBase}/analytics/top10-active/${year}`);
            const json = await res.json();
            if (json.status === 'success' && json.data) {
                sorted = json.data;
            }
        } catch (e) {
            console.warn('Top10 API failed, using local data', e);
            sorted = [...fallbackData].sort((a, b) => b.used - a.used).slice(0, 10);
        }

        this.state.charts['top10'] = new Chart(ctx, {
            type: 'bar',
            indexAxis: 'y',
            data: {
                labels: sorted.map(e => e.name),
                datasets: [{
                    label: 'Days Used (在職中のみ)',
                    data: sorted.map(e => e.used),
                    backgroundColor: 'rgba(251, 191, 36, 0.7)',
                    borderColor: '#fbbf24',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        ticks: { color: '#94a3b8', autoSkip: false },
                        grid: { display: false }
                    },
                    x: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    /**
     * Renderiza gráfico de fábricas
     * @param {Array<[string, number]>} factoryStats - Estadísticas por fábrica
     */
    renderFactoryChart(factoryStats) {
        const container = document.getElementById('chart-factories');
        if (!container) return;

        this.destroy('factories');
        const stats = factoryStats.slice(0, 10); // Top 10

        const options = {
            series: [{
                name: 'Days Used',
                data: stats.map(s => s[1])
            }],
            chart: {
                type: 'bar',
                height: 500,
                background: 'transparent',
                toolbar: { show: true },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    animateGradually: { enabled: true, delay: 150 },
                    dynamicAnimation: { enabled: true, speed: 350 }
                }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    borderRadius: 8,
                    dataLabels: { position: 'top' },
                    distributed: true
                }
            },
            colors: ['#2563eb', '#1d4ed8', '#1e40af', '#155e75', '#164e63',
                '#3b82f6', '#10b981', '#f59e0b', '#64748b', '#475569'],
            dataLabels: {
                enabled: true,
                style: { fontSize: '12px', colors: ['#fff'] },
                formatter: (value) => value.toFixed(1),
                offsetX: 30
            },
            xaxis: {
                categories: stats.map(s => s[0]),
                labels: { style: { colors: '#94a3b8' } },
                axisBorder: { show: false }
            },
            yaxis: {
                labels: { style: { colors: '#94a3b8' } }
            },
            grid: {
                borderColor: 'rgba(255,255,255,0.05)',
                xaxis: { lines: { show: true } },
                yaxis: { lines: { show: false } }
            },
            tooltip: {
                theme: 'dark',
                y: { formatter: (value) => value.toFixed(1) + ' days' }
            },
            legend: { show: false }
        };

        this.state.charts['factories'] = new ApexCharts(container, options);
        this.state.charts['factories'].render();
    }
}

/**
 * Instancias singleton para compatibilidad con código legacy
 */
export const visualizations = new Visualizations();
export const chartManager = new ChartManager();

export default { ChartManager, Visualizations, visualizations, chartManager };
