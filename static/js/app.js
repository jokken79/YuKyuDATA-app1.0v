/**
 * YuKyu Dashboard v5.3 - Security Enhanced
 */

const App = {
    state: {
        data: [],
        year: null,
        availableYears: [],
        charts: {},
        currentView: 'dashboard'
    },

    config: {
        apiBase: 'http://localhost:8000/api'
    },

    // ========================================
    // SECURITY UTILITIES (XSS Prevention)
    // ========================================
    utils: {
        /**
         * Escapes HTML to prevent XSS attacks
         */
        escapeHtml(str) {
            if (str === null || str === undefined) return '';
            const div = document.createElement('div');
            div.textContent = String(str);
            return div.innerHTML;
        },

        /**
         * Escapes attribute values
         */
        escapeAttr(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/'/g, '&#39;')
                .replace(/"/g, '&quot;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
        },

        /**
         * Safely creates a number from input
         */
        safeNumber(val, defaultVal = 0) {
            const num = parseFloat(val);
            return Number.isFinite(num) ? num : defaultVal;
        },

        /**
         * Validates year is within acceptable range
         */
        isValidYear(year) {
            const num = parseInt(year);
            return Number.isInteger(num) && num >= 2000 && num <= 2100;
        }
    },

    async init() {
        console.log('🚀 Initializing YuKyu Premium Dashboard...');
        this.ui.showLoading();

        // Initialize theme
        this.theme.init();

        // Initial Fetch
        await this.data.fetchEmployees();

        this.ui.hideLoading();
        this.events.setupListeners();
    },

    // ========================================
    // THEME MODULE
    // ========================================
    theme: {
        current: 'dark',

        init() {
            // Load saved theme or default to dark
            const saved = localStorage.getItem('yukyu-theme');
            this.current = saved || 'dark';
            this.apply();
        },

        toggle() {
            this.current = this.current === 'dark' ? 'light' : 'dark';
            this.apply();
            localStorage.setItem('yukyu-theme', this.current);
            App.ui.showToast('info', this.current === 'dark' ? '🌙 ダークモード' : '☀️ ライトモード');
        },

        apply() {
            document.documentElement.setAttribute('data-theme', this.current);
            const icon = document.getElementById('theme-icon');
            const label = document.getElementById('theme-label');
            if (icon) icon.textContent = this.current === 'dark' ? '🌙' : '☀️';
            if (label) label.textContent = this.current === 'dark' ? 'Dark' : 'Light';
        }
    },

    data: {
        async fetchEmployees(year = null) {
            try {
                let url = `${App.config.apiBase}/employees`;
                if (year) url += `?year=${year}`;

                const res = await fetch(url);
                const json = await res.json();

                App.state.data = json.data.map(emp => ({
                    ...emp,
                    employeeNum: emp.employee_num,
                    usageRate: emp.granted > 0 ? Math.round((emp.used / emp.granted) * 100) : 0
                }));
                App.state.availableYears = json.available_years;

                // Smart Year Selection
                if (App.state.availableYears.length > 0 && !App.state.year) {
                    const currentYear = new Date().getFullYear();
                    // Prefer current year if available, otherwise first available
                    if (App.state.availableYears.includes(currentYear)) {
                        App.state.year = currentYear;
                    } else if (App.state.availableYears.includes(currentYear - 1)) {
                        // Or previous year if current not available
                        App.state.year = currentYear - 1;
                    } else {
                        // Fallback to first available
                        App.state.year = App.state.availableYears[0];
                    }

                    // If year wasn't passed, we need to refetch with the selected year to filter correctly
                    if (!year) {
                        return this.fetchEmployees(App.state.year);
                    }
                }

                App.ui.updateAll();
                App.ui.showToast('success', 'Data refresh complete');

            } catch (err) {
                console.error(err);
                App.ui.showToast('error', 'Failed to load data');
            }
        },

        async sync() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/sync`, { method: 'POST' });
                if (!res.ok) throw new Error(await res.text());
                const json = await res.json();
                App.ui.showToast('success', `Synced ${json.count} records`);
                await this.fetchEmployees(App.state.year);
            } catch (err) {
                App.ui.showToast('error', err.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async syncGenzai() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/sync-genzai`, { method: 'POST' });
                if (!res.ok) throw res;
                App.ui.showToast('success', 'Genzai (Dispatch) Synced');
            } catch (e) { App.ui.showToast('error', 'Sync Failed'); }
            finally { App.ui.hideLoading(); }
        },

        async syncUkeoi() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/sync-ukeoi`, { method: 'POST' });
                if (!res.ok) throw res;
                App.ui.showToast('success', 'Ukeoi (contract) Synced');
            } catch (e) { App.ui.showToast('error', 'Sync Failed'); }
            finally { App.ui.hideLoading(); }
        },

        getFiltered() {
            if (!App.state.year) return App.state.data;
            return App.state.data.filter(e => e.year === App.state.year);
        },

        getFactoryStats() {
            const stats = {};
            const data = this.getFiltered();
            data.forEach(e => {
                const f = e.haken || 'Unknown';
                if (!stats[f]) stats[f] = 0;
                stats[f] += e.used;
            });
            return Object.entries(stats).sort((a, b) => b[1] - a[1]);
        }
    },

    ui: {
        updateAll() {
            this.renderKPIs();
            this.renderTable();
            this.renderCharts();
            this.updateYearFilter();
            document.getElementById('emp-count-badge').innerText = `${App.data.getFiltered().length} Employees`;
        },

        switchView(viewName) {
            // Hide all views
            document.querySelectorAll('.view-section').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));

            // Show target view
            const target = document.getElementById(`view-${viewName}`);
            if (target) {
                target.style.display = 'block';
                setTimeout(() => {
                    target.classList.add('active');
                    // Animate view transition with GSAP
                    if (App.animations && App.animations.transitionView) {
                        App.animations.transitionView(target);
                    }
                }, 10);
            }

            // Update Sidebar
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
            if (activeNav) activeNav.classList.add('active');

            // Update Header
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
            document.getElementById('page-title').innerText = titleMap[viewName] || 'Dashboard';

            App.state.currentView = viewName;

            // Re-render charts if switching to factory view to ensure size correctness
            if (viewName === 'factories') {
                setTimeout(() => App.charts.renderFactoryChart(), 100);
            }

            // Load data for specific views
            if (viewName === 'requests') {
                App.requests.loadFactories();
                App.requests.loadPending();
                App.requests.loadHistory();
            }

            if (viewName === 'calendar') {
                App.calendar.loadEvents();
            }

            if (viewName === 'compliance') {
                App.compliance.loadAlerts();
            }

            if (viewName === 'analytics') {
                App.analytics.loadDashboard();
            }

            if (viewName === 'reports') {
                App.reports.init();
            }

            if (viewName === 'settings') {
                App.settings.loadSnapshot();
            }
        },

        renderKPIs() {
            const data = App.data.getFiltered();
            const total = data.length;
            const granted = data.reduce((s, e) => s + e.granted, 0);
            const used = data.reduce((s, e) => s + e.used, 0);
            const balance = granted - used;
            const rate = granted > 0 ? Math.round((used / granted) * 100) : 0;

            document.getElementById('kpi-used').innerText = used.toLocaleString();
            document.getElementById('kpi-balance').innerText = balance.toLocaleString();
            document.getElementById('kpi-rate').innerText = rate + '%';
            document.getElementById('kpi-total').innerText = total;
        },

        renderTable(filterText = '') {
            const tbody = document.getElementById('table-body');
            let data = App.data.getFiltered();

            if (filterText) {
                const q = filterText.toLowerCase();
                data = data.filter(e =>
                    e.name.toLowerCase().includes(q) ||
                    String(e.employeeNum).includes(q) ||
                    (e.haken && e.haken.toLowerCase().includes(q))
                );
            }

            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem;">No matching records found</td></tr>';
                return;
            }

            // Using data attributes instead of inline onclick (XSS prevention)
            tbody.innerHTML = data.map(e => {
                const empNum = App.utils.escapeAttr(e.employeeNum);
                const name = App.utils.escapeHtml(e.name);
                const haken = App.utils.escapeHtml(e.haken || '-');
                const granted = App.utils.safeNumber(e.granted).toFixed(1);
                const used = App.utils.safeNumber(e.used).toFixed(1);
                const balance = App.utils.safeNumber(e.balance);
                const usageRate = App.utils.safeNumber(e.usageRate);
                const balanceClass = balance < 0 ? 'badge-critical' : balance < 5 ? 'badge-danger' : 'badge-success';

                return `
                <tr class="employee-row" data-employee-num="${empNum}" style="cursor: pointer;">
                    <td><div class="font-bold">${empNum}</div></td>
                    <td><div class="font-bold text-white">${name}</div></td>
                    <td><div class="text-sm text-gray-400">${haken}</div></td>
                    <td>${granted}</td>
                    <td><span class="text-gradient">${used}</span></td>
                    <td><span class="badge ${balanceClass}">${balance.toFixed(1)}</span></td>
                    <td>
                        <div style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                            <div style="width: ${Math.min(usageRate, 100)}%; height: 100%; background: var(--primary);"></div>
                        </div>
                        <div class="text-xs mt-1 text-right">${usageRate}%</div>
                    </td>
                </tr>
            `}).join('');
        },

        handleSearch(val) {
            this.renderTable(val);
        },

        updateYearFilter() {
            const container = document.getElementById('year-filter');
            if (App.state.availableYears.length === 0) return;

            container.innerHTML = App.state.availableYears.map(y => `
                <button class="btn btn-glass ${App.state.year === y ? 'btn-primary' : ''}" 
                        onclick="App.data.fetchEmployees(${y}); App.state.year=${y};">
                    ${y}
                </button>
            `).join('');
        },

        renderCharts() {
            App.charts.renderDistribution();
            App.charts.renderTrends();
            App.charts.renderFactoryChart();
        },

        showLoading() { document.getElementById('loader').classList.add('active'); },
        hideLoading() { document.getElementById('loader').classList.remove('active'); },

        showToast(type, msg) {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.style.borderLeft = type === 'success' ? '4px solid var(--success)' : type === 'error' ? '4px solid var(--danger)' : '4px solid var(--primary)';
            toast.innerHTML = type === 'success' ? `✅ ${msg}` : type === 'error' ? `❌ ${msg}` : `ℹ️ ${msg}`;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        },

        openModal(id) {
            const emp = App.state.data.find(e => e.employeeNum == id);
            if (!emp) return;

            document.getElementById('modal-title').innerText = emp.name;
            document.getElementById('modal-content').innerHTML = `
                <div class="bento-grid" style="grid-template-columns: 1fr 1fr; margin-bottom: 2rem;">
                    <div><span class="text-gray-400">ID:</span> ${emp.employeeNum}</div>
                    <div><span class="text-gray-400">Factory:</span> ${emp.haken}</div>
                    <div><span class="text-gray-400">Granted:</span> ${emp.granted}</div>
                    <div><span class="text-gray-400">Used:</span> ${emp.used}</div>
                    <div><span class="text-gray-400">Balance:</span> ${emp.balance}</div>
                    <div><span class="text-gray-400">Rate:</span> ${emp.usageRate}%</div>
                </div>
            `;
            document.getElementById('detail-modal').classList.add('active');
        },

        closeModal() {
            document.getElementById('detail-modal').classList.remove('active');
        }
    },

    charts: {
        destroy(id) {
            if (App.state.charts[id]) {
                App.state.charts[id].destroy();
            }
        },

        renderDistribution() {
            const container = document.getElementById('chart-distribution');
            if (!container) return;

            this.destroy('distribution');

            const data = App.data.getFiltered();
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
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
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
                colors: ['#f87171', '#fbbf24', '#38bdf8', '#34d399'],
                legend: {
                    position: 'right',
                    labels: {
                        colors: '#94a3b8'
                    },
                    markers: {
                        width: 12,
                        height: 12,
                        radius: 3
                    }
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
                                value: {
                                    color: '#e2e8f0',
                                    fontSize: '22px',
                                    fontWeight: 600
                                }
                            }
                        }
                    }
                },
                dataLabels: {
                    enabled: true,
                    style: {
                        fontSize: '14px',
                        fontWeight: 'bold'
                    },
                    dropShadow: {
                        enabled: true,
                        blur: 3,
                        opacity: 0.8
                    }
                },
                stroke: {
                    width: 0
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function(value) {
                            return value + ' employees'
                        }
                    }
                }
            };

            App.state.charts['distribution'] = new ApexCharts(container, options);
            App.state.charts['distribution'].render();
        },

        async renderTrends() {
            const container = document.getElementById('chart-trends');
            if (!container) return;
            this.destroy('trends');

            let trendsData = Array(12).fill(0);
            try {
                if (App.state.year) {
                    const res = await fetch(`${App.config.apiBase}/yukyu/monthly-summary/${App.state.year}`);
                    const json = await res.json();
                    if (json.data) {
                        json.data.forEach(m => {
                            // m.month is 1-12
                            if (m.month >= 1 && m.month <= 12) {
                                trendsData[m.month - 1] = m.total_days;
                            }
                        });
                    }
                }
            } catch (e) { console.error("Trend fetch error", e); }

            const options = {
                series: [{
                    name: 'Days Used',
                    data: trendsData
                }],
                chart: {
                    type: 'area',
                    height: 320,
                    background: 'transparent',
                    toolbar: {
                        show: true,
                        tools: {
                            download: true,
                            zoom: true,
                            zoomin: true,
                            zoomout: true,
                            pan: false
                        }
                    },
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800,
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
                    },
                    dropShadow: {
                        enabled: true,
                        top: 3,
                        left: 0,
                        blur: 15,
                        opacity: 0.2,
                        color: '#818cf8'
                    }
                },
                colors: ['#818cf8'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shade: 'dark',
                        type: 'vertical',
                        shadeIntensity: 0.5,
                        gradientToColors: ['#38bdf8'],
                        opacityFrom: 0.7,
                        opacityTo: 0.2,
                        stops: [0, 100]
                    }
                },
                stroke: {
                    curve: 'smooth',
                    width: 3,
                    colors: ['#818cf8']
                },
                dataLabels: {
                    enabled: false
                },
                markers: {
                    size: 5,
                    colors: ['#818cf8'],
                    strokeColors: '#fff',
                    strokeWidth: 2,
                    hover: {
                        size: 7
                    }
                },
                xaxis: {
                    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    },
                    axisBorder: {
                        show: false
                    },
                    axisTicks: {
                        show: false
                    }
                },
                yaxis: {
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        },
                        formatter: function(value) {
                            return Math.round(value)
                        }
                    }
                },
                grid: {
                    borderColor: 'rgba(255,255,255,0.05)',
                    strokeDashArray: 4,
                    xaxis: {
                        lines: {
                            show: false
                        }
                    }
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function(value) {
                            return value.toFixed(1) + ' days'
                        }
                    }
                }
            };

            App.state.charts['trends'] = new ApexCharts(container, options);
            App.state.charts['trends'].render();
        },

        renderFactoryChart() {
            const container = document.getElementById('chart-factories');
            if (!container) return;

            this.destroy('factories');
            const stats = App.data.getFactoryStats().slice(0, 10); // Top 10

            const options = {
                series: [{
                    name: 'Days Used',
                    data: stats.map(s => s[1])
                }],
                chart: {
                    type: 'bar',
                    height: 500,
                    background: 'transparent',
                    toolbar: {
                        show: true
                    },
                    animations: {
                        enabled: true,
                        easing: 'easeinout',
                        speed: 800,
                        animateGradually: {
                            enabled: true,
                            delay: 150
                        },
                        dynamicAnimation: {
                            enabled: true,
                            speed: 350
                        }
                    }
                },
                plotOptions: {
                    bar: {
                        horizontal: true,
                        borderRadius: 8,
                        dataLabels: {
                            position: 'top'
                        },
                        distributed: true
                    }
                },
                colors: ['#38bdf8', '#818cf8', '#f472b6', '#34d399', '#fbbf24',
                         '#60a5fa', '#a78bfa', '#fb923c', '#4ade80', '#facc15'],
                dataLabels: {
                    enabled: true,
                    style: {
                        fontSize: '12px',
                        colors: ['#fff']
                    },
                    formatter: function(value) {
                        return value.toFixed(1)
                    },
                    offsetX: 30
                },
                xaxis: {
                    categories: stats.map(s => s[0]),
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    },
                    axisBorder: {
                        show: false
                    }
                },
                yaxis: {
                    labels: {
                        style: {
                            colors: '#94a3b8'
                        }
                    }
                },
                grid: {
                    borderColor: 'rgba(255,255,255,0.05)',
                    xaxis: {
                        lines: {
                            show: true
                        }
                    },
                    yaxis: {
                        lines: {
                            show: false
                        }
                    }
                },
                tooltip: {
                    theme: 'dark',
                    y: {
                        formatter: function(value) {
                            return value.toFixed(1) + ' days'
                        }
                    }
                },
                legend: {
                    show: false
                }
            };

            App.state.charts['factories'] = new ApexCharts(container, options);
            App.state.charts['factories'].render();
        }
    },

    events: {
        setupListeners() {
            // Close modal when clicking outside
            document.getElementById('detail-modal').addEventListener('click', (e) => {
                if (e.target.id === 'detail-modal') App.ui.closeModal();
            });

            // Event delegation for employee rows (XSS-safe)
            const tableBody = document.getElementById('table-body');
            if (tableBody) {
                tableBody.addEventListener('click', (e) => {
                    const row = e.target.closest('.employee-row');
                    if (row && row.dataset.employeeNum) {
                        App.ui.openModal(row.dataset.employeeNum);
                    }
                });
            }

            // Event delegation for search results
            const searchResults = document.getElementById('emp-search-results');
            if (searchResults) {
                searchResults.addEventListener('click', (e) => {
                    const item = e.target.closest('.search-result-item');
                    if (item && item.dataset.employeeNum) {
                        App.requests.selectEmployee(item.dataset.employeeNum);
                    }
                });
            }

            // Event delegation for leave request actions
            const pendingList = document.getElementById('pending-requests');
            if (pendingList) {
                pendingList.addEventListener('click', (e) => {
                    const approveBtn = e.target.closest('.btn-approve');
                    const rejectBtn = e.target.closest('.btn-reject');
                    if (approveBtn && approveBtn.dataset.requestId) {
                        App.requests.approve(parseInt(approveBtn.dataset.requestId));
                    }
                    if (rejectBtn && rejectBtn.dataset.requestId) {
                        App.requests.reject(parseInt(rejectBtn.dataset.requestId));
                    }
                });
            }

            // Keyboard navigation
            document.addEventListener('keydown', (e) => {
                // ESC to close modal
                if (e.key === 'Escape') {
                    const modal = document.getElementById('detail-modal');
                    if (modal && modal.classList.contains('active')) {
                        App.ui.closeModal();
                    }
                }
            });
        }
    },

    // ========================================
    // REQUESTS MODULE (申請)
    // ========================================
    requests: {
        selectedEmployee: null,
        searchTimeout: null,
        factories: [],

        async loadFactories() {
            try {
                const res = await fetch(`${App.config.apiBase}/factories?status=在職中`);
                const json = await res.json();

                if (json.data) {
                    this.factories = json.data;
                    const select = document.getElementById('factory-filter');
                    if (select) {
                        // Keep first option (All Factories)
                        select.innerHTML = '<option value="">すべての工場 (All Factories)</option>';
                        this.factories.forEach(factory => {
                            const opt = document.createElement('option');
                            opt.value = factory;
                            opt.textContent = factory;
                            select.appendChild(opt);
                        });
                    }
                }
            } catch (e) {
                console.error('Failed to load factories:', e);
            }
        },

        filterByFactory() {
            const factory = document.getElementById('factory-filter').value;
            const searchInput = document.getElementById('emp-search');
            const query = searchInput.value;

            // If factory is selected, show employees from that factory
            if (factory) {
                this.searchWithFactory(query, factory);
            } else {
                // If no factory selected and no query, clear results
                if (!query || query.length < 2) {
                    document.getElementById('emp-search-results').innerHTML = '';
                } else {
                    this.searchEmployee(query);
                }
            }
        },

        async searchWithFactory(query, factory) {
            try {
                let url = `${App.config.apiBase}/employees/search?status=在職中`;
                if (query) url += `&q=${encodeURIComponent(query)}`;
                if (factory) url += `&factory=${encodeURIComponent(factory)}`;

                const res = await fetch(url);
                const json = await res.json();

                const container = document.getElementById('emp-search-results');
                if (json.data && json.data.length > 0) {
                    container.innerHTML = json.data.slice(0, 15).map(emp => {
                        const empNum = App.utils.escapeAttr(emp.employee_num);
                        const name = App.utils.escapeHtml(emp.name);
                        const empFactory = App.utils.escapeHtml(emp.factory || '-');
                        const type = App.utils.escapeHtml(emp.type);
                        return `
                        <div class="search-result-item" data-employee-num="${empNum}"
                             style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s;">
                            <div style="font-weight: 600;">${name}</div>
                            <div style="font-size: 0.85rem; color: var(--muted);">${empNum} | ${empFactory} | ${type}</div>
                        </div>
                    `}).join('');
                } else {
                    container.innerHTML = '<div style="padding: 1rem; color: var(--muted); text-align: center;">No results found</div>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async searchEmployee(query) {
            if (this.searchTimeout) clearTimeout(this.searchTimeout);

            const factory = document.getElementById('factory-filter')?.value || '';

            // If factory is selected, allow search with shorter query
            if (!factory && (!query || query.length < 2)) {
                document.getElementById('emp-search-results').innerHTML = '';
                return;
            }

            this.searchTimeout = setTimeout(async () => {
                try {
                    let url = `${App.config.apiBase}/employees/search?status=在職中`;
                    if (query) url += `&q=${encodeURIComponent(query)}`;
                    if (factory) url += `&factory=${encodeURIComponent(factory)}`;

                    const res = await fetch(url);
                    const json = await res.json();

                    const container = document.getElementById('emp-search-results');
                    if (json.data && json.data.length > 0) {
                        // Using data attributes instead of inline onclick (XSS prevention)
                        container.innerHTML = json.data.slice(0, 15).map(emp => {
                            const empNum = App.utils.escapeAttr(emp.employee_num);
                            const name = App.utils.escapeHtml(emp.name);
                            const empFactory = App.utils.escapeHtml(emp.factory || '-');
                            const type = App.utils.escapeHtml(emp.type);
                            return `
                            <div class="search-result-item" data-employee-num="${empNum}"
                                 style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s;">
                                <div style="font-weight: 600;">${name}</div>
                                <div style="font-size: 0.85rem; color: var(--muted);">${empNum} | ${empFactory} | ${type}</div>
                            </div>
                        `}).join('');
                    } else {
                        container.innerHTML = '<div style="padding: 1rem; color: var(--muted); text-align: center;">No results found</div>';
                    }
                } catch (e) {
                    console.error(e);
                }
            }, 300);
        },

        async selectEmployee(empNum) {
            try {
                const res = await fetch(`${App.config.apiBase}/employees/${empNum}/leave-info`);
                const json = await res.json();

                if (json.employee) {
                    this.selectedEmployee = json;

                    // Update UI
                    document.getElementById('selected-emp-info').style.display = 'block';
                    document.getElementById('selected-emp-name').innerText = json.employee.name;
                    document.getElementById('selected-emp-details').innerText =
                        `${json.employee.employee_num} | ${json.employee.factory || '-'} | ${json.employee.type}`;
                    document.getElementById('selected-emp-balance').innerText = json.total_available.toFixed(1) + '日';

                    // Show hourly wage info if available
                    const hourlyWageInfo = document.getElementById('hourly-wage-info');
                    if (json.hourly_wage && json.hourly_wage > 0) {
                        hourlyWageInfo.style.display = 'block';
                        document.getElementById('selected-emp-wage').innerText = `¥${json.hourly_wage.toLocaleString()}`;
                        const totalHours = json.total_hours_available || (json.total_available * 8);
                        document.getElementById('selected-emp-hours').innerText = `${totalHours.toFixed(0)}時間`;
                    } else {
                        hourlyWageInfo.style.display = 'none';
                    }

                    // Show usage history
                    this.renderUsageHistory(json);

                    // Clear search and mark as valid
                    document.getElementById('emp-search').value = json.employee.name;
                    document.getElementById('emp-search').classList.add('is-valid');
                    document.getElementById('emp-search-results').innerHTML = '';

                    // Update progress steps
                    this.updateProgressSteps(2);

                    // Update cost estimate if hourly is selected
                    this.updateCostEstimate();
                }
            } catch (e) {
                App.ui.showToast('error', 'Failed to load employee info');
            }
        },

        toggleLeaveType() {
            const leaveType = document.getElementById('leave-type').value;
            const daysContainer = document.getElementById('days-input-container');
            const hoursContainer = document.getElementById('hours-input-container');
            const costContainer = document.getElementById('cost-estimate-container');

            if (leaveType === 'hourly') {
                daysContainer.style.display = 'none';
                hoursContainer.style.display = 'block';
                costContainer.style.display = 'block';
                this.updateCostEstimate();
            } else {
                daysContainer.style.display = 'block';
                hoursContainer.style.display = 'none';
                costContainer.style.display = 'none';

                // Set default days based on type
                const daysInput = document.getElementById('days-requested');
                if (leaveType === 'half_am' || leaveType === 'half_pm') {
                    daysInput.value = '0.5';
                } else {
                    daysInput.value = '1';
                }
            }
        },

        updateCostEstimate() {
            if (!this.selectedEmployee || !this.selectedEmployee.hourly_wage) {
                document.getElementById('cost-estimate').innerText = '-';
                return;
            }

            const hours = parseFloat(document.getElementById('hours-requested').value) || 0;
            const wage = this.selectedEmployee.hourly_wage;
            const cost = hours * wage;

            document.getElementById('cost-estimate').innerText = `¥${cost.toLocaleString()}`;
        },

        renderUsageHistory(json) {
            const container = document.getElementById('usage-history-container');
            const summaryEl = document.getElementById('usage-history-summary');
            const detailEl = document.getElementById('usage-history-detail');

            // Check if we have history data
            const history = json.history || [];
            const usageHistory = json.usage_history || [];

            if (history.length === 0 && usageHistory.length === 0) {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'block';

            // Build summary by year (from history data)
            let summaryHtml = '<div style="display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">';
            history.forEach(h => {
                const year = h.year;
                const used = h.used || 0;
                const granted = h.granted || 0;
                summaryHtml += `
                    <div style="padding: 0.5rem 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px; font-size: 0.8rem;">
                        <span style="color: var(--primary); font-weight: 600;">${year}年</span>
                        <span style="margin-left: 0.5rem;">使用: ${used}日</span>
                        <span style="margin-left: 0.5rem; color: var(--muted);">/ ${granted}日</span>
                    </div>
                `;
            });
            summaryHtml += '</div>';
            summaryEl.innerHTML = summaryHtml;

            // Build detail list (individual usage dates)
            if (usageHistory.length > 0) {
                let detailHtml = '<table style="width: 100%; font-size: 0.8rem; border-collapse: collapse;">';
                detailHtml += '<thead><tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">';
                detailHtml += '<th style="text-align: left; padding: 0.5rem;">日付</th>';
                detailHtml += '<th style="text-align: right; padding: 0.5rem;">日数</th>';
                detailHtml += '<th style="text-align: right; padding: 0.5rem;">年度</th>';
                detailHtml += '</tr></thead><tbody>';

                usageHistory.forEach(u => {
                    const date = u.date || '-';
                    const days = u.days || 0;
                    const year = u.year || '-';
                    detailHtml += `
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <td style="padding: 0.5rem;">${App.utils.escapeHtml(date)}</td>
                            <td style="text-align: right; padding: 0.5rem;">${days}日</td>
                            <td style="text-align: right; padding: 0.5rem; color: var(--muted);">${year}</td>
                        </tr>
                    `;
                });

                detailHtml += '</tbody></table>';
                detailEl.innerHTML = detailHtml;
            } else {
                detailEl.innerHTML = '<div style="color: var(--muted); font-size: 0.8rem; padding: 0.5rem;">使用履歴の詳細はありません</div>';
            }
        },

        toggleUsageHistory() {
            const detailEl = document.getElementById('usage-history-detail');
            const btn = event.target;
            if (detailEl.style.display === 'none') {
                detailEl.style.display = 'block';
                btn.innerText = '詳細を隠す';
            } else {
                detailEl.style.display = 'none';
                btn.innerText = '詳細を表示';
            }
        },

        // ===== UX IMPROVEMENTS =====

        // Update progress steps
        updateProgressSteps(step) {
            for (let i = 1; i <= 3; i++) {
                const el = document.getElementById(`step-${i}`);
                el.classList.remove('active', 'completed');
                if (i < step) el.classList.add('completed');
                if (i === step) el.classList.add('active');
            }
        },

        // Validate dates inline
        validateDates() {
            const startDate = document.getElementById('start-date');
            const endDate = document.getElementById('end-date');
            const startValidation = document.getElementById('start-date-validation');
            const endValidation = document.getElementById('end-date-validation');
            let isValid = true;

            // Reset
            startDate.classList.remove('is-valid', 'is-invalid');
            endDate.classList.remove('is-valid', 'is-invalid');
            startValidation.classList.remove('show', 'error', 'success');
            endValidation.classList.remove('show', 'error', 'success');

            const today = new Date().toISOString().split('T')[0];

            if (startDate.value) {
                if (startDate.value < today) {
                    startDate.classList.add('is-invalid');
                    startValidation.innerHTML = '⚠️ 過去の日付は選択できません';
                    startValidation.classList.add('show', 'error');
                    isValid = false;
                } else {
                    startDate.classList.add('is-valid');
                }
            }

            if (endDate.value && startDate.value) {
                if (endDate.value < startDate.value) {
                    endDate.classList.add('is-invalid');
                    endValidation.innerHTML = '⚠️ 終了日は開始日以降にしてください';
                    endValidation.classList.add('show', 'error');
                    isValid = false;
                } else {
                    endDate.classList.add('is-valid');
                }
            }

            // Update progress if employee selected and dates valid
            if (this.selectedEmployee && startDate.value && endDate.value && isValid) {
                this.updateProgressSteps(2);
            }

            return isValid;
        },

        // Validate days inline
        validateDays() {
            const daysInput = document.getElementById('days-requested');
            const validation = document.getElementById('days-validation');
            const days = parseFloat(daysInput.value) || 0;

            daysInput.classList.remove('is-valid', 'is-invalid');
            validation.classList.remove('show', 'error', 'warning', 'success');

            if (!this.selectedEmployee) return;

            const available = this.selectedEmployee.total_available || 0;

            if (days <= 0) {
                daysInput.classList.add('is-invalid');
                validation.innerHTML = '⚠️ 日数を入力してください';
                validation.classList.add('show', 'error');
                return false;
            }

            if (days > available) {
                daysInput.classList.add('is-invalid');
                validation.innerHTML = `⚠️ 残り${available}日を超えています`;
                validation.classList.add('show', 'error');
                return false;
            }

            if (days > available * 0.8) {
                daysInput.classList.add('is-valid');
                validation.innerHTML = `ℹ️ 残り${(available - days).toFixed(1)}日になります`;
                validation.classList.add('show', 'warning');
                return true;
            }

            daysInput.classList.add('is-valid');
            return true;
        },

        // Validate hours inline
        validateHours() {
            const hoursInput = document.getElementById('hours-requested');
            const validation = document.getElementById('hours-validation');
            const hours = parseFloat(hoursInput.value) || 0;

            hoursInput.classList.remove('is-valid', 'is-invalid');
            validation.classList.remove('show', 'error', 'warning', 'success');

            if (!this.selectedEmployee) return;

            const totalHours = this.selectedEmployee.total_hours_available || (this.selectedEmployee.total_available * 8);

            if (hours <= 0 || hours > 7) {
                hoursInput.classList.add('is-invalid');
                validation.innerHTML = '⚠️ 1〜7時間の範囲で入力してください';
                validation.classList.add('show', 'error');
                return false;
            }

            if (hours > totalHours) {
                hoursInput.classList.add('is-invalid');
                validation.innerHTML = `⚠️ 残り${totalHours.toFixed(0)}時間を超えています`;
                validation.classList.add('show', 'error');
                return false;
            }

            hoursInput.classList.add('is-valid');
            return true;
        },

        // Update character counter
        updateCharCounter() {
            const textarea = document.getElementById('leave-reason');
            const counter = document.getElementById('reason-char-counter');
            const length = textarea.value.length;
            const max = 200;

            counter.textContent = `${length} / ${max}`;
            counter.classList.remove('warning', 'danger');

            if (length > max * 0.9) {
                counter.classList.add('danger');
            } else if (length > max * 0.7) {
                counter.classList.add('warning');
            }
        },

        // Show confirmation modal
        showConfirmation() {
            // Validate all fields first
            if (!this.selectedEmployee) {
                App.ui.showToast('error', '従業員を選択してください');
                document.getElementById('emp-search').focus();
                return;
            }

            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;

            if (!startDate || !endDate) {
                App.ui.showToast('error', '日付を入力してください');
                return;
            }

            if (!this.validateDates()) {
                App.ui.showToast('error', '日付を確認してください');
                return;
            }

            const leaveType = document.getElementById('leave-type').value;
            const isHourly = leaveType === 'hourly';

            if (isHourly && !this.validateHours()) {
                return;
            } else if (!isHourly && !this.validateDays()) {
                return;
            }

            // Update progress to step 3
            this.updateProgressSteps(3);

            // Populate confirmation modal
            document.getElementById('confirm-employee').textContent = this.selectedEmployee.employee.name;
            document.getElementById('confirm-factory').textContent = this.selectedEmployee.employee.factory || '-';
            document.getElementById('confirm-dates').textContent = `${startDate} 〜 ${endDate}`;

            const typeLabels = {
                'full': '全日休暇',
                'half_am': '午前半休',
                'half_pm': '午後半休',
                'hourly': '時間休'
            };
            document.getElementById('confirm-type').textContent = typeLabels[leaveType] || leaveType;

            if (isHourly) {
                const hours = parseFloat(document.getElementById('hours-requested').value) || 0;
                document.getElementById('confirm-amount').textContent = `${hours}時間`;

                const wage = this.selectedEmployee.hourly_wage || 0;
                const cost = hours * wage;
                document.getElementById('confirm-cost').textContent = `¥${cost.toLocaleString()}`;
                document.getElementById('confirm-cost-row').style.display = 'flex';
            } else {
                const days = parseFloat(document.getElementById('days-requested').value) || 0;
                document.getElementById('confirm-amount').textContent = `${days}日`;
                document.getElementById('confirm-cost-row').style.display = 'none';
            }

            const available = this.selectedEmployee.total_available || 0;
            const requested = isHourly
                ? (parseFloat(document.getElementById('hours-requested').value) || 0) / 8
                : (parseFloat(document.getElementById('days-requested').value) || 0);
            const remaining = (available - requested).toFixed(1);
            document.getElementById('confirm-balance').textContent = `${available}日 → ${remaining}日`;

            const reason = document.getElementById('leave-reason').value || '(なし)';
            document.getElementById('confirm-reason').textContent = reason;

            // Show modal
            document.getElementById('confirm-modal').classList.add('active');
        },

        hideConfirmation() {
            document.getElementById('confirm-modal').classList.remove('active');
            this.updateProgressSteps(2);
        },

        async submitConfirmed() {
            // Add loading state to button
            const submitBtn = document.getElementById('confirm-submit-btn');
            submitBtn.classList.add('is-loading');

            try {
                await this.submit();
                this.hideConfirmation();
            } finally {
                submitBtn.classList.remove('is-loading');
            }
        },

        async submit() {
            if (!this.selectedEmployee) {
                App.ui.showToast('error', '従業員を選択してください');
                return;
            }

            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const leaveType = document.getElementById('leave-type').value;
            const reason = document.getElementById('leave-reason').value;

            // Determine days and hours based on leave type
            let daysRequested = 0;
            let hoursRequested = 0;

            if (leaveType === 'hourly') {
                hoursRequested = parseFloat(document.getElementById('hours-requested').value) || 0;
                daysRequested = hoursRequested / 8; // Convert hours to days for balance check
            } else {
                daysRequested = parseFloat(document.getElementById('days-requested').value) || 0;
            }

            if (!startDate || !endDate) {
                App.ui.showToast('error', '日付を入力してください');
                return;
            }

            // Validate based on leave type
            if (leaveType === 'hourly') {
                if (hoursRequested <= 0 || hoursRequested > 7) {
                    App.ui.showToast('error', '時間数は1〜7時間の範囲で入力してください');
                    return;
                }
                const totalHoursAvailable = this.selectedEmployee.total_hours_available || (this.selectedEmployee.total_available * 8);
                if (hoursRequested > totalHoursAvailable) {
                    App.ui.showToast('error', `残時間が不足しています (残り: ${totalHoursAvailable.toFixed(0)}時間)`);
                    return;
                }
            } else {
                if (daysRequested > this.selectedEmployee.total_available) {
                    App.ui.showToast('error', `残日数が不足しています (残り: ${this.selectedEmployee.total_available}日)`);
                    return;
                }
            }

            // Calculate cost estimate for hourly leave
            const hourlyWage = this.selectedEmployee.hourly_wage || 0;
            const costEstimate = leaveType === 'hourly' ? hoursRequested * hourlyWage : 0;

            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        employee_num: this.selectedEmployee.employee.employee_num,
                        employee_name: this.selectedEmployee.employee.name,
                        start_date: startDate,
                        end_date: endDate,
                        days_requested: daysRequested,
                        hours_requested: hoursRequested,
                        leave_type: leaveType,
                        reason: reason,
                        hourly_wage: hourlyWage,
                        cost_estimate: costEstimate
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Request failed');
                }

                const typeLabel = leaveType === 'hourly' ? `${hoursRequested}時間` : `${daysRequested}日`;
                App.ui.showToast('success', `申請が送信されました (${typeLabel})`);
                this.resetForm();
                this.loadPending();
                this.loadHistory();

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        resetForm() {
            this.selectedEmployee = null;
            document.getElementById('factory-filter').value = '';
            document.getElementById('emp-search').value = '';
            document.getElementById('emp-search-results').innerHTML = '';
            document.getElementById('selected-emp-info').style.display = 'none';
            document.getElementById('hourly-wage-info').style.display = 'none';
            document.getElementById('usage-history-container').style.display = 'none';
            document.getElementById('start-date').value = '';
            document.getElementById('end-date').value = '';
            document.getElementById('days-requested').value = '1';
            document.getElementById('hours-requested').value = '1';
            document.getElementById('leave-type').value = 'full';
            document.getElementById('leave-reason').value = '';

            // Reset to days mode
            document.getElementById('days-input-container').style.display = 'block';
            document.getElementById('hours-input-container').style.display = 'none';
            document.getElementById('cost-estimate-container').style.display = 'none';

            // Reset validation states
            ['emp-search', 'start-date', 'end-date', 'days-requested', 'hours-requested'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.remove('is-valid', 'is-invalid');
            });

            // Reset validation messages
            ['emp-search-validation', 'start-date-validation', 'end-date-validation', 'days-validation', 'hours-validation'].forEach(id => {
                const el = document.getElementById(id);
                if (el) {
                    el.classList.remove('show', 'error', 'success', 'warning');
                    el.innerHTML = '';
                }
            });

            // Reset progress steps
            this.updateProgressSteps(1);

            // Reset char counter
            const charCounter = document.getElementById('reason-char-counter');
            if (charCounter) charCounter.textContent = '0 / 200';
        },

        async loadPending() {
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests?status=PENDING`);
                const json = await res.json();

                const container = document.getElementById('pending-requests');
                if (json.data && json.data.length > 0) {
                    container.innerHTML = json.data.map(req => {
                        // Display hours or days based on leave type
                        const isHourly = req.leave_type === 'hourly';
                        const duration = isHourly
                            ? `${App.utils.safeNumber(req.hours_requested)}時間`
                            : `${App.utils.safeNumber(req.days_requested)}日`;
                        const typeLabel = {
                            'full': '全日',
                            'half_am': '午前半休',
                            'half_pm': '午後半休',
                            'hourly': '時間休'
                        }[req.leave_type] || '';
                        const costInfo = isHourly && req.cost_estimate > 0
                            ? `<div style="font-size: 0.8rem; color: var(--warning); margin-top: 0.25rem;">💰 見積: ¥${App.utils.safeNumber(req.cost_estimate).toLocaleString()}</div>`
                            : '';

                        // XSS prevention: escape all user data and use data attributes
                        const empName = App.utils.escapeHtml(req.employee_name);
                        const startDate = App.utils.escapeHtml(req.start_date);
                        const endDate = App.utils.escapeHtml(req.end_date);
                        const reason = App.utils.escapeHtml(req.reason || '-');
                        const reqId = parseInt(req.id) || 0;

                        return `
                            <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.75rem;">
                                <div class="flex-between">
                                    <div>
                                        <div style="font-weight: 600;">${empName}</div>
                                        <div style="font-size: 0.85rem; color: var(--muted);">
                                            ${startDate} 〜 ${endDate}
                                            <span class="badge badge-info" style="margin-left: 0.5rem; padding: 0.15rem 0.5rem; font-size: 0.7rem;">${typeLabel}</span>
                                            (${duration})
                                        </div>
                                        <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem;">${reason}</div>
                                        ${costInfo}
                                    </div>
                                    <div style="display: flex; gap: 0.5rem;">
                                        <button class="btn btn-glass btn-approve" data-request-id="${reqId}"
                                            style="background: rgba(52, 211, 153, 0.2); padding: 0.5rem 1rem;">✓ 承認</button>
                                        <button class="btn btn-glass btn-reject" data-request-id="${reqId}"
                                            style="background: rgba(248, 113, 113, 0.2); padding: 0.5rem 1rem;">✗ 却下</button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">承認待ちの申請はありません</div>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async loadHistory() {
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests`);
                const json = await res.json();

                const tbody = document.getElementById('requests-history');
                if (json.data && json.data.length > 0) {
                    tbody.innerHTML = json.data.map(req => {
                        const statusBadge = req.status === 'APPROVED' ? 'badge-success' :
                            req.status === 'REJECTED' ? 'badge-danger' : 'badge-warning';
                        const statusText = req.status === 'APPROVED' ? '承認済' :
                            req.status === 'REJECTED' ? '却下' : '審査中';

                        // Display hours or days based on leave type
                        const isHourly = req.leave_type === 'hourly';
                        const duration = isHourly
                            ? `${req.hours_requested || 0}時間`
                            : `${req.days_requested}日`;
                        const typeLabel = {
                            'full': '全日',
                            'half_am': '午前半休',
                            'half_pm': '午後半休',
                            'hourly': '時間休'
                        }[req.leave_type] || '全日';

                        return `
                            <tr>
                                <td>${req.id}</td>
                                <td>${req.employee_name}</td>
                                <td>${req.start_date} 〜 ${req.end_date}</td>
                                <td>
                                    <span class="badge badge-info" style="margin-right: 0.25rem; padding: 0.1rem 0.4rem; font-size: 0.65rem;">${typeLabel}</span>
                                    ${duration}
                                </td>
                                <td>${req.reason || '-'}</td>
                                <td><span class="badge ${statusBadge}">${statusText}</span></td>
                                <td>${req.requested_at?.slice(0, 10) || '-'}</td>
                            </tr>
                        `;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;">申請履歴がありません</td></tr>';
                }
            } catch (e) {
                console.error(e);
            }
        },

        async approve(requestId) {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}/approve`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ approved_by: 'Manager' })
                });

                if (!res.ok) throw new Error('Approval failed');

                App.ui.showToast('success', '申請を承認しました');
                this.loadPending();
                this.loadHistory();
                App.data.fetchEmployees(App.state.year); // Refresh balance

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        },

        async reject(requestId) {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests/${requestId}/reject`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rejected_by: 'Manager' })
                });

                if (!res.ok) throw new Error('Rejection failed');

                App.ui.showToast('success', '申請を却下しました');
                this.loadPending();
                this.loadHistory();

            } catch (e) {
                App.ui.showToast('error', e.message);
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // COMPLIANCE MODULE
    // ========================================
    compliance: {
        async check5Day() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/5day-check/${year}`);
                const json = await res.json();

                // Update summary cards
                document.getElementById('comp-total').innerText = json.summary.total_checked;
                document.getElementById('comp-compliant').innerText = json.summary.compliant;
                document.getElementById('comp-atrisk').innerText = json.summary.at_risk;
                document.getElementById('comp-noncompliant').innerText = json.summary.non_compliant;

                // Show non-compliant list
                const container = document.getElementById('compliance-list');
                if (json.non_compliant_employees && json.non_compliant_employees.length > 0) {
                    container.innerHTML = json.non_compliant_employees.map(emp => {
                        const statusColor = emp.status === 'non_compliant' ? 'var(--danger)' : 'var(--warning)';
                        return `
                            <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid ${statusColor};">
                                <div class="flex-between">
                                    <div>
                                        <div style="font-weight: 600;">${emp.name}</div>
                                        <div style="font-size: 0.85rem; color: var(--muted);">${emp.employee_num}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="font-size: 1.1rem; font-weight: 700; color: ${statusColor};">${emp.days_used.toFixed(1)}日</div>
                                        <div style="font-size: 0.8rem; color: var(--muted);">残り ${emp.days_remaining.toFixed(1)}日必要</div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">✅ 全員が5日取得義務を達成しています</div>';
                }

                App.ui.showToast('success', `Compliance check completed for ${year}`);

            } catch (e) {
                App.ui.showToast('error', 'Compliance check failed');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadAlerts() {
            try {
                const res = await fetch(`${App.config.apiBase}/compliance/alerts`);
                const json = await res.json();

                const container = document.getElementById('alerts-container');
                if (json.alerts && json.alerts.length > 0) {
                    container.innerHTML = json.alerts.map(alert => {
                        const levelIcon = alert.level === 'critical' ? '🔴' : alert.level === 'warning' ? '🟡' : '🔵';
                        return `
                            <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                                <div style="font-weight: 600;">${levelIcon} ${alert.employee_name}</div>
                                <div style="font-size: 0.9rem; margin-top: 0.25rem;">${alert.message_ja}</div>
                                <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.5rem;">
                                    対応: ${alert.action_required || '-'}
                                </div>
                            </div>
                        `;
                    }).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--success);">✅ アラートはありません</div>';
                }

            } catch (e) {
                console.error(e);
            }
        },

        async loadLedger() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/annual-ledger/${year}`);
                const json = await res.json();

                const container = document.getElementById('ledger-container');
                if (json.entries && json.entries.length > 0) {
                    container.innerHTML = `
                        <table class="modern-table">
                            <thead>
                                <tr>
                                    <th>社員番号</th>
                                    <th>氏名</th>
                                    <th>基準日</th>
                                    <th>付与日数</th>
                                    <th>取得日数</th>
                                    <th>残日数</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${json.entries.map(e => `
                                    <tr>
                                        <td>${e.employee_num}</td>
                                        <td>${e.employee_name}</td>
                                        <td>${e.grant_date}</td>
                                        <td>${e.granted_days}</td>
                                        <td>${e.used_days}</td>
                                        <td>${e.remaining_days}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                } else {
                    container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--muted);">データがありません</div>';
                }

            } catch (e) {
                App.ui.showToast('error', 'Failed to load ledger');
            } finally {
                App.ui.hideLoading();
            }
        },

        async exportLedger(format = 'csv') {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/compliance/export-ledger/${year}?format=${format}`, {
                    method: 'POST'
                });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `年次有給休暇管理簿を出力しました: ${json.filename}`);
                }

            } catch (e) {
                App.ui.showToast('error', 'Export failed');
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // SETTINGS MODULE
    // ========================================
    settings: {
        async loadSnapshot() {
            try {
                const res = await fetch(`${App.config.apiBase}/system/snapshot`);
                const json = await res.json();

                if (json.snapshot) {
                    const s = json.snapshot;
                    document.getElementById('sys-db-size').innerText = s.database_size_kb.toFixed(1) + ' KB';
                    document.getElementById('sys-emp-count').innerText = s.employees_count;
                    document.getElementById('sys-health').innerText = s.health_status;
                    document.getElementById('sys-health').style.color =
                        s.health_status === 'HEALTHY' ? 'var(--success)' : 'var(--danger)';
                }

                App.ui.showToast('success', 'System snapshot updated');

            } catch (e) {
                App.ui.showToast('error', 'Failed to load snapshot');
            }
        },

        async viewAuditLog() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/system/audit-log?limit=50`);
                const json = await res.json();

                let content = '<div style="max-height: 400px; overflow-y: auto;">';
                if (json.entries && json.entries.length > 0) {
                    content += json.entries.map(e => `
                        <div style="padding: 0.5rem; background: rgba(255,255,255,0.03); margin-bottom: 0.25rem; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">
                            <span style="color: var(--primary);">[${e.action}]</span>
                            <span style="color: var(--muted);">${e.entity_type}/${e.entity_id || '-'}</span>
                            <span style="color: #64748b; float: right;">${e.timestamp?.slice(0, 19)}</span>
                        </div>
                    `).join('');
                } else {
                    content += '<div style="text-align: center; padding: 2rem; color: var(--muted);">No audit log entries</div>';
                }
                content += '</div>';

                document.getElementById('modal-title').innerText = '📜 Audit Log';
                document.getElementById('modal-content').innerHTML = content;
                document.getElementById('detail-modal').classList.add('active');

            } catch (e) {
                App.ui.showToast('error', 'Failed to load audit log');
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // CALENDAR MODULE
    // ========================================
    calendar: {
        currentYear: new Date().getFullYear(),
        currentMonth: new Date().getMonth() + 1,
        events: [],
        selectedDate: null,

        async loadEvents() {
            App.ui.showLoading();
            try {
                const res = await fetch(`${App.config.apiBase}/calendar/events?year=${this.currentYear}&month=${this.currentMonth}`);
                const json = await res.json();
                this.events = json.events || [];
                this.renderCalendar();
                this.updateMonthlySummary();
                App.ui.showToast('success', 'カレンダーを更新しました');
            } catch (e) {
                App.ui.showToast('error', 'カレンダーの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        renderCalendar() {
            const grid = document.getElementById('calendar-grid');
            const title = document.getElementById('calendar-month-title');

            // Update title
            const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
            title.innerText = `${this.currentYear}年 ${monthNames[this.currentMonth - 1]}`;

            // Clear existing days (keep headers)
            const headers = grid.querySelectorAll('.calendar-header');
            grid.innerHTML = '';
            headers.forEach(h => grid.appendChild(h));

            // Get first day and days in month
            const firstDay = new Date(this.currentYear, this.currentMonth - 1, 1).getDay();
            const daysInMonth = new Date(this.currentYear, this.currentMonth, 0).getDate();
            const daysInPrevMonth = new Date(this.currentYear, this.currentMonth - 1, 0).getDate();

            const today = new Date();
            const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

            // Previous month days
            for (let i = firstDay - 1; i >= 0; i--) {
                const day = daysInPrevMonth - i;
                grid.appendChild(this.createDayCell(day, true));
            }

            // Current month days
            for (let day = 1; day <= daysInMonth; day++) {
                const dateStr = `${this.currentYear}-${String(this.currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const isToday = dateStr === todayStr;
                const dayEvents = this.events.filter(e => e.start <= dateStr && e.end >= dateStr);
                grid.appendChild(this.createDayCell(day, false, isToday, dateStr, dayEvents));
            }

            // Next month days
            const totalCells = firstDay + daysInMonth;
            const remainingCells = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
            for (let day = 1; day <= remainingCells; day++) {
                grid.appendChild(this.createDayCell(day, true));
            }
        },

        createDayCell(day, isOtherMonth, isToday = false, dateStr = '', events = []) {
            const cell = document.createElement('div');
            cell.className = `calendar-day ${isOtherMonth ? 'other-month' : ''} ${isToday ? 'today' : ''} ${this.selectedDate === dateStr ? 'selected' : ''}`;

            if (!isOtherMonth && dateStr) {
                cell.onclick = () => this.selectDate(dateStr, events);
            }

            let html = `<div class="calendar-day-number">${day}</div>`;

            if (!isOtherMonth && events.length > 0) {
                const displayEvents = events.slice(0, 2);
                displayEvents.forEach(e => {
                    html += `<div class="calendar-event" style="background: ${e.color};">${e.title.split('(')[0].trim()}</div>`;
                });
                if (events.length > 2) {
                    html += `<div class="calendar-event-count">+${events.length - 2}</div>`;
                }
            }

            cell.innerHTML = html;
            return cell;
        },

        selectDate(dateStr, events) {
            this.selectedDate = dateStr;
            this.renderCalendar();

            document.getElementById('selected-date-display').innerText = dateStr;

            const container = document.getElementById('day-detail-container');
            if (events.length > 0) {
                container.innerHTML = events.map(e => {
                    const typeLabels = { 'full': '全日', 'half_am': '午前半休', 'half_pm': '午後半休', 'hourly': '時間休', 'usage': '使用日' };
                    const typeLabel = typeLabels[e.leave_type] || typeLabels[e.type] || '休暇';
                    return `
                        <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid ${e.color};">
                            <div style="font-weight: 600;">${e.employee_name}</div>
                            <div style="font-size: 0.85rem; color: var(--muted);">
                                ${typeLabel} ${e.days ? `(${e.days}日)` : ''} ${e.hours ? `(${e.hours}時間)` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">この日の休暇取得者はいません</div>';
            }
        },

        updateMonthlySummary() {
            const uniqueEmployees = new Set(this.events.map(e => e.employee_num));
            const totalDays = this.events.reduce((sum, e) => sum + (e.days || 0), 0);

            document.getElementById('cal-month-employees').innerText = uniqueEmployees.size;
            document.getElementById('cal-month-days').innerText = totalDays.toFixed(1);
        },

        prevMonth() {
            this.currentMonth--;
            if (this.currentMonth < 1) {
                this.currentMonth = 12;
                this.currentYear--;
            }
            this.loadEvents();
        },

        nextMonth() {
            this.currentMonth++;
            if (this.currentMonth > 12) {
                this.currentMonth = 1;
                this.currentYear++;
            }
            this.loadEvents();
        },

        goToToday() {
            this.currentYear = new Date().getFullYear();
            this.currentMonth = new Date().getMonth() + 1;
            this.loadEvents();
        }
    },

    // ========================================
    // ANALYTICS MODULE
    // ========================================
    analytics: {
        async loadDashboard() {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/analytics/dashboard/${year}`);
                const json = await res.json();

                // Update summary cards
                document.getElementById('ana-total-emp').innerText = json.summary.total_employees;
                document.getElementById('ana-total-granted').innerText = json.summary.total_granted.toLocaleString();
                document.getElementById('ana-total-used').innerText = json.summary.total_used.toLocaleString();
                document.getElementById('ana-avg-rate').innerText = json.summary.average_rate + '%';

                // Render department chart
                this.renderDepartmentChart(json.department_stats);

                // Render employee type chart
                this.renderTypeChart(json.type_stats);

                // Render top users
                this.renderTopUsers(json.top_users);

                // Render high balance
                this.renderHighBalance(json.high_balance);

                // Load predictions
                this.loadPredictions();

            } catch (e) {
                App.ui.showToast('error', '分析データの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        renderDepartmentChart(deptStats) {
            const ctx = document.getElementById('chart-department');
            if (!ctx) return;

            if (App.state.charts['department']) {
                App.state.charts['department'].destroy();
            }

            const data = deptStats.slice(0, 10);
            App.state.charts['department'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.map(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name),
                    datasets: [{
                        label: '使用日数',
                        data: data.map(d => d.total_used),
                        backgroundColor: 'rgba(56, 189, 248, 0.5)',
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { legend: { display: false } }
                }
            });
        },

        renderTypeChart(typeStats) {
            const ctx = document.getElementById('chart-emp-type');
            if (!ctx) return;

            if (App.state.charts['empType']) {
                App.state.charts['empType'].destroy();
            }

            App.state.charts['empType'] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(typeStats),
                    datasets: [{
                        data: Object.values(typeStats).map(v => v.used),
                        backgroundColor: ['#38bdf8', '#818cf8', '#34d399'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#94a3b8' } }
                    }
                }
            });
        },

        renderTopUsers(topUsers) {
            const container = document.getElementById('top-users-list');
            container.innerHTML = topUsers.map((u, i) => `
                <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="width: 30px; height: 30px; background: ${i < 3 ? 'var(--warning)' : 'rgba(255,255,255,0.1)'}; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 0.75rem; font-weight: 700; font-size: 0.8rem;">
                        ${i + 1}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${u.name}</div>
                        <div style="font-size: 0.8rem; color: var(--muted);">${u.employee_num}</div>
                    </div>
                    <div style="font-weight: 700; color: var(--success);">${u.used}日</div>
                </div>
            `).join('');
        },

        renderHighBalance(highBalance) {
            const container = document.getElementById('high-balance-list');
            container.innerHTML = highBalance.map(u => `
                <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600;">${u.name}</div>
                        <div style="font-size: 0.8rem; color: var(--muted);">${u.employee_num}</div>
                    </div>
                    <div style="font-weight: 700; color: var(--warning);">${u.balance}日</div>
                </div>
            `).join('');
        },

        async loadPredictions() {
            const year = App.state.year || new Date().getFullYear();

            try {
                const res = await fetch(`${App.config.apiBase}/analytics/predictions/${year}`);
                const json = await res.json();

                document.getElementById('pred-current-month').innerText = json.current_month + '月';
                document.getElementById('pred-remaining-months').innerText = json.remaining_months + 'ヶ月';
                document.getElementById('pred-avg-monthly').innerText = json.avg_monthly_usage + '日';
                document.getElementById('pred-at-risk').innerText = json.at_risk_count + '人';

                const container = document.getElementById('at-risk-employees');
                if (json.at_risk_employees && json.at_risk_employees.length > 0) {
                    container.innerHTML = json.at_risk_employees.map(e => `
                        <div style="display: flex; align-items: center; padding: 0.5rem; background: rgba(248, 113, 113, 0.1); border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid var(--danger);">
                            <div style="flex: 1;">
                                <div style="font-weight: 600;">${e.name}</div>
                                <div style="font-size: 0.8rem; color: var(--muted);">${e.employee_num}</div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.8rem; color: var(--muted);">現在 ${e.current_used}日</div>
                                <div style="font-weight: 700; color: var(--danger);">あと ${e.days_needed}日必要</div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div style="text-align: center; color: var(--success); padding: 1rem;">✅ 5日義務達成リスク者はいません</div>';
                }

            } catch (e) {
                console.error('Predictions error', e);
            }
        },

        async exportExcel(type) {
            const year = App.state.year || new Date().getFullYear();
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/export/excel?export_type=${type}&year=${year}`, {
                    method: 'POST'
                });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `${json.filename} をエクスポートしました`);
                }
            } catch (e) {
                App.ui.showToast('error', 'エクスポートに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        }
    },

    // ========================================
    // MONTHLY REPORTS MODULE
    // ========================================
    reports: {
        currentYear: new Date().getFullYear(),
        currentMonth: new Date().getMonth() + 1,
        mode: 'monthly',

        init() {
            // Initialize year selector
            const yearSelect = document.getElementById('report-year');
            const years = App.state.availableYears.length > 0 ? App.state.availableYears : [new Date().getFullYear()];
            yearSelect.innerHTML = years.map(y => `<option value="${y}" ${y === this.currentYear ? 'selected' : ''}>${y}年</option>`).join('');

            // Set current month
            document.getElementById('report-month').value = this.currentMonth;

            // Initialize custom date pickers with default range (last 30 days)
            const today = new Date();
            const thirtyDaysAgo = new Date(today);
            thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
            document.getElementById('report-start-date').value = thirtyDaysAgo.toISOString().split('T')[0];
            document.getElementById('report-end-date').value = today.toISOString().split('T')[0];

            // Load data
            this.loadMonthList();
            this.loadReport();
        },

        setMode(mode) {
            this.mode = mode;
            const monthlySelector = document.getElementById('monthly-selector');
            const customSelector = document.getElementById('custom-selector');
            const tabMonthly = document.getElementById('tab-monthly');
            const tabCustom = document.getElementById('tab-custom');

            // Update tab active states
            if (this.mode === 'monthly') {
                tabMonthly.classList.add('active');
                tabCustom.classList.remove('active');
                monthlySelector.style.display = 'flex';
                customSelector.style.display = 'none';
                this.loadReport();
            } else {
                tabMonthly.classList.remove('active');
                tabCustom.classList.add('active');
                monthlySelector.style.display = 'none';
                customSelector.style.display = 'block';
            }
        },

        async exportReport() {
            const data = this.mode === 'monthly'
                ? { year: this.currentYear, month: this.currentMonth }
                : {
                    startDate: document.getElementById('report-start-date').value,
                    endDate: document.getElementById('report-end-date').value
                };

            App.ui.showLoading();
            try {
                const params = this.mode === 'monthly'
                    ? `export_type=monthly_report&year=${data.year}&month=${data.month}`
                    : `export_type=custom_report&start_date=${data.startDate}&end_date=${data.endDate}`;

                const res = await fetch(`${App.config.apiBase}/export/excel?${params}`, { method: 'POST' });
                const json = await res.json();

                if (json.status === 'success') {
                    App.ui.showToast('success', `レポートをエクスポートしました: ${json.filename}`);
                    if (json.download_url) {
                        window.open(json.download_url, '_blank');
                    }
                } else {
                    throw new Error(json.detail || 'エクスポートに失敗しました');
                }
            } catch (e) {
                App.ui.showToast('error', e.message || 'エクスポートに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadCustomReport() {
            const startDate = document.getElementById('report-start-date').value;
            const endDate = document.getElementById('report-end-date').value;

            if (!startDate || !endDate) {
                App.ui.showToast('error', '開始日と終了日を選択してください');
                return;
            }

            if (endDate < startDate) {
                App.ui.showToast('error', '終了日は開始日より後を選択してください');
                return;
            }

            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/custom?start_date=${startDate}&end_date=${endDate}`);
                const json = await res.json();

                if (json.status !== 'success') {
                    throw new Error(json.detail || 'レポート取得に失敗しました');
                }

                // Update period display
                document.getElementById('report-period-label').innerText = json.report_period.label;

                // Update summary cards
                document.getElementById('rpt-emp-count').innerText = json.summary.total_employees + '人';
                document.getElementById('rpt-total-days').innerText = json.summary.total_days + '日';
                document.getElementById('rpt-total-hours').innerText = json.summary.total_hours + '時間';
                const avgDays = json.summary.total_employees > 0
                    ? (json.summary.total_days / json.summary.total_employees).toFixed(1)
                    : '0';
                document.getElementById('rpt-avg-days').innerText = avgDays + '日';

                // Render lists
                this.renderEmployeeList(json.employees);
                this.renderFactoryList(json.by_factory);
                this.renderDailyGrid(json.by_date);

                App.ui.showToast('success', `カスタムレポートを読み込みました (${json.report_period.days_in_period}日間)`);

            } catch (e) {
                App.ui.showToast('error', e.message || 'レポートの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        async loadMonthList() {
            this.currentYear = parseInt(document.getElementById('report-year').value);
            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/monthly-list/${this.currentYear}`);
                const json = await res.json();

                const tbody = document.getElementById('report-year-summary');
                if (json.reports && json.reports.length > 0) {
                    tbody.innerHTML = json.reports.map(r => `
                        <tr style="cursor: pointer;" onclick="App.reports.selectMonth(${r.month})">
                            <td style="font-weight: 600;">${r.label}</td>
                            <td style="font-size: 0.85rem; color: var(--muted);">${r.period}</td>
                            <td>${r.employee_count}人</td>
                            <td style="color: var(--primary); font-weight: 600;">${r.total_days}日</td>
                            <td><button class="btn btn-glass" style="padding: 0.25rem 0.75rem; font-size: 0.8rem;">詳細</button></td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 2rem;">データがありません</td></tr>';
                }

            } catch (e) {
                App.ui.showToast('error', '月次一覧の読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        selectMonth(month) {
            document.getElementById('report-month').value = month;
            this.loadReport();
        },

        async loadReport() {
            this.currentYear = parseInt(document.getElementById('report-year').value);
            this.currentMonth = parseInt(document.getElementById('report-month').value);

            App.ui.showLoading();

            try {
                const res = await fetch(`${App.config.apiBase}/reports/monthly/${this.currentYear}/${this.currentMonth}`);
                const json = await res.json();

                // Update period display
                document.getElementById('report-period-label').innerText = json.report_period.label;

                // Update summary cards
                document.getElementById('rpt-emp-count').innerText = json.summary.total_employees + '人';
                document.getElementById('rpt-total-days').innerText = json.summary.total_days + '日';
                document.getElementById('rpt-total-hours').innerText = json.summary.total_hours + '時間';
                const avgDays = json.summary.total_employees > 0
                    ? (json.summary.total_days / json.summary.total_employees).toFixed(1)
                    : '0';
                document.getElementById('rpt-avg-days').innerText = avgDays + '日';

                // Render employee list
                this.renderEmployeeList(json.employees);

                // Render factory list
                this.renderFactoryList(json.by_factory);

                // Render daily grid
                this.renderDailyGrid(json.by_date);

                App.ui.showToast('success', `${this.currentYear}年${this.currentMonth}月度レポートを読み込みました`);

            } catch (e) {
                App.ui.showToast('error', 'レポートの読み込みに失敗しました');
            } finally {
                App.ui.hideLoading();
            }
        },

        renderEmployeeList(employees) {
            const container = document.getElementById('report-employee-list');
            if (employees && employees.length > 0) {
                container.innerHTML = employees.map(emp => {
                    const datesHtml = emp.dates.map(d => {
                        const typeLabel = {'full': '全', 'half_am': '午前', 'half_pm': '午後', 'hourly': '時'}[d.type] || '';
                        return `<span class="badge badge-info" style="margin: 0.1rem; padding: 0.15rem 0.4rem; font-size: 0.65rem;">${d.date.slice(5)} ${typeLabel}</span>`;
                    }).join('');

                    return `
                        <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                            <div class="flex-between" style="margin-bottom: 0.5rem;">
                                <div>
                                    <div style="font-weight: 600;">${emp.name}</div>
                                    <div style="font-size: 0.8rem; color: var(--muted);">${emp.employee_num} | ${emp.factory || '-'}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">${emp.total_days}日</div>
                                    ${emp.total_hours > 0 ? `<div style="font-size: 0.8rem; color: var(--warning);">+${emp.total_hours}時間</div>` : ''}
                                </div>
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                                ${datesHtml}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">この期間の取得者はいません</div>';
            }
        },

        renderFactoryList(factories) {
            const container = document.getElementById('report-factory-list');
            if (factories && factories.length > 0) {
                container.innerHTML = factories.map(f => `
                    <div style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem;">
                        <div class="flex-between" style="margin-bottom: 0.5rem;">
                            <div style="font-weight: 600;">${f.factory}</div>
                            <div>
                                <span style="font-size: 0.9rem; color: var(--muted);">${f.employee_count}人</span>
                                <span style="font-size: 1.1rem; font-weight: 700; color: var(--primary); margin-left: 0.5rem;">${f.total_days}日</span>
                            </div>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--muted);">
                            ${f.employees.map(e => e.name).join(', ')}
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem;">データがありません</div>';
            }
        },

        renderDailyGrid(dailyData) {
            const container = document.getElementById('report-daily-grid');
            if (dailyData && dailyData.length > 0) {
                container.innerHTML = dailyData.map(d => {
                    const bgColor = d.count >= 5 ? 'rgba(248, 113, 113, 0.3)' :
                                   d.count >= 3 ? 'rgba(251, 191, 36, 0.3)' :
                                   'rgba(56, 189, 248, 0.15)';
                    return `
                        <div style="padding: 0.5rem; background: ${bgColor}; border-radius: 8px; text-align: center;" title="${d.employees.join(', ')}">
                            <div style="font-weight: 600; font-size: 0.9rem;">${d.date.slice(5)}</div>
                            <div style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">${d.count}</div>
                            <div style="font-size: 0.7rem; color: var(--muted);">人</div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = '<div style="text-align: center; color: var(--muted); padding: 2rem; grid-column: 1 / -1;">この期間のデータはありません</div>';
            }
        }
    },

    // ========================================
    // GSAP ANIMATIONS MODULE
    // ========================================
    animations: {
        init() {
            if (typeof gsap === 'undefined') {
                console.warn('GSAP not loaded, skipping animations');
                return;
            }

            // Register ScrollTrigger plugin
            if (typeof ScrollTrigger !== 'undefined') {
                gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);
            }

            // Animate stat cards on load
            gsap.from('.stat-card', {
                duration: 0.8,
                y: 30,
                opacity: 0,
                stagger: 0.1,
                ease: 'power3.out',
                delay: 0.2
            });

            // Animate glass panels on scroll
            gsap.utils.toArray('.glass-panel').forEach((panel, index) => {
                if (index > 3) { // Skip first 4 stat cards (already animated)
                    gsap.from(panel, {
                        scrollTrigger: {
                            trigger: panel,
                            start: 'top 90%',
                            end: 'top 70%',
                            toggleActions: 'play none none reverse'
                        },
                        duration: 0.6,
                        y: 40,
                        opacity: 0,
                        ease: 'power2.out'
                    });
                }
            });

            // Smooth scroll for anchor links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        gsap.to(window, {
                            duration: 1,
                            scrollTo: { y: target, offsetY: 20 },
                            ease: 'power3.inOut'
                        });
                    }
                });
            });

            // Animate sidebar navigation items
            gsap.from('.nav-item', {
                duration: 0.6,
                x: -30,
                opacity: 0,
                stagger: 0.08,
                ease: 'power2.out',
                delay: 0.3
            });

            // Animate logo
            gsap.from('.logo', {
                duration: 1,
                scale: 0.8,
                opacity: 0,
                ease: 'elastic.out(1, 0.5)'
            });

            // Parallax effect for background orbs
            if (window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
                gsap.to('body::before', {
                    scrollTrigger: {
                        scrub: true
                    },
                    y: (i, target) => -ScrollTrigger.maxScroll(window) * 0.3
                });
            }

            // Button hover animations
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('mouseenter', () => {
                    gsap.to(btn, {
                        duration: 0.3,
                        scale: 1.05,
                        ease: 'power2.out'
                    });
                });
                btn.addEventListener('mouseleave', () => {
                    gsap.to(btn, {
                        duration: 0.3,
                        scale: 1,
                        ease: 'power2.out'
                    });
                });
            });

            // Number counter animation for KPIs
            this.animateCounters();
        },

        animateCounters() {
            const counters = [
                { id: 'kpi-used', suffix: '' },
                { id: 'kpi-balance', suffix: '' },
                { id: 'kpi-rate', suffix: '%' },
                { id: 'kpi-total', suffix: '' }
            ];

            counters.forEach(({ id, suffix }) => {
                const element = document.getElementById(id);
                if (element && element.textContent !== '-') {
                    const value = parseFloat(element.textContent.replace(/[^\d.-]/g, ''));
                    if (!isNaN(value)) {
                        const obj = { val: 0 };
                        gsap.to(obj, {
                            val: value,
                            duration: 2,
                            ease: 'power2.out',
                            onUpdate: function() {
                                element.textContent = Math.round(obj.val).toLocaleString() + suffix;
                            }
                        });
                    }
                }
            });
        },

        // Animate view transitions
        transitionView(viewElement) {
            if (typeof gsap === 'undefined') return;

            gsap.from(viewElement, {
                duration: 0.5,
                opacity: 0,
                y: 20,
                ease: 'power2.out'
            });

            // Animate children with stagger
            const children = viewElement.querySelectorAll('.glass-panel, .stat-card');
            gsap.from(children, {
                duration: 0.6,
                y: 30,
                opacity: 0,
                stagger: 0.08,
                ease: 'power3.out',
                delay: 0.1
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();

    // Initialize GSAP animations after a short delay
    setTimeout(() => {
        if (App.animations) {
            App.animations.init();
        }
    }, 300);
});
