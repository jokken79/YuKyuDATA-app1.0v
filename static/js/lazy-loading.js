/**
 * Lazy Loading Implementation
 * Carga perezosa de imágenes, componentes y scripts
 */

// ============================================
// 1. IMAGE LAZY LOADING
// ============================================

class LazyImageLoader {
  constructor(options = {}) {
    this.options = {
      threshold: 0.1,
      rootMargin: '50px',
      ...options
    };
    this.init();
  }

  init() {
    // Usar IntersectionObserver para lazy loading
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver(
        (entries, observer) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target;
              img.src = img.dataset.src;
              img.classList.add('loaded');
              observer.unobserve(img);
            }
          });
        },
        this.options
      );

      // Observar todas las imágenes con data-src
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    } else {
      // Fallback para navegadores sin IntersectionObserver
      this.loadAllImages();
    }
  }

  loadAllImages() {
    document.querySelectorAll('img[data-src]').forEach(img => {
      img.src = img.dataset.src;
    });
  }
}

// ============================================
// 2. COMPONENT LAZY LOADING
// ============================================

class LazyComponentLoader {
  static async loadComponent(selector, modulePath) {
    const container = document.querySelector(selector);
    if (!container) return;

    // Usar IntersectionObserver para cargar cuando sea visible
    const observer = new IntersectionObserver(
      async (entries) => {
        if (entries[0].isIntersecting) {
          try {
            const module = await import(modulePath);
            if (module.default) {
              module.default(container);
            }
            observer.unobserve(container);
          } catch (error) {
            console.error(`Error cargando componente ${modulePath}:`, error);
          }
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(container);
  }

  static async loadMultiple(components) {
    return Promise.all(
      components.map(({ selector, path }) => 
        this.loadComponent(selector, path)
      )
    );
  }
}

// ============================================
// 3. SCRIPT LAZY LOADING
// ============================================

class LazyScriptLoader {
  static loadScript(src, options = {}) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.async = options.async !== false;
      script.defer = options.defer !== false;

      script.onload = () => resolve(script);
      script.onerror = () => reject(new Error(`Script ${src} failed to load`));

      document.body.appendChild(script);
    });
  }

  static loadStylesheet(href) {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;

      link.onload = () => resolve(link);
      link.onerror = () => reject(new Error(`Stylesheet ${href} failed to load`));

      document.head.appendChild(link);
    });
  }
}

// ============================================
// 4. CHART LAZY LOADING
// ============================================

class LazyChartLoader {
  static async loadChart(containerId, chartOptions) {
    return new Promise((resolve) => {
      const container = document.getElementById(containerId);
      if (!container) return;

      const observer = new IntersectionObserver(
        async (entries) => {
          if (entries[0].isIntersecting) {
            try {
              // Cargar ApexCharts o Chart.js cuando sea visible
              await LazyScriptLoader.loadScript(
                'https://cdn.jsdelivr.net/npm/apexcharts@latest/dist/apexcharts.min.js'
              );
              
              // Inicializar gráfico
              if (window.ApexCharts) {
                const chart = new ApexCharts(container, chartOptions);
                chart.render();
                resolve(chart);
              }
            } catch (error) {
              console.error('Error cargando gráfico:', error);
            }
            observer.unobserve(container);
          }
        },
        { threshold: 0.1 }
      );

      observer.observe(container);
    });
  }
}

// ============================================
// 5. NETWORK INFORMATION API
// ============================================

class AdaptiveLoading {
  static shouldLoadHeavyAssets() {
    if ('connection' in navigator) {
      const connection = navigator.connection;
      
      // No cargar assets pesados en conexiones lentas
      return (
        connection.effectiveType !== '4g' &&
        connection.effectiveType !== '3g'
      );
    }
    return true;
  }

  static shouldLoadImages() {
    if ('connection' in navigator) {
      const connection = navigator.connection;
      return connection.effectiveType !== 'slow-2g';
    }
    return true;
  }

  static getSaveDataMode() {
    return (navigator.connection && navigator.connection.saveData) || false;
  }
}

// ============================================
// INICIALIZACIÓN
// ============================================

// Esperar a que DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
  // Lazy load imágenes
  new LazyImageLoader({
    threshold: 0.1,
    rootMargin: '100px'
  });

  // Lazy load componentes específicos
  LazyComponentLoader.loadMultiple([
    {
      selector: '#analytics-section',
      path: './components/analytics.js'
    },
    {
      selector: '#reports-section',
      path: './components/reports.js'
    }
  ]);
});

// Exportar para uso en otros módulos
export { LazyImageLoader, LazyComponentLoader, LazyScriptLoader, LazyChartLoader, AdaptiveLoading };
