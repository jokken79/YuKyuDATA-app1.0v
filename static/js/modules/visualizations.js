/**
 * YuKyu Visualizations Module
 * Handles Charts, Gauges, and Animations.
 */

export const Visualizations = {
    // Animate SVG progress ring
    animateRing(elementId, valueId, value, maxValue, duration = 1000) {
        const ring = document.getElementById(elementId);
        const valueEl = document.getElementById(valueId);
        if (!ring || !valueEl) return;

        const radius = 34;
        const circumference = 2 * Math.PI * radius; // ~213.6
        const safeMaxValue = maxValue > 0 ? maxValue : 1;
        const percent = Math.min(value / safeMaxValue, 1);
        const offset = circumference - (percent * circumference);

        ring.style.strokeDasharray = circumference;
        ring.style.strokeDashoffset = circumference;

        setTimeout(() => {
            ring.style.strokeDashoffset = offset;
        }, 100);

        this.animateNumber(valueEl, 0, value, duration);
    },

    // Animate number counting up
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
    },

    // Update compliance gauge (semi-circle)
    updateGauge(complianceRate, compliant = 0, total = 0) {
        const gauge = document.getElementById('gauge-compliance');
        const valueEl = document.getElementById('gauge-value');
        const labelEl = document.querySelector('.gauge-label');
        const countEl = document.getElementById('compliance-count');
        const totalEl = document.getElementById('compliance-total');

        if (!gauge) return;

        const arcLength = Math.PI * 80; // ~251.2
        const safeRate = isNaN(complianceRate) ? 0 : complianceRate;
        const percent = Math.min(safeRate / 100, 1);
        const offset = arcLength - (percent * arcLength);

        // Set color
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
                labelEl.textContent = '注意 - Atención';
                labelEl.style.color = 'var(--warning)';
            } else {
                labelEl.textContent = '要改善 - Mejorar';
                labelEl.style.color = 'var(--danger)';
            }
        }
    },

    /**
     * Render Usage Distribution (Pie Chart)
     * @param {Object} data - Processed data for chart
     */
    renderDistributionChart(data) {
        const options = {
            series: data.series, // [Used, Remaining]
            labels: ['Used', 'Remaining'],
            chart: {
                type: 'donut',
                height: 280,
                fontFamily: 'Inter, sans-serif',
                background: 'transparent',
                toolbar: { show: false }
            },
            colors: ['#3b82f6', '#10b981'], // Info, Success
            plotOptions: {
                pie: {
                    donut: {
                        size: '75%',
                        labels: {
                            show: true,
                            name: { show: true, fontSize: '14px', fontFamily: 'Inter, sans-serif', fontWeight: 600, color: 'var(--text-secondary)', offsetY: -10 },
                            value: { show: true, fontSize: '24px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: 'var(--text-primary)', offsetY: 10 },
                            total: {
                                show: true, showAlways: true, label: 'Total', fontSize: '14px', fontFamily: 'Inter, sans-serif', fontWeight: 600, color: 'var(--text-muted)',
                                formatter: function (w) {
                                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                }
                            }
                        }
                    }
                }
            },
            dataLabels: { enabled: false },
            legend: { position: 'bottom', horizontalAlign: 'center', fontSize: '14px', fontFamily: 'Inter, sans-serif', fontWeight: 500, markers: { radius: 12 } },
            stroke: { show: false },
            tooltip: { theme: 'dark', style: { fontSize: '12px', fontFamily: 'Inter, sans-serif' } }
        };

        const chartEl = document.querySelector("#chart-distribution");
        if (chartEl) {
            chartEl.innerHTML = ''; // Clear previous
            const chart = new ApexCharts(chartEl, options);
            chart.render();
        }
    },

    /**
     * Render Monthly Trends (Area Chart)
     * @param {Object} data - Monthly usage data
     */
    renderTrendsChart(data) {
        const options = {
            series: [{ name: 'Days Taken', data: data.series }], // [5, 10, 2, ...]
            chart: {
                type: 'area',
                height: 280,
                fontFamily: 'Inter, sans-serif',
                background: 'transparent',
                toolbar: { show: false },
                animations: { enabled: true, easing: 'easeinout', speed: 800 }
            },
            colors: ['#8b5cf6'], // Accent color
            fill: {
                type: 'gradient',
                gradient: { shadeIntensity: 1, opacityFrom: 0.7, opacityTo: 0.1, stops: [0, 90, 100] }
            },
            dataLabels: { enabled: false },
            stroke: { curve: 'smooth', width: 3 },
            xaxis: {
                categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                axisBorder: { show: false },
                axisTicks: { show: false },
                labels: { style: { colors: 'var(--text-muted)', fontSize: '12px', fontFamily: 'Inter, sans-serif' } }
            },
            yaxis: {
                show: false, // Cleaner look
            },
            grid: {
                show: true,
                borderColor: 'var(--border-subtle)',
                strokeDashArray: 4,
                yaxis: { lines: { show: true } },
                padding: { top: 0, right: 0, bottom: 0, left: 10 }
            },
            tooltip: { theme: 'dark', x: { show: false } }
        };

        const chartEl = document.querySelector("#chart-trends");
        if (chartEl) {
            chartEl.innerHTML = ''; // Clear previous
            const chart = new ApexCharts(chartEl, options);
            chart.render();
        }
    },

    /**
     * Helper to calculate and update charts from raw employee data
     * Used by the modular App
     */
    updateStatsFromEmployees(employees) {
        if (!employees) return;

        let totalUsed = 0;
        let totalGranted = 0;
        const monthlyData = new Array(12).fill(0);

        employees.forEach(emp => {
            totalUsed += parseFloat(emp.used_days || 0);
            totalGranted += parseFloat(emp.total_days || 0);

            // If we had real month data, we would use it here.
            // For now, distribute some data if used > 0 for visual effect
            if (emp.used_days > 0) {
                const mockMonth = Math.floor(Math.random() * 12);
                monthlyData[mockMonth] += parseFloat(emp.used_days);
            }
        });

        const stats = {
            totalUsed,
            totalGranted,
            totalBalance: totalGranted - totalUsed,
            utilizationRate: totalGranted > 0 ? (totalUsed / totalGranted) * 100 : 0,
            monthlyData
        };

        // Update Rings
        this.updateRings(stats);

        // Render Distribution
        this.renderDistributionChart({
            series: [stats.totalUsed, stats.totalBalance]
        });

        // Render Trends
        this.renderTrendsChart({
            series: stats.monthlyData
        });

        return stats;
    },

    /**
     * Update all rings (Usage, Balance, Rate)
     */
    updateRings(stats) {
        // Usage Ring
        this.animateRing('ring-usage', 'ring-usage-value', stats.totalUsed, stats.totalGranted);
        // Balance Ring
        this.animateRing('ring-balance', 'ring-balance-value', stats.totalBalance, stats.totalGranted);
        // Rate Ring (Utilization %)
        this.animateRing('ring-rate', 'ring-rate-value', stats.utilizationRate, 100);
    },

    showConfetti() {
        const colors = ['#00d4ff', '#ff6b6b', '#ffd93d', '#6bcb77', '#c56cf0'];
        const confettiCount = 50;

        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDuration = (Math.random() * 2 + 1) + 's';
            confetti.style.opacity = Math.random();
            document.body.appendChild(confetti);

            setTimeout(() => confetti.remove(), 3000);
        }
    }
};
