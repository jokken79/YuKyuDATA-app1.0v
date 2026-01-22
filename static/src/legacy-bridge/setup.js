/**
 * Legacy Bridge: Setup & Configuration
 *
 * Pre-configuración del bridge con componentes comunes
 * Importar este archivo para inicializar el bridge completamente
 *
 * Usage:
 *   import { setupBridgeWithDefaults } from '/static/src/legacy-bridge/setup.js';
 *   await setupBridgeWithDefaults();
 */

import { getUnifiedBridge } from './unified-bridge.js';

/**
 * Registro de componentes por categoría
 * Aquí van todos los componentes que pueden ser registrados
 */
const COMPONENT_REGISTRY = {
    // Componentes core
    core: {
        Alert: {
            module: () => import('/static/src/components/Alert.js'),
            metadata: {
                category: 'core',
                props: ['type', 'message', 'onClose'],
                description: 'Alert notification component'
            }
        },
        Modal: {
            module: () => import('/static/src/components/Modal.js'),
            metadata: {
                category: 'core',
                props: ['title', 'isOpen', 'onClose', 'children'],
                description: 'Modal dialog component'
            }
        },
        Button: {
            module: () => import('/static/src/components/Button.js'),
            metadata: {
                category: 'core',
                props: ['onClick', 'variant', 'disabled', 'children'],
                description: 'Button component'
            }
        },
    },

    // Componentes de formulario
    form: {
        Form: {
            module: () => import('/static/src/components/Form.js'),
            metadata: {
                category: 'form',
                props: ['onSubmit', 'children'],
                description: 'Form wrapper component'
            }
        },
        Input: {
            module: () => import('/static/src/components/Input.js'),
            metadata: {
                category: 'form',
                props: ['name', 'value', 'onChange', 'placeholder', 'type'],
                description: 'Text input component'
            }
        },
        Select: {
            module: () => import('/static/src/components/Select.js'),
            metadata: {
                category: 'form',
                props: ['name', 'value', 'onChange', 'options'],
                description: 'Select dropdown component'
            }
        },
        DatePicker: {
            module: () => import('/static/src/components/DatePicker.js'),
            metadata: {
                category: 'form',
                props: ['value', 'onChange', 'placeholder'],
                description: 'Date picker component'
            }
        },
    },

    // Componentes de datos
    data: {
        Table: {
            module: () => import('/static/src/components/Table.js'),
            metadata: {
                category: 'data',
                props: ['columns', 'data', 'onRowClick'],
                description: 'Data table component'
            }
        },
        Card: {
            module: () => import('/static/src/components/Card.js'),
            metadata: {
                category: 'data',
                props: ['title', 'children'],
                description: 'Card container component'
            }
        },
        Badge: {
            module: () => import('/static/src/components/Badge.js'),
            metadata: {
                category: 'data',
                props: ['variant', 'children'],
                description: 'Badge label component'
            }
        },
    },

    // Componentes de layout
    layout: {
        Container: {
            module: () => import('/static/src/components/Container.js'),
            metadata: {
                category: 'layout',
                props: ['children', 'className'],
                description: 'Layout container component'
            }
        },
        Grid: {
            module: () => import('/static/src/components/Grid.js'),
            metadata: {
                category: 'layout',
                props: ['columns', 'gap', 'children'],
                description: 'Grid layout component'
            }
        },
        Stack: {
            module: () => import('/static/src/components/Stack.js'),
            metadata: {
                category: 'layout',
                props: ['direction', 'gap', 'children'],
                description: 'Stack layout component'
            }
        },
    },

    // Componentes específicos de YuKyu
    yukyu: {
        EmployeeCard: {
            module: () => import('/static/src/components/EmployeeCard.js'),
            metadata: {
                category: 'yukyu',
                props: ['employee', 'onClick'],
                description: 'Employee information card (名前, 残日数, etc)'
            }
        },
        LeaveRequestForm: {
            module: () => import('/static/src/components/LeaveRequestForm.js'),
            metadata: {
                category: 'yukyu',
                props: ['onSubmit', 'onCancel'],
                description: 'Leave request form (有給休暇申請)'
            }
        },
        ComplianceIndicator: {
            module: () => import('/static/src/components/ComplianceIndicator.js'),
            metadata: {
                category: 'yukyu',
                props: ['status', 'message'],
                description: 'Compliance status indicator (5日ルール, etc)'
            }
        },
        StatCard: {
            module: () => import('/static/src/components/StatCard.js'),
            metadata: {
                category: 'yukyu',
                props: ['label', 'value', 'unit'],
                description: 'Statistic card (残日数, etc)'
            }
        },
    }
};

/**
 * Registrar un componente individual (lazy load)
 * @private
 */
async function registerComponent(bridge, name, config) {
    try {
        const module = await config.module();
        const Component = module.default || module[name];

        if (!Component) {
            console.warn(`[Bridge Setup] Component ${name} export not found in module`);
            return false;
        }

        bridge.registerModernComponent(name, Component, config.metadata);
        console.log(`[Bridge Setup] ✓ Registered: ${name}`);
        return true;
    } catch (error) {
        console.error(`[Bridge Setup] ✗ Failed to register ${name}:`, error);
        return false;
    }
}

/**
 * Setup bridge con todos los componentes por defecto
 *
 * USAGE:
 * ```javascript
 * import { setupBridgeWithDefaults } from '/static/src/legacy-bridge/setup.js';
 *
 * await setupBridgeWithDefaults({
 *   categories: ['core', 'form', 'yukyu'],  // Solo estas categorías
 *   enableDebug: true,                       // Habilitar debug
 *   setupDefaultFeatures: true,              // Registrar features estándar
 * });
 * ```
 *
 * @param {Object} options - Opciones de setup
 * @param {Array<string>} options.categories - Categorías a registrar ('core', 'form', 'data', 'layout', 'yukyu')
 * @param {boolean} options.enableDebug - Habilitar debug mode (default: false)
 * @param {boolean} options.setupDefaultFeatures - Registrar features estándar (default: true)
 * @param {Function} options.onProgress - Callback para tracking de progreso
 * @returns {Promise<Object>} Setup result
 */
export async function setupBridgeWithDefaults(options = {}) {
    const {
        categories = ['core', 'form', 'data', 'layout', 'yukyu'],
        enableDebug = false,
        setupDefaultFeatures = true,
        onProgress = null
    } = options;

    const bridge = getUnifiedBridge();
    const results = {
        totalComponents: 0,
        registeredComponents: 0,
        failedComponents: 0,
        categories: {},
        startTime: Date.now(),
    };

    console.group('[Bridge Setup] Starting initialization...');
    console.log('Options:', { categories, enableDebug, setupDefaultFeatures });

    // Registrar componentes por categoría
    for (const category of categories) {
        if (!COMPONENT_REGISTRY[category]) {
            console.warn(`[Bridge Setup] Category "${category}" not found`);
            continue;
        }

        results.categories[category] = {
            total: 0,
            registered: 0
        };

        const categoryComponents = COMPONENT_REGISTRY[category];
        console.group(`📦 Category: ${category}`);

        for (const [componentName, config] of Object.entries(categoryComponents)) {
            results.totalComponents++;
            results.categories[category].total++;

            const success = await registerComponent(bridge, componentName, config);

            if (success) {
                results.registeredComponents++;
                results.categories[category].registered++;
            } else {
                results.failedComponents++;
            }

            // Progress callback
            if (onProgress) {
                onProgress({
                    component: componentName,
                    category,
                    total: results.totalComponents,
                    registered: results.registeredComponents,
                    failed: results.failedComponents
                });
            }
        }

        console.groupEnd();
    }

    // Setup features estándar
    if (setupDefaultFeatures) {
        console.group('🏢 Registering default features');

        const defaultFeatures = [
            // Dashboard
            { name: 'dashboard', system: 'hybrid', details: {
                modern: ['StatCards', 'Charts'],
                legacy: ['Table', 'Filters']
            }},

            // Employees
            { name: 'employees', system: 'hybrid', details: {
                modern: ['EmployeeCard', 'ActionButtons'],
                legacy: ['DataTable', 'Pagination']
            }},

            // Leave Requests
            { name: 'leave_requests', system: 'legacy', details: {
                status: 'Planned for Q2 2026 migration'
            }},

            // Compliance
            { name: 'compliance', system: 'legacy', details: {
                status: 'Planned for Q3 2026 migration'
            }},

            // Analytics
            { name: 'analytics', system: 'legacy', details: {
                status: 'Planned for Q3 2026 migration'
            }},
        ];

        defaultFeatures.forEach(feature => {
            bridge.registerFeature(feature.name, feature.system, feature.details);
            console.log(`  ✓ ${feature.name} (${feature.system})`);
        });

        console.groupEnd();
    }

    // Setup debug mode
    if (enableDebug) {
        console.group('🔍 Enabling debug mode');
        bridge.enableDebugMode();
        console.log('✓ Debug mode enabled');
        console.groupEnd();
    }

    // Print summary
    const duration = Date.now() - results.startTime;
    const successRate = Math.round((results.registeredComponents / results.totalComponents) * 100);

    console.log(`
╔════════════════════════════════════════════╗
║      BRIDGE SETUP COMPLETE                 ║
╚════════════════════════════════════════════╝

📊 Results:
   • Total components: ${results.totalComponents}
   • Successfully registered: ${results.registeredComponents}
   • Failed: ${results.failedComponents}
   • Success rate: ${successRate}%
   • Duration: ${duration}ms

📦 By category:
${Object.entries(results.categories)
    .map(([cat, stats]) => `   • ${cat}: ${stats.registered}/${stats.total}`)
    .join('\n')}

${enableDebug ? '✓ Debug mode: ENABLED' : '✗ Debug mode: disabled'}
${setupDefaultFeatures ? '✓ Default features: REGISTERED' : '✗ Default features: skipped'}

Bridge instance: window.UnifiedBridge
    `);

    console.groupEnd();

    // Retornar setup result
    return {
        bridge,
        results,
        getStatus: () => ({
            ready: results.registeredComponents > 0,
            components: results.registeredComponents,
            failed: results.failedComponents,
            success: successRate
        })
    };
}

/**
 * Setup mínimo (solo componentes core esenciales)
 *
 * USAGE:
 * ```javascript
 * import { setupBridgeMinimal } from '/static/src/legacy-bridge/setup.js';
 * await setupBridgeMinimal();
 * ```
 */
export async function setupBridgeMinimal() {
    return setupBridgeWithDefaults({
        categories: ['core'],
        enableDebug: false,
        setupDefaultFeatures: false
    });
}

/**
 * Setup completo con debug
 *
 * USAGE:
 * ```javascript
 * import { setupBridgeComplete } from '/static/src/legacy-bridge/setup.js';
 * await setupBridgeComplete();
 * ```
 */
export async function setupBridgeComplete() {
    return setupBridgeWithDefaults({
        categories: ['core', 'form', 'data', 'layout', 'yukyu'],
        enableDebug: true,
        setupDefaultFeatures: true
    });
}

/**
 * Setup con solo componentes YuKyu
 *
 * USAGE:
 * ```javascript
 * import { setupBridgeYuKyu } from '/static/src/legacy-bridge/setup.js';
 * await setupBridgeYuKyu();
 * ```
 */
export async function setupBridgeYuKyu() {
    return setupBridgeWithDefaults({
        categories: ['yukyu'],
        enableDebug: false,
        setupDefaultFeatures: true
    });
}

/**
 * Registrar componente personalizado (fuera del registry)
 *
 * USAGE:
 * ```javascript
 * import { registerCustomComponent } from '/static/src/legacy-bridge/setup.js';
 * import { MyCustomComponent } from './MyCustomComponent.js';
 *
 * await registerCustomComponent('MyCustom', MyCustomComponent, {
 *   category: 'custom',
 *   props: ['prop1', 'prop2'],
 *   description: 'My custom component'
 * });
 * ```
 *
 * @param {string} name - Component name
 * @param {Function} Component - Component factory
 * @param {Object} metadata - Component metadata
 */
export function registerCustomComponent(name, Component, metadata = {}) {
    const bridge = getUnifiedBridge();
    bridge.registerModernComponent(name, Component, {
        category: 'custom',
        ...metadata
    });
    console.log(`[Bridge Setup] ✓ Registered custom component: ${name}`);
}

/**
 * Get setup statistics
 *
 * USAGE:
 * ```javascript
 * const stats = getSetupStats();
 * console.log(stats);
 * ```
 */
export function getSetupStats() {
    const bridge = getUnifiedBridge();
    const components = bridge.getRegisteredComponents();
    const migration = bridge.getMigrationStats();

    return {
        bridge: {
            componentsRegistered: components.length,
            components: components,
        },
        migration: migration,
        summary: {
            total: components.length,
            categories: [...new Set(components.map(c => c.category))].sort(),
            features: Object.keys(migration.features).length,
            progress: bridge.getMigrationProgress()
        }
    };
}

/**
 * Print setup statistics
 *
 * USAGE:
 * ```javascript
 * printSetupStats();
 * ```
 */
export function printSetupStats() {
    const stats = getSetupStats();

    console.group('[Bridge Setup] Statistics');
    console.table({
        'Components Registered': stats.bridge.componentsRegistered,
        'Features': stats.summary.features,
        'Migration Progress': `${stats.summary.progress}%`
    });

    console.log('Categories:', stats.summary.categories);
    console.log('All components:', stats.bridge.components);
    console.groupEnd();
}

/**
 * Export setup helpers
 */
export default {
    setupBridgeWithDefaults,
    setupBridgeMinimal,
    setupBridgeComplete,
    setupBridgeYuKyu,
    registerCustomComponent,
    getSetupStats,
    printSetupStats,
    COMPONENT_REGISTRY
};
