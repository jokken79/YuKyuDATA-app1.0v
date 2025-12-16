# 📚 Ejemplos Prácticos - Theme "The Best Jpkken"

> Ejemplos de código completos y listos para usar

---

## 📋 Índice de Ejemplos

1. [Página HTML Completa](#1-página-html-completa)
2. [Stat Cards](#2-stat-cards)
3. [Tabla de Datos](#3-tabla-de-datos)
4. [Formulario](#4-formulario)
5. [Gráficos Chart.js](#5-gráficos-chartjs)
6. [Gráficos ApexCharts](#6-gráficos-apexcharts)
7. [Modal/Dialog](#7-modal-dialog)
8. [Navigation Sidebar](#8-navigation-sidebar)
9. [Toast Notifications](#9-toast-notifications)
10. [Loading Spinner](#10-loading-spinner)
11. [Badges y Tags](#11-badges-y-tags)
12. [Tabs](#12-tabs)

---

## 1. Página HTML Completa

```html
<!DOCTYPE html>
<html lang="es" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>YuKyu Dashboard - Theme Arari</title>

  <!-- Fuentes Google -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+JP:wght@300;400;500;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Theme CSS -->
  <link rel="stylesheet" href="css/main.css">
  <link rel="stylesheet" href="css/arari-glow.css">
  <link rel="stylesheet" href="css/premium-enhancements.css">
</head>
<body>
  <div class="app-container">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="logo">
        <img src="icons/logo-premium.svg" alt="YuKyu Logo" style="width: 42px; height: 42px;">
        <span class="text-gradient" style="font-size: 1.5rem; font-weight: 800;">YuKyu</span>
      </div>

      <nav style="margin-top: 2rem; flex: 1;">
        <div class="nav-item active">
          <span>📊</span>
          <span>Dashboard</span>
        </div>
        <div class="nav-item">
          <span>👥</span>
          <span>Empleados</span>
        </div>
        <div class="nav-item">
          <span>📅</span>
          <span>Calendario</span>
        </div>
        <div class="nav-item">
          <span>📈</span>
          <span>Reportes</span>
        </div>
        <div class="nav-item">
          <span>⚙️</span>
          <span>Configuración</span>
        </div>
      </nav>

      <!-- Theme Toggle -->
      <div class="theme-toggle" onclick="toggleTheme()" style="margin-top: auto;">
        <span id="theme-label" style="font-size: 0.85rem; color: var(--text-secondary);">Dark</span>
        <div class="theme-toggle-track">
          <div class="theme-toggle-thumb">
            <span id="theme-icon">🌙</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="flex-between" style="margin-bottom: 2rem; position: relative;">
        <h1 class="text-gradient" style="font-size: 2.5rem; font-weight: 800; margin: 0;">
          Dashboard 有給休暇
        </h1>
        <div class="flex-center" style="gap: 1rem;">
          <button class="btn btn-glass">
            <span>🔄</span>
            <span>Sync</span>
          </button>
          <button class="btn btn-primary">
            <span>📥</span>
            <span>Exportar</span>
          </button>
        </div>
      </header>

      <!-- Bento Grid - Stats -->
      <div class="bento-grid" style="margin-bottom: 2rem;">
        <div class="glass-panel stat-card col-span-1">
          <div class="stat-label">Total Empleados</div>
          <div class="stat-value">156</div>
          <div style="font-size: 0.8rem; color: var(--success); margin-top: 0.5rem;">
            ↑ 12% vs mes anterior
          </div>
        </div>

        <div class="glass-panel stat-card col-span-1">
          <div class="stat-label">Promedio Uso</div>
          <div class="stat-value">72.5%</div>
          <div style="font-size: 0.8rem; color: var(--warning); margin-top: 0.5rem;">
            → 0.3% vs mes anterior
          </div>
        </div>

        <div class="glass-panel stat-card col-span-1">
          <div class="stat-label">Días Otorgados</div>
          <div class="stat-value">1,248</div>
        </div>

        <div class="glass-panel stat-card col-span-1">
          <div class="stat-label">Días Usados</div>
          <div class="stat-value">904</div>
        </div>
      </div>

      <!-- Chart Area -->
      <div class="bento-grid">
        <div class="glass-panel col-span-2" style="padding: 1.5rem;">
          <h3 style="margin-bottom: 1rem; font-weight: 600;">Distribución de Uso</h3>
          <canvas id="usageChart" style="max-height: 300px;"></canvas>
        </div>

        <div class="glass-panel col-span-2" style="padding: 1.5rem;">
          <h3 style="margin-bottom: 1rem; font-weight: 600;">Top 10 Usuarios</h3>
          <canvas id="top10Chart" style="max-height: 300px;"></canvas>
        </div>
      </div>
    </main>
  </div>

  <!-- Scripts -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="js/chart-colors.js"></script>
  <script>
    // Theme Toggle
    function toggleTheme() {
      const html = document.documentElement;
      const current = html.getAttribute('data-theme');
      const newTheme = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);

      document.getElementById('theme-label').textContent = newTheme === 'dark' ? 'Dark' : 'Light';
      document.getElementById('theme-icon').textContent = newTheme === 'dark' ? '🌙' : '☀️';
    }

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
  </script>
</body>
</html>
```

---

## 2. Stat Cards

```html
<!-- Stat Card Básica -->
<div class="glass-panel stat-card col-span-1">
  <div class="stat-label">Total Empleados</div>
  <div class="stat-value">156</div>
</div>

<!-- Stat Card con Badge -->
<div class="glass-panel stat-card col-span-1">
  <div class="flex-between" style="margin-bottom: 0.5rem;">
    <div class="stat-label">Días Críticos</div>
    <span class="badge badge-critical">Alerta</span>
  </div>
  <div class="stat-value">23</div>
</div>

<!-- Stat Card con Cambio Porcentual -->
<div class="glass-panel stat-card col-span-1">
  <div class="stat-label">Promedio Uso</div>
  <div class="stat-value">72.5%</div>
  <div style="font-size: 0.85rem; color: var(--success); margin-top: 0.5rem; display: flex; align-items: center; gap: 0.25rem;">
    <span>↑</span>
    <span>5.2% vs mes anterior</span>
  </div>
</div>

<!-- Stat Card con Progress Bar -->
<div class="glass-panel stat-card col-span-1">
  <div class="stat-label">Cumplimiento</div>
  <div class="stat-value">87%</div>
  <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 10px; margin-top: 1rem; overflow: hidden;">
    <div style="width: 87%; height: 100%; background: linear-gradient(90deg, var(--success), var(--primary)); border-radius: 10px;"></div>
  </div>
</div>
```

---

## 3. Tabla de Datos

```html
<div class="glass-panel" style="padding: 1.5rem;">
  <div class="flex-between" style="margin-bottom: 1.5rem;">
    <h3 style="font-weight: 600;">Empleados</h3>
    <input type="text" class="input-glass" placeholder="🔍 Buscar..." style="width: 300px;">
  </div>

  <table class="modern-table">
    <thead>
      <tr>
        <th>ID</th>
        <th>Nombre</th>
        <th>派遣先</th>
        <th>Otorgados</th>
        <th>Usados</th>
        <th>Balance</th>
        <th>Uso %</th>
        <th>Estado</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span style="font-family: var(--font-mono); color: var(--text-muted);">E001</span></td>
        <td><strong>田中 太郎</strong></td>
        <td>高雄工業 熊本</td>
        <td>10.0</td>
        <td>8.5</td>
        <td>1.5</td>
        <td><span class="text-gradient" style="font-weight: 700;">85.0%</span></td>
        <td><span class="badge badge-warning">Alto</span></td>
      </tr>
      <tr>
        <td><span style="font-family: var(--font-mono); color: var(--text-muted);">E002</span></td>
        <td><strong>佐藤 花子</strong></td>
        <td>高雄工業 熊本</td>
        <td>10.0</td>
        <td>3.0</td>
        <td>7.0</td>
        <td><span style="font-weight: 700;">30.0%</span></td>
        <td><span class="badge badge-success">Bajo</span></td>
      </tr>
      <tr>
        <td><span style="font-family: var(--font-mono); color: var(--text-muted);">E003</span></td>
        <td><strong>鈴木 一郎</strong></td>
        <td>高雄工業 熊本</td>
        <td>10.0</td>
        <td>9.5</td>
        <td>0.5</td>
        <td><span class="text-gradient" style="font-weight: 700;">95.0%</span></td>
        <td><span class="badge badge-critical">Crítico</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 4. Formulario

```html
<div class="glass-panel" style="padding: 2rem;">
  <h2 style="margin-bottom: 1.5rem; font-weight: 700;">Solicitar Vacaciones</h2>

  <form id="vacation-form">
    <!-- Sección 1 -->
    <div class="form-section">
      <div class="form-section-title">📋 Información del Empleado</div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label class="required">Empleado ID</label>
          <input type="text" class="input-glass" placeholder="E001" required>
        </div>

        <div class="form-group">
          <label class="required">Nombre</label>
          <input type="text" class="input-glass" placeholder="田中 太郎" required>
        </div>
      </div>
    </div>

    <!-- Sección 2 -->
    <div class="form-section">
      <div class="form-section-title">📅 Detalles de la Solicitud</div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
        <div class="form-group">
          <label class="required">Fecha Inicio</label>
          <input type="date" class="input-glass" required>
        </div>

        <div class="form-group">
          <label class="required">Fecha Fin</label>
          <input type="date" class="input-glass" required>
        </div>
      </div>

      <div class="form-group">
        <label>Tipo de Vacación</label>
        <select class="input-glass">
          <option>Día completo</option>
          <option>Medio día (AM)</option>
          <option>Medio día (PM)</option>
          <option>Horas</option>
        </select>
      </div>

      <div class="form-group">
        <label>Motivo</label>
        <textarea class="input-glass" rows="3" placeholder="Opcional..."></textarea>
        <div class="char-counter">0 / 200</div>
      </div>
    </div>

    <!-- Botones -->
    <div class="flex-between" style="margin-top: 1.5rem;">
      <button type="button" class="btn btn-glass">
        <span>✕</span>
        <span>Cancelar</span>
      </button>
      <button type="submit" class="btn btn-primary">
        <span>✓</span>
        <span>Enviar Solicitud</span>
      </button>
    </div>
  </form>
</div>
```

---

## 5. Gráficos Chart.js

```html
<div class="glass-panel" style="padding: 1.5rem;">
  <h3 style="margin-bottom: 1rem;">Top 10 Usuarios</h3>
  <canvas id="top10Chart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="js/chart-colors.js"></script>
<script>
const ctx = document.getElementById('top10Chart').getContext('2d');

new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['田中', '佐藤', '鈴木', '高橋', '伊藤', '渡辺', '山本', '中村', '小林', '加藤'],
    datasets: [{
      label: 'Días Usados',
      data: [9.5, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0, 4.5],
      backgroundColor: ChartColors.rgba.warning70,
      borderColor: ChartColors.primary.warning,
      borderWidth: 2,
      borderRadius: 6,
    }]
  },
  options: {
    ...ChartColors.chartJsDefaults,
    indexAxis: 'y',
    scales: {
      x: {
        grid: { color: ChartColors.rgba.white05 },
        ticks: { color: '#94a3b8' }
      },
      y: {
        grid: { display: false },
        ticks: { color: '#94a3b8' }
      }
    }
  }
});
</script>
```

---

## 6. Gráficos ApexCharts

```html
<div class="glass-panel" style="padding: 1.5rem;">
  <h3 style="margin-bottom: 1rem;">Tendencias Mensuales</h3>
  <div id="trendsChart"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
<script src="js/chart-colors.js"></script>
<script>
const options = {
  ...ChartColors.apexDefaults,
  series: [{
    name: 'Uso Mensual',
    data: [30, 40, 35, 50, 49, 60, 70, 91, 65, 55, 45, 72]
  }],
  chart: {
    type: 'area',
    height: 350,
    background: 'transparent',
    toolbar: { show: false }
  },
  colors: [ChartColors.primary.cyan],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.7,
      opacityTo: 0.2,
      stops: [0, 90, 100],
      gradientToColors: [ChartColors.primary.purple]
    }
  },
  stroke: {
    curve: 'smooth',
    width: 3
  },
  xaxis: {
    categories: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
  },
  yaxis: {
    title: { text: 'Días Usados' }
  }
};

const chart = new ApexCharts(document.querySelector("#trendsChart"), options);
chart.render();
</script>
```

---

## 7. Modal/Dialog

```html
<!-- Modal Overlay -->
<div class="loader-overlay" id="detailModal" style="display: none;">
  <div class="glass-panel" style="width: 90%; max-width: 600px; padding: 2rem; position: relative;">
    <!-- Close Button -->
    <button onclick="closeModal()" style="position: absolute; top: 1rem; right: 1rem; background: none; border: none; font-size: 1.5rem; cursor: pointer; color: var(--text-muted);">
      ✕
    </button>

    <!-- Modal Header -->
    <h2 style="margin-bottom: 1.5rem; font-weight: 700;">
      Detalles del Empleado
    </h2>

    <!-- Modal Content -->
    <div style="background: rgba(255,255,255,0.03); border-radius: 12px; padding: 1.25rem; margin-bottom: 1.5rem;">
      <div class="flex-between" style="padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
        <span style="color: var(--text-muted);">ID:</span>
        <strong>E001</strong>
      </div>
      <div class="flex-between" style="padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
        <span style="color: var(--text-muted);">Nombre:</span>
        <strong>田中 太郎</strong>
      </div>
      <div class="flex-between" style="padding: 0.75rem 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
        <span style="color: var(--text-muted);">派遣先:</span>
        <strong>高雄工業 熊本</strong>
      </div>
      <div class="flex-between" style="padding: 0.75rem 0;">
        <span style="color: var(--text-muted);">Uso:</span>
        <strong class="text-gradient">85.0%</strong>
      </div>
    </div>

    <!-- Modal Actions -->
    <div class="flex-between">
      <button onclick="closeModal()" class="btn btn-glass">Cerrar</button>
      <button class="btn btn-primary">Editar</button>
    </div>
  </div>
</div>

<script>
function openModal() {
  document.getElementById('detailModal').style.display = 'flex';
  setTimeout(() => {
    document.getElementById('detailModal').classList.add('active');
  }, 10);
}

function closeModal() {
  document.getElementById('detailModal').classList.remove('active');
  setTimeout(() => {
    document.getElementById('detailModal').style.display = 'none';
  }, 300);
}
</script>
```

---

## 8. Navigation Sidebar

```html
<aside class="sidebar">
  <!-- Logo -->
  <div class="logo">
    <img src="icons/logo-premium.svg" alt="Logo" style="width: 42px; height: 42px;">
    <span class="text-gradient" style="font-size: 1.5rem; font-weight: 800;">YuKyu</span>
  </div>

  <!-- Navigation -->
  <nav style="margin-top: 2rem; flex: 1;">
    <div class="nav-item active">
      <span>📊</span>
      <span>Dashboard</span>
    </div>
    <div class="nav-item">
      <span>👥</span>
      <span>Empleados</span>
    </div>
    <div class="nav-item">
      <span>📅</span>
      <span>Calendario</span>
    </div>
    <div class="nav-item">
      <span>📈</span>
      <span>Analytics</span>
    </div>
    <div class="nav-item">
      <span>📋</span>
      <span>Solicitudes</span>
    </div>
    <div class="nav-item">
      <span>⚙️</span>
      <span>Configuración</span>
    </div>
  </nav>

  <!-- User Profile -->
  <div style="padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 12px; margin-top: auto;">
    <div class="flex-between">
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--secondary)); display: flex; align-items: center; justify-content: center; font-weight: 700;">
          JK
        </div>
        <div>
          <div style="font-weight: 600; font-size: 0.9rem;">Jokken79</div>
          <div style="font-size: 0.75rem; color: var(--text-muted);">Admin</div>
        </div>
      </div>
      <button style="background: none; border: none; cursor: pointer; color: var(--text-muted);">⋮</button>
    </div>
  </div>

  <!-- Theme Toggle -->
  <div class="theme-toggle" onclick="toggleTheme()" style="margin-top: 1rem;">
    <span id="theme-label" style="font-size: 0.85rem;">Dark</span>
    <div class="theme-toggle-track">
      <div class="theme-toggle-thumb">
        <span id="theme-icon">🌙</span>
      </div>
    </div>
  </div>
</aside>
```

---

## 9. Toast Notifications

```html
<!-- Toast Container -->
<div class="toast-container" id="toast-container"></div>

<script>
function showToast(type, message) {
  const container = document.getElementById('toast-container');

  const toast = document.createElement('div');
  toast.className = 'toast';

  const icon = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }[type] || 'ℹ';

  const color = {
    success: 'var(--success)',
    error: 'var(--danger)',
    warning: 'var(--warning)',
    info: 'var(--primary)'
  }[type] || 'var(--primary)';

  toast.innerHTML = `
    <div style="width: 32px; height: 32px; border-radius: 50%; background: ${color}; display: flex; align-items: center; justify-content: center; font-weight: 700;">
      ${icon}
    </div>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => {
    toast.style.animation = 'slideInLeft 0.3s reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Ejemplos de uso:
// showToast('success', 'Datos sincronizados correctamente');
// showToast('error', 'Error al cargar los datos');
// showToast('warning', 'Acción no permitida');
// showToast('info', 'Información actualizada');
</script>
```

---

## 10. Loading Spinner

```html
<!-- Loading Overlay -->
<div class="loader-overlay" id="loader">
  <div class="spinner"></div>
  <div style="margin-top: 2rem; color: var(--text-muted); font-size: 0.9rem;">
    Cargando datos...
  </div>
</div>

<script>
function showLoading() {
  const loader = document.getElementById('loader');
  loader.style.display = 'flex';
  setTimeout(() => loader.classList.add('active'), 10);
}

function hideLoading() {
  const loader = document.getElementById('loader');
  loader.classList.remove('active');
  setTimeout(() => loader.style.display = 'none', 400);
}

// Ejemplo de uso:
// showLoading();
// fetch('/api/data').then(() => hideLoading());
</script>
```

---

## 11. Badges y Tags

```html
<!-- Success Badge -->
<span class="badge badge-success">Bajo</span>

<!-- Warning Badge -->
<span class="badge badge-warning">Alto</span>

<!-- Danger Badge -->
<span class="badge badge-danger">Crítico</span>

<!-- Critical Badge (pulsante) -->
<span class="badge badge-critical">Urgente</span>

<!-- Info Badge -->
<span class="badge badge-info">Información</span>

<!-- Badge con ícono -->
<span class="badge badge-success" style="display: inline-flex; align-items: center; gap: 0.35rem;">
  <span>✓</span>
  <span>Aprobado</span>
</span>
```

---

## 12. Tabs

```html
<!-- Tab Container -->
<div class="tab-container">
  <button class="tab-btn active" onclick="switchTab('dashboard')">
    <span>📊</span>
    <span>Dashboard</span>
  </button>
  <button class="tab-btn" onclick="switchTab('calendar')">
    <span>📅</span>
    <span>Calendario</span>
  </button>
  <button class="tab-btn" onclick="switchTab('reports')">
    <span>📈</span>
    <span>Reportes</span>
  </button>
</div>

<!-- Tab Content -->
<div class="tab-content active" id="tab-dashboard">
  <div class="glass-panel" style="padding: 2rem; margin-top: 1.5rem;">
    <h3>Dashboard Content</h3>
  </div>
</div>

<div class="tab-content" id="tab-calendar" style="display: none;">
  <div class="glass-panel" style="padding: 2rem; margin-top: 1.5rem;">
    <h3>Calendar Content</h3>
  </div>
</div>

<div class="tab-content" id="tab-reports" style="display: none;">
  <div class="glass-panel" style="padding: 2rem; margin-top: 1.5rem;">
    <h3>Reports Content</h3>
  </div>
</div>

<script>
function switchTab(tabName) {
  // Remove active from all tabs
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => {
    content.style.display = 'none';
    content.classList.remove('active');
  });

  // Add active to clicked tab
  event.target.closest('.tab-btn').classList.add('active');
  const content = document.getElementById(`tab-${tabName}`);
  content.style.display = 'block';
  setTimeout(() => content.classList.add('active'), 10);
}
</script>
```

---

## 🎯 Tips de Implementación

### 1. Animaciones Staggered Dinámicas

```javascript
// Animar elementos dinámicamente
function animateCards(selector) {
  const cards = document.querySelectorAll(selector);
  cards.forEach((card, index) => {
    card.style.animation = `fadeInUp 0.6s ease-out ${index * 0.1}s both`;
  });
}

// Uso:
animateCards('.stat-card');
```

### 2. Validación de Formularios con Feedback Visual

```javascript
function validateInput(input) {
  const value = input.value.trim();

  if (value === '') {
    input.classList.add('is-invalid');
    input.classList.remove('is-valid');
    return false;
  } else {
    input.classList.add('is-valid');
    input.classList.remove('is-invalid');
    return true;
  }
}

// Uso:
document.querySelectorAll('input[required]').forEach(input => {
  input.addEventListener('blur', () => validateInput(input));
});
```

### 3. Skeleton Loading

```html
<div class="glass-panel" style="padding: 1.5rem;">
  <div class="skeleton skeleton-text"></div>
  <div class="skeleton skeleton-text short"></div>
  <div class="skeleton skeleton-text medium"></div>
</div>
```

---

**¡Estos ejemplos están listos para copiar y pegar! 🚀**
