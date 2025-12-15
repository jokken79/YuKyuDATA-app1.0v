/**
 * YuKyu Dashboard v5.2 - Fixed Logic
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

    async init() {
        console.log('🚀 Initializing YuKyu Premium Dashboard...');
        this.ui.showLoading();

        // Initial Fetch
        await this.data.fetchEmployees();

        this.ui.hideLoading();
        this.events.setupListeners();
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
                setTimeout(() => target.classList.add('active'), 10); // Trigger animation
            }

            // Update Sidebar
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            const activeNav = document.querySelector(`.nav-item[data-view="${viewName}"]`);
            if (activeNav) activeNav.classList.add('active');

            // Update Header
            const titleMap = {
                'dashboard': 'Dashboard Overview',
                'employees': 'Employee Directory',
                'factories': 'Factory Analytics'
            };
            document.getElementById('page-title').innerText = titleMap[viewName] || 'Dashboard';

            App.state.currentView = viewName;

            // Re-render charts if switching to factory view to ensure size correctness
            if (viewName === 'factories') {
                setTimeout(() => App.charts.renderFactoryChart(), 100);
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

            tbody.innerHTML = data.map(e => `
                <tr onclick="App.ui.openModal('${e.employeeNum}')" style="cursor: pointer;">
                    <td><div class="font-bold">${e.employeeNum}</div></td>
                    <td><div class="font-bold text-white">${e.name}</div></td>
                    <td><div class="text-sm text-gray-400">${e.haken || '-'}</div></td>
                    <td>${e.granted.toFixed(1)}</td>
                    <td><span class="text-gradient">${e.used.toFixed(1)}</span></td>
                    <td><span class="badge ${e.balance < 5 ? 'badge-danger' : 'badge-success'}">${e.balance.toFixed(1)}</span></td>
                    <td>
                        <div style="width: 100px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden;">
                            <div style="width: ${Math.min(e.usageRate, 100)}%; height: 100%; background: var(--primary);"></div>
                        </div>
                        <div class="text-xs mt-1 text-right">${e.usageRate}%</div>
                    </td>
                </tr>
            `).join('');
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
            const ctx = document.getElementById('chart-distribution').getContext('2d');
            this.destroy('distribution');

            const data = App.data.getFiltered();
            const ranges = [0, 0, 0, 0]; // 0-25, 26-50, 51-75, 76-100

            data.forEach(e => {
                if (e.usageRate <= 25) ranges[0]++;
                else if (e.usageRate <= 50) ranges[1]++;
                else if (e.usageRate <= 75) ranges[2]++;
                else ranges[3]++;
            });

            App.state.charts['distribution'] = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['0-25%', '26-50%', '51-75%', '76-100%'],
                    datasets: [{
                        data: ranges,
                        backgroundColor: ['#f87171', '#fbbf24', '#38bdf8', '#34d399'],
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

        async renderTrends() {
            const ctx = document.getElementById('chart-trends');
            if (!ctx) return;
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

            App.state.charts['trends'] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    datasets: [{
                        label: 'Days Used',
                        data: trendsData,
                        borderColor: '#818cf8',
                        backgroundColor: 'rgba(129, 140, 248, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        },

        renderFactoryChart() {
            const ctx = document.getElementById('chart-factories');
            if (!ctx) return;

            this.destroy('factories');
            const stats = App.data.getFactoryStats().slice(0, 10); // Top 10

            App.state.charts['factories'] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: stats.map(s => s[0]),
                    datasets: [{
                        label: 'Days Used',
                        data: stats.map(s => s[1]),
                        backgroundColor: 'rgba(56, 189, 248, 0.5)',
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    },

    events: {
        setupListeners() {
            // Close modal when clicking outside
            document.getElementById('detail-modal').addEventListener('click', (e) => {
                if (e.target.id === 'detail-modal') App.ui.closeModal();
            });
        }
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
