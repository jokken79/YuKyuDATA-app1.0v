/**
 * UI Manager Module
 * Gestiona toda la interfaz de usuario: KPIs, tablas, modales, toasts, etc.
 * @module ui-manager
 */

import { escapeHtml, escapeAttr, safeNumber } from './utils.js';

/**
 * Clase para gestionar la interfaz de usuario
 */
export class UIManager {
    /**
     * Crea una nueva instancia de UIManager
     * @param {Object} state - Objeto de estado de la aplicación
     * @param {Object} config - Configuración de la aplicación
     * @param {Object} visualizations - Instancia de Visualizations
     * @param {Object} chartManager - Instancia de ChartManager
     */
    constructor(state, config, visualizations, chartManager) {
        /** @type {Object} Estado de la aplicación */
        this.state = state;

        /** @type {Object} Configuración */
        this.config = config;

        /** @type {Object} Gestor de visualizaciones */
        this.visualizations = visualizations;

        /** @type {Object} Gestor de gráficos */
        this.chartManager = chartManager;
    }

    /**
     * Actualiza todos los componentes de UI
     * @param {Function} getFiltered - Función para obtener datos filtrados
     * @param {Function} getFactoryStats - Función para obtener stats de fábricas
     */
    async updateAll(getFiltered, getFactoryStats) {
        await this.renderKPIs();
        this.renderTable('', this.state.typeFilter, getFiltered);
        await this.renderCharts(getFiltered, getFactoryStats);
        this.updateYearFilter();
        this.updateTypeCounts(getFiltered);

        const empCountBadge = document.getElementById('emp-count-badge');
        if (empCountBadge && getFiltered) {
            empCountBadge.innerText = `${getFiltered().length} Employees`;
        }
    }

    /**
     * Cambia la vista activa
     * @param {string} viewName - Nombre de la vista
     * @param {Object} modules - Módulos adicionales (requests, calendar, etc.)
     */
    switchView(viewName, modules = {}) {
        // Ocultar todas las vistas
        document.querySelectorAll('.view-section').forEach(el => {
            el.style.display = 'none';
            el.classList.remove('active');
        });

        // Mostrar vista objetivo
        const target = document.getElementById(`view-${viewName}`);
        if (target) {
            target.style.display = 'block';
            setTimeout(() => {
                target.classList.add('active');
                // Animar transición con GSAP si está disponible
                if (modules.animations && modules.animations.transitionView) {
                    modules.animations.transitionView(target);
                }
            }, 10);
        }

        // Actualizar sidebar
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
        if (activeNav) activeNav.classList.add('active');

        // Actualizar header
        const titleMap = {
            'dashboard': 'ダッシュボード',
            'employees': '従業員一覧',
            'factories': '工場別分析',
            'requests': '有給休暇申請',
            'calendar': '休暇カレンダー',
            'compliance': 'コンプライアンス',
            'analytics': '詳細分析',
            'reports': '月次レポート (21日〜20日)',
            'settings': 'システム設定'
        };

        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.innerText = titleMap[viewName] || 'Dashboard';
        }

        this.state.currentView = viewName;

        // Re-renderizar charts si cambiamos a vista de fábricas
        if (viewName === 'factories' && modules.chartManager) {
            setTimeout(() => {
                if (modules.getFactoryStats) {
                    const stats = modules.getFactoryStats();
                    modules.chartManager.renderFactoryChart(stats);
                }
            }, 100);
        }

        // Cargar datos para vistas específicas
        if (viewName === 'requests' && modules.requests) {
            modules.requests.loadFactories();
            modules.requests.loadPending();
            modules.requests.loadHistory();
        }

        if (viewName === 'calendar' && modules.calendar) {
            modules.calendar.loadEvents();
        }

        if (viewName === 'compliance' && modules.compliance) {
            modules.compliance.loadAlerts();
        }

        if (viewName === 'analytics' && modules.analytics) {
            modules.analytics.loadDashboard();
        }

        if (viewName === 'reports' && modules.reports) {
            modules.reports.init();
        }

        if (viewName === 'settings' && modules.settings) {
            modules.settings.loadSnapshot();
        }

        if (viewName === 'employees' && modules.employeeTypes) {
            modules.employeeTypes.loadData();
        }
    }

    /**
     * Renderiza los KPIs principales
     */
    async renderKPIs() {
        const data = this.state.data.filter(e => !this.state.year || e.year === this.state.year);
        const total = data.length;
        const granted = data.reduce((s, e) => s + e.granted, 0);

        let used = 0;
        let balance = 0;
        let rate = 0;

        try {
            if (this.state.year) {
                const res = await fetch(`${this.config.apiBase}/yukyu/kpi-stats/${this.state.year}`);
                const kpi = await res.json();
                if (kpi.status === 'success') {
                    used = kpi.total_used;
                    balance = kpi.total_balance;
                    rate = kpi.usage_rate;
                }
            }
        } catch (e) {
            // Fallback al cálculo antiguo si el endpoint falla
            used = data.reduce((s, e) => s + e.used, 0);
            balance = granted - used;
            rate = granted > 0 ? Math.round((used / granted) * 100) : 0;
        }

        // Actualizar displays de KPI tradicionales
        const kpiUsed = document.getElementById('kpi-used');
        const kpiBalance = document.getElementById('kpi-balance');
        const kpiRate = document.getElementById('kpi-rate');
        const kpiTotal = document.getElementById('kpi-total');

        if (kpiUsed) kpiUsed.innerText = Math.round(used).toLocaleString();
        if (kpiBalance) kpiBalance.innerText = Math.round(balance).toLocaleString();
        if (kpiRate) kpiRate.innerText = rate + '%';
        if (kpiTotal) kpiTotal.innerText = total;

        // Calcular valores máximos para los anillos
        const maxUsage = granted > 0 ? granted : 10000;
        const maxBalance = granted > 0 ? granted : 10000;

        // Animar anillos de progreso
        if (this.visualizations) {
            this.visualizations.animateRing('ring-usage', 'ring-usage-value', used, maxUsage, 1200);
            this.visualizations.animateRing('ring-balance', 'ring-balance-value', balance, maxBalance, 1200);
            this.visualizations.animateRing('ring-rate', 'ring-rate-value', rate, 100, 1200);

            // Calcular cumplimiento (% de empleados con >= 5 días usados - ley japonesa)
            const compliant = data.filter(e => e.used >= 5).length;
            const complianceRate = total > 0 ? Math.round((compliant / total) * 100) : 0;
            this.visualizations.updateGauge(complianceRate, compliant, total);

            // Actualizar countdown de días por vencer
            this.visualizations.updateExpiringDays(data);
        }
    }

    /**
     * Renderiza la tabla de empleados
     * @param {string} filterText - Texto para filtrar
     * @param {string} typeFilter - Tipo de empleado (all, genzai, ukeoi, staff)
     * @param {Function} getFiltered - Función para obtener datos filtrados
     */
    renderTable(filterText = '', typeFilter = 'all', getFiltered = null) {
        const tbody = document.getElementById('table-body');
        if (!tbody) return;

        let data = getFiltered ? getFiltered() : this.state.data;

        // Filtrar por texto de búsqueda
        if (filterText) {
            const q = filterText.toLowerCase();
            data = data.filter(e =>
                e.name.toLowerCase().includes(q) ||
                String(e.employeeNum).includes(q) ||
                (e.haken && e.haken.toLowerCase().includes(q))
            );
        }

        // Filtrar por tipo de empleado
        if (typeFilter && typeFilter !== 'all') {
            data = data.filter(e => e.employeeType === typeFilter);
        }

        if (data.length === 0) {
            tbody.textContent = '';
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 7;
            td.style.textAlign = 'center';
            td.style.padding = '2rem';
            td.textContent = 'No matching records found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        // Usar data attributes en lugar de onclick inline (prevención de XSS)
        tbody.innerHTML = data.map(e => {
            const empNum = escapeAttr(e.employeeNum);
            const name = escapeHtml(e.name);
            const haken = escapeHtml(e.haken || '-');
            const granted = safeNumber(e.granted).toFixed(1);
            const used = safeNumber(e.used).toFixed(1);
            const balance = safeNumber(e.balance);
            const usageRate = safeNumber(e.usageRate);
            const balanceClass = balance < 0 ? 'badge-critical' : balance < 5 ? 'badge-danger' : 'badge-success';

            // Badge de tipo de empleado
            const typeLabels = { genzai: '派遣', ukeoi: '請負', staff: '社員' };
            const typeClasses = { genzai: 'type-genzai', ukeoi: 'type-ukeoi', staff: 'type-staff' };
            const empType = e.employeeType || 'staff';
            const typeLabel = typeLabels[empType] || '社員';
            const typeClass = typeClasses[empType] || 'type-staff';

            // Determinar color basado en tasa de uso
            const rateColor = usageRate >= 80 ? 'var(--success)' : usageRate >= 50 ? 'var(--warning)' : 'var(--danger)';
            const rateGlow = usageRate >= 80 ? '0 0 8px var(--success)' : usageRate >= 50 ? '0 0 8px var(--warning)' : '0 0 8px var(--danger)';

            return `
            <tr class="employee-row" data-employee-num="${empNum}" style="cursor: pointer;">
                <td><div class="font-bold">${empNum}</div></td>
                <td>
                    <div class="employee-name-cell">
                        <span class="font-bold text-white">${name}</span>
                        <span class="badge-type ${typeClass}">${typeLabel}</span>
                    </div>
                </td>
                <td><div class="text-sm text-gray-400">${haken}</div></td>
                <td>${granted}</td>
                <td><span class="text-gradient">${used}</span></td>
                <td><span class="badge ${balanceClass}">${balance.toFixed(1)}</span></td>
                <td>
                    <div class="mini-progress" style="width: 100px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; position: relative;">
                        <div class="mini-progress-fill" style="width: ${Math.min(usageRate, 100)}%; height: 100%; background: linear-gradient(90deg, ${rateColor}, ${rateColor}88); border-radius: 4px; box-shadow: ${rateGlow}; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                    </div>
                    <div class="text-xs mt-1 text-right" style="color: ${rateColor}; font-weight: 500;">${usageRate}%</div>
                </td>
            </tr>
        `}).join('');
    }

    /**
     * Maneja búsqueda de empleados
     * @param {string} val - Valor de búsqueda
     * @param {Object} employeeTypes - Módulo employeeTypes si existe
     */
    handleSearch(val, employeeTypes = null) {
        if (employeeTypes && employeeTypes.data && employeeTypes.data.all.length > 0) {
            employeeTypes.renderTable(val);
        } else {
            this.renderTable(val, this.state.typeFilter);
        }
    }

    /**
     * Filtra por tipo de empleado
     * @param {string} type - Tipo (all, genzai, ukeoi, staff)
     * @param {Function} getFiltered - Función para obtener datos filtrados
     */
    filterByType(type, getFiltered = null) {
        this.state.typeFilter = type;

        // Actualizar tab activo
        document.querySelectorAll('.type-tab').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });

        // Re-renderizar tabla con búsqueda actual y filtro de tipo
        const searchInput = document.getElementById('search-input');
        const searchVal = searchInput ? searchInput.value : '';
        this.renderTable(searchVal, type, getFiltered);
    }

    /**
     * Actualiza contadores de tipos de empleados
     * @param {Function} getFiltered - Función para obtener datos filtrados
     */
    updateTypeCounts(getFiltered) {
        const data = getFiltered ? getFiltered() : this.state.data;
        const counts = {
            all: data.length,
            genzai: data.filter(e => e.employeeType === 'genzai').length,
            ukeoi: data.filter(e => e.employeeType === 'ukeoi').length,
            staff: data.filter(e => e.employeeType === 'staff').length
        };

        // Actualizar badges de conteo
        const countAll = document.getElementById('count-all');
        const countGenzai = document.getElementById('count-genzai');
        const countUkeoi = document.getElementById('count-ukeoi');
        const countStaff = document.getElementById('count-staff');

        if (countAll) countAll.textContent = counts.all;
        if (countGenzai) countGenzai.textContent = counts.genzai;
        if (countUkeoi) countUkeoi.textContent = counts.ukeoi;
        if (countStaff) countStaff.textContent = counts.staff;
    }

    /**
     * Actualiza el filtro de años
     */
    updateYearFilter() {
        const container = document.getElementById('year-filter');
        if (!container || this.state.availableYears.length === 0) return;

        container.innerHTML = this.state.availableYears.map(y => `
            <button class="btn btn-glass ${this.state.year === y ? 'btn-primary' : ''}"
                    data-year="${y}">
                ${y}
            </button>
        `).join('');
    }

    /**
     * Renderiza todos los gráficos
     * @param {Function} getFiltered - Función para obtener datos filtrados
     * @param {Function} getFactoryStats - Función para obtener stats de fábricas
     */
    async renderCharts(getFiltered, getFactoryStats) {
        if (!this.chartManager) return;

        const data = getFiltered ? getFiltered() : this.state.data;

        this.chartManager.renderDistribution(data);
        await this.chartManager.renderTrends(this.state.year);

        if (getFactoryStats) {
            const stats = getFactoryStats();
            this.chartManager.renderFactoryChart(stats);
        }

        await this.chartManager.renderTypes(this.state.year);
        await this.chartManager.renderTop10(this.state.year, data);
    }

    /**
     * Muestra el loader
     */
    showLoading() {
        const loader = document.getElementById('loader');
        if (loader) loader.classList.add('active');
    }

    /**
     * Oculta el loader
     */
    hideLoading() {
        const loader = document.getElementById('loader');
        if (loader) loader.classList.remove('active');
    }

    /**
     * Establece el estado de loading de un botón
     * @param {HTMLElement} btn - Elemento botón
     * @param {boolean} isLoading - Estado de loading
     */
    setBtnLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            btn.classList.add('is-loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('is-loading');
            btn.disabled = false;
        }
    }

    /**
     * Alterna el menú móvil
     */
    toggleMobileMenu() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (sidebar && toggle) {
            const isOpen = sidebar.classList.contains('is-open');
            if (isOpen) {
                this.closeMobileMenu();
            } else {
                sidebar.classList.add('is-open');
                toggle.classList.add('is-active');
                toggle.setAttribute('aria-expanded', 'true');
                if (overlay) {
                    overlay.classList.add('is-active');
                    overlay.setAttribute('aria-hidden', 'false');
                }
                document.body.style.overflow = 'hidden';
            }
        }
    }

    /**
     * Cierra el menú móvil
     */
    closeMobileMenu() {
        const toggle = document.getElementById('mobile-menu-toggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (sidebar) sidebar.classList.remove('is-open');
        if (toggle) {
            toggle.classList.remove('is-active');
            toggle.setAttribute('aria-expanded', 'false');
        }
        if (overlay) {
            overlay.classList.remove('is-active');
            overlay.setAttribute('aria-hidden', 'true');
        }
        document.body.style.overflow = '';
    }

    /**
     * Muestra una notificación toast
     * @param {string} type - Tipo (success, error, warning, info)
     * @param {string} msg - Mensaje
     * @param {number} duration - Duración en ms
     */
    showToast(type, msg, duration = 4000) {
        // Usar sistema de toast moderno si está disponible
        if (typeof ModernUI !== 'undefined' && ModernUI.Toast) {
            const hasEmoji = /^[\u{1F300}-\u{1F9FF}]/u.test(msg);
            let title = '';
            let message = msg;

            if (hasEmoji) {
                const parts = msg.split(' ');
                if (parts.length > 1) {
                    title = parts[0];
                    message = parts.slice(1).join(' ');
                }
            } else {
                const titles = {
                    success: 'Success',
                    error: 'Error',
                    warning: 'Warning',
                    info: 'Info'
                };
                title = titles[type] || 'Notification';
            }

            ModernUI.Toast.show({ type, title, message, duration });
            return;
        }

        // Fallback al sistema de toast original
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const styles = {
            success: { border: 'var(--success)', bg: 'rgba(34, 197, 94, 0.1)' },
            error: { border: 'var(--danger)', bg: 'rgba(239, 68, 68, 0.1)' },
            warning: { border: 'var(--warning)', bg: 'rgba(251, 191, 36, 0.1)' },
            info: { border: 'var(--primary)', bg: 'rgba(56, 189, 248, 0.1)' }
        };
        const style = styles[type] || styles.info;

        toast.style.cssText = `
            border-left: 4px solid ${style.border};
            background: ${style.bg};
            backdrop-filter: blur(10px);
        `;
        toast.innerHTML = msg;

        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.className = 'toast-close';
        closeBtn.onclick = () => toast.remove();
        toast.appendChild(closeBtn);

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    /**
     * Abre el modal de detalles de empleado
     * @param {string|number} id - ID del empleado
     */
    async openModal(id) {
        const emp = this.state.data.find(e => e.employeeNum == id);
        if (!emp) return;

        // Mostrar modal con loading
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');
        const detailModal = document.getElementById('detail-modal');

        if (modalTitle) modalTitle.innerText = emp.name;
        if (modalContent) {
            modalContent.innerHTML = `
                <div style="text-align: center; padding: 2rem;">
                    <div class="spinner" style="margin: 0 auto;"></div>
                    <p style="margin-top: 1rem; color: #94a3b8;">Cargando datos...</p>
                </div>
            `;
        }
        if (detailModal) detailModal.classList.add('active');

        // Obtener datos completos del empleado
        try {
            const res = await fetch(`${this.config.apiBase}/employees/${id}/leave-info`);
            const json = await res.json();

            if (json.status !== 'success') {
                throw new Error('No se pudieron cargar los datos');
            }

            const employee = json.employee || {};
            const yukyuHistory = json.yukyu_history || [];
            const usageHistory = json.usage_history || [];
            const totalAvailable = json.total_available || 0;

            // Calcular fecha de renovación
            let renewalDate = 'No disponible';
            if (yukyuHistory.length > 0) {
                const latestYear = Math.max(...yukyuHistory.map(h => h.year));
                renewalDate = `${latestYear + 1}年11月頃`;
            }

            // Generar HTML del historial de 2 años
            let historyHtml = '';
            yukyuHistory.sort((a, b) => b.year - a.year).forEach(h => {
                historyHtml += `
                    <div class="glass-panel" style="padding: 1rem; margin-bottom: 0.5rem; background: rgba(56, 189, 248, 0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <strong style="color: #38bdf8;">📅 ${h.year}年度</strong>
                            <span class="badge" style="background: ${h.usage_rate > 75 ? '#22c55e' : h.usage_rate > 50 ? '#eab308' : '#ef4444'};">
                                ${h.usage_rate?.toFixed(1) || 0}%
                            </span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem; font-size: 0.9rem;">
                            <div><span style="color: #94a3b8;">付与:</span> ${h.granted || 0}日</div>
                            <div><span style="color: #94a3b8;">使用:</span> ${h.used || 0}日</div>
                            <div><span style="color: #38bdf8; font-weight: bold;">残:</span> ${h.balance || 0}日</div>
                        </div>
                    </div>
                `;
            });

            // Generar HTML de fechas de uso recientes
            let usageDatesHtml = '';
            if (usageHistory.length > 0) {
                const recentUsage = usageHistory.slice(0, 10);
                usageDatesHtml = `
                    <div style="margin-top: 1rem;">
                        <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📋 使用履歴 (最近10件)</h4>
                        <div style="max-height: 150px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 0.5rem;">
                            ${recentUsage.map(u => `
                                <div style="display: flex; justify-content: space-between; padding: 0.3rem 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                                    <span>${u.date}</span>
                                    <span style="color: #38bdf8;">${u.days}日</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            if (modalContent) {
                modalContent.innerHTML = `
                    <!-- Información básica -->
                    <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 1.5rem; gap: 0.8rem;">
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">社員番号</div>
                            <div style="font-size: 1.2rem; font-weight: bold;">${emp.employeeNum}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">派遣先</div>
                            <div style="font-size: 0.9rem; font-weight: bold;">${emp.haken || employee.factory || '-'}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">タイプ</div>
                            <div style="font-size: 1rem;">${employee.type || (emp.type === 'haken' ? '派遣' : emp.type === 'ukeoi' ? '請負' : 'スタッフ')}</div>
                        </div>
                        <div class="glass-panel" style="padding: 0.8rem; text-align: center;">
                            <div style="color: #94a3b8; font-size: 0.8rem;">ステータス</div>
                            <div style="font-size: 1rem; color: ${employee.status === '在職中' ? '#22c55e' : '#ef4444'};">${employee.status || '在職中'}</div>
                        </div>
                    </div>

                    <!-- Balance total actual -->
                    <div class="glass-panel" style="padding: 1rem; margin-bottom: 1rem; background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(56, 189, 248, 0.2)); text-align: center;">
                        <div style="color: #94a3b8; font-size: 0.9rem;">💰 有給残日数 (合計)</div>
                        <div style="font-size: 2rem; font-weight: bold; color: #22c55e;">${totalAvailable}日</div>
                        <div style="color: #94a3b8; font-size: 0.8rem;">次回付与: ${renewalDate}</div>
                    </div>

                    <!-- Historial de 2 años -->
                    <h4 style="color: #94a3b8; margin-bottom: 0.5rem;">📊 年度別履歴 (過去2年)</h4>
                    ${historyHtml || '<p style="color: #64748b;">履歴データがありません</p>'}

                    <!-- Fechas de uso recientes -->
                    ${usageDatesHtml}
                `;
            }

        } catch (error) {
            console.error('Error loading employee details:', error);
            // Fallback a datos básicos si el API falla
            if (modalContent) {
                modalContent.innerHTML = `
                    <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 2rem;">
                        <div><span class="text-gray-400">ID:</span> ${emp.employeeNum}</div>
                        <div><span class="text-gray-400">Factory:</span> ${emp.haken}</div>
                        <div><span class="text-gray-400">Granted:</span> ${emp.granted}</div>
                        <div><span class="text-gray-400">Used:</span> ${emp.used}</div>
                        <div><span class="text-gray-400">Balance:</span> ${emp.balance}</div>
                        <div><span class="text-gray-400">Rate:</span> ${emp.usageRate}%</div>
                    </div>
                    <p style="color: #f59e0b; font-size: 0.9rem;">⚠️ 詳細データの取得に失敗しました</p>
                `;
            }
        }
    }

    /**
     * Cierra el modal de detalles
     */
    closeModal() {
        const detailModal = document.getElementById('detail-modal');
        if (detailModal) {
            detailModal.classList.remove('active');
        }
    }
}

export default UIManager;
