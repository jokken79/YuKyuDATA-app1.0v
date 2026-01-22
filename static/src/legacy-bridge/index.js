/**
 * Legacy Bridge: Main Export
 *
 * Central entry point para el sistema de puente legacy-moderno
 * Exporta todas las APIs públicas
 *
 * USAGE:
 * ```javascript
 * // Import bridge core
 * import { getUnifiedBridge, initBridge } from '/static/src/legacy-bridge/index.js';
 *
 * // Import setup helpers
 * import { setupBridgeWithDefaults, setupBridgeComplete } from '/static/src/legacy-bridge/index.js';
 *
 * // O directamente de archivos específicos
 * import { unified-bridge } from './unified-bridge.js';
 * ```
 */

// Core bridge
export {
    getUnifiedBridge,
    initBridge,
    UnifiedBridge
} from './unified-bridge.js';

// State bridge
export {
    initUnifiedStateBridge,
    getAppUnifiedState,
    getPageCoordinator,
    switchPageModern,
    subscribeToState,
    setStateValue,
    getStateSnapshot,
    getFilteredData,
    getStatistics,
    setupPageSwitchingDelegation,
    cleanupUnifiedState,
    enableStateDebugLogging
} from './unified-state-bridge.js';

// Setup helpers
export {
    setupBridgeWithDefaults,
    setupBridgeMinimal,
    setupBridgeComplete,
    setupBridgeYuKyu,
    registerCustomComponent,
    getSetupStats,
    printSetupStats,
    COMPONENT_REGISTRY
} from './setup.js';

/**
 * Alias para nombres comunes
 */
export const Bridge = getUnifiedBridge;

/**
 * Helper para inicialización rápida
 * Combina initBridge + setupBridgeWithDefaults
 *
 * USAGE:
 * ```javascript
 * import { quickStart } from '/static/src/legacy-bridge/index.js';
 * await quickStart();
 * ```
 */
export async function quickStart(options = {}) {
    const { initBridge: init } = await import('./unified-bridge.js');
    const { setupBridgeWithDefaults } = await import('./setup.js');

    const bridge = init();
    await setupBridgeWithDefaults(options);

    return bridge;
}

/**
 * Información de versión
 */
export const VERSION = {
    bridge: '1.0.0',
    pattern: 'Strangler Fig',
    lastUpdated: '2026-01-22',
    components: {
        core: 'unified-bridge.js',
        state: 'unified-state-bridge.js',
        setup: 'setup.js',
        examples: 'examples.js',
        migration: 'MIGRATION_GUIDE.md'
    }
};

/**
 * Re-export todo desde ejemplos (útil para testing)
 */
export * from './examples.js';

export default {
    getUnifiedBridge,
    initBridge,
    setupBridgeWithDefaults,
    setupBridgeComplete,
    quickStart,
    VERSION
};
