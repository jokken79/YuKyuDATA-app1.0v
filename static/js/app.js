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
                'factories': 'Factory Analytics',
                'requests': '有給休暇申請',
                'compliance': 'Compliance & Reports',
                'settings': 'System Settings'
            };
            document.getElementById('page-title').innerText = titleMap[viewName] || 'Dashboard';

            App.state.currentView = viewName;

            // Re-render charts if switching to factory view to ensure size correctness
            if (viewName === 'factories') {
                setTimeout(() => App.charts.renderFactoryChart(), 100);
            }

            // Load data for specific views
            if (viewName === 'requests') {
                App.requests.loadPending();
                App.requests.loadHistory();
            }

            if (viewName === 'compliance') {
                App.compliance.loadAlerts();
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
    },

    // ========================================
    // REQUESTS MODULE (申請)
    // ========================================
    requests: {
        selectedEmployee: null,
        searchTimeout: null,

        async searchEmployee(query) {
            if (this.searchTimeout) clearTimeout(this.searchTimeout);

            if (!query || query.length < 2) {
                document.getElementById('emp-search-results').innerHTML = '';
                return;
            }

            this.searchTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`${App.config.apiBase}/employees/search?q=${encodeURIComponent(query)}&status=在職中`);
                    const json = await res.json();

                    const container = document.getElementById('emp-search-results');
                    if (json.data && json.data.length > 0) {
                        container.innerHTML = json.data.slice(0, 10).map(emp => `
                            <div class="search-result-item" onclick="App.requests.selectEmployee('${emp.employee_num}')"
                                 style="padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s;">
                                <div style="font-weight: 600;">${emp.name}</div>
                                <div style="font-size: 0.85rem; color: var(--muted);">${emp.employee_num} | ${emp.factory || '-'} | ${emp.type}</div>
                            </div>
                        `).join('');
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

                    // Clear search
                    document.getElementById('emp-search').value = json.employee.name;
                    document.getElementById('emp-search-results').innerHTML = '';
                }
            } catch (e) {
                App.ui.showToast('error', 'Failed to load employee info');
            }
        },

        async submit() {
            if (!this.selectedEmployee) {
                App.ui.showToast('error', '従業員を選択してください');
                return;
            }

            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            const daysRequested = parseFloat(document.getElementById('days-requested').value);
            const reason = document.getElementById('leave-reason').value;

            if (!startDate || !endDate) {
                App.ui.showToast('error', '日付を入力してください');
                return;
            }

            if (daysRequested > this.selectedEmployee.total_available) {
                App.ui.showToast('error', `残日数が不足しています (残り: ${this.selectedEmployee.total_available}日)`);
                return;
            }

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
                        reason: reason
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Request failed');
                }

                App.ui.showToast('success', '申請が送信されました');
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
            document.getElementById('emp-search').value = '';
            document.getElementById('selected-emp-info').style.display = 'none';
            document.getElementById('start-date').value = '';
            document.getElementById('end-date').value = '';
            document.getElementById('days-requested').value = '1';
            document.getElementById('leave-reason').value = '';
        },

        async loadPending() {
            try {
                const res = await fetch(`${App.config.apiBase}/leave-requests?status=PENDING`);
                const json = await res.json();

                const container = document.getElementById('pending-requests');
                if (json.data && json.data.length > 0) {
                    container.innerHTML = json.data.map(req => `
                        <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 0.75rem;">
                            <div class="flex-between">
                                <div>
                                    <div style="font-weight: 600;">${req.employee_name}</div>
                                    <div style="font-size: 0.85rem; color: var(--muted);">${req.start_date} 〜 ${req.end_date} (${req.days_requested}日)</div>
                                    <div style="font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem;">${req.reason || '-'}</div>
                                </div>
                                <div style="display: flex; gap: 0.5rem;">
                                    <button class="btn btn-glass" style="background: rgba(52, 211, 153, 0.2); padding: 0.5rem 1rem;"
                                        onclick="App.requests.approve(${req.id})">✓ 承認</button>
                                    <button class="btn btn-glass" style="background: rgba(248, 113, 113, 0.2); padding: 0.5rem 1rem;"
                                        onclick="App.requests.reject(${req.id})">✗ 却下</button>
                                </div>
                            </div>
                        </div>
                    `).join('');
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
                        return `
                            <tr>
                                <td>${req.id}</td>
                                <td>${req.employee_name}</td>
                                <td>${req.start_date} 〜 ${req.end_date}</td>
                                <td>${req.days_requested}日</td>
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
    }
};

document.addEventListener('DOMContentLoaded', () => App.init());
