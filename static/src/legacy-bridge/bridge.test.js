/**
 * Legacy Bridge: Unit Tests
 *
 * Tests para verificar funcionamiento del bridge
 * Ejecutar con: npm test -- bridge.test.js
 */

import { getUnifiedBridge, initBridge } from './unified-bridge.js';

/**
 * Setup y teardown
 */
let bridge;

beforeEach(() => {
    // Limpiar globalbridge
    if (window.UnifiedBridge) {
        delete window.UnifiedBridge;
    }
    // Crear nueva instancia
    bridge = initBridge();
});

afterEach(() => {
    if (bridge) {
        // Cleanup
        bridge = null;
    }
});

/**
 * ============================================================================
 * TESTS: Component Registry
 * ============================================================================
 */

describe('Component Registry', () => {
    test('should register a component', () => {
        const TestComponent = () => '<div>Test</div>';

        bridge.registerModernComponent('Test', TestComponent, {
            category: 'test',
            props: ['text'],
            description: 'Test component'
        });

        expect(bridge.componentRegistry.has('Test')).toBe(true);
    });

    test('should throw error for non-function component', () => {
        expect(() => {
            bridge.registerModernComponent('Invalid', 'not-a-function');
        }).toThrow(TypeError);
    });

    test('should get registered component', () => {
        const TestComponent = () => '<div>Test</div>';
        bridge.registerModernComponent('Test', TestComponent);

        const retrieved = bridge.componentRegistry.get('Test');
        expect(retrieved).toBe(TestComponent);
    });

    test('should list all registered components', () => {
        const Comp1 = () => '<div>1</div>';
        const Comp2 = () => '<div>2</div>';

        bridge.registerModernComponent('Comp1', Comp1, { category: 'core' });
        bridge.registerModernComponent('Comp2', Comp2, { category: 'form' });

        const all = bridge.getRegisteredComponents();
        expect(all.length).toBe(2);
        expect(all.map(c => c.name)).toEqual(['Comp1', 'Comp2']);
    });

    test('should get components by category', () => {
        bridge.registerModernComponent('Alert', () => '<div>Alert</div>', { category: 'core' });
        bridge.registerModernComponent('Button', () => '<div>Button</div>', { category: 'core' });
        bridge.registerModernComponent('Input', () => '<div>Input</div>', { category: 'form' });

        const coreComps = bridge.componentRegistry.getByCategory('core');
        expect(coreComps).toEqual(['Alert', 'Button']);
    });
});

/**
 * ============================================================================
 * TESTS: State Synchronization
 * ============================================================================
 */

describe('State Synchronization', () => {
    test('should sync state value', () => {
        bridge.syncState('testKey', 'testValue');

        expect(bridge.getState('testKey')).toBe('testValue');
    });

    test('should sync with legacy App.state', () => {
        window.App = window.App || {};
        window.App.state = {};

        bridge.syncState('year', 2025);

        expect(window.App.state.year).toBe(2025);
        expect(bridge.getState('year')).toBe(2025);
    });

    test('should subscribe to state changes', (done) => {
        const callback = jest.fn((newVal, oldVal) => {
            expect(newVal).toBe('newValue');
            expect(oldVal).toBeUndefined();
            done();
        });

        bridge.onStateChange('key', callback);
        bridge.syncState('key', 'newValue');
    });

    test('should unsubscribe from state changes', () => {
        const callback = jest.fn();

        const unsub = bridge.onStateChange('key', callback);
        unsub();

        bridge.syncState('key', 'value');

        expect(callback).not.toHaveBeenCalled();
    });

    test('should get state snapshot', () => {
        bridge.syncState('key1', 'value1');
        bridge.syncState('key2', 'value2');

        const snapshot = bridge.getStateSnapshot();

        expect(snapshot.modern.key1).toBe('value1');
        expect(snapshot.modern.key2).toBe('value2');
    });

    test('should notify multiple subscribers', () => {
        const callback1 = jest.fn();
        const callback2 = jest.fn();

        bridge.onStateChange('key', callback1);
        bridge.onStateChange('key', callback2);

        bridge.syncState('key', 'value');

        expect(callback1).toHaveBeenCalledWith('value', undefined, 'key');
        expect(callback2).toHaveBeenCalledWith('value', undefined, 'key');
    });

    test('should handle subscriber errors gracefully', () => {
        const errorCallback = jest.fn(() => {
            throw new Error('Subscriber error');
        });

        bridge.onStateChange('key', errorCallback);

        // Should not throw
        expect(() => {
            bridge.syncState('key', 'value');
        }).not.toThrow();
    });

    test('should track state sync log', () => {
        bridge.syncState('key1', 'value1', 'modern');
        bridge.syncState('key2', 'value2', 'legacy');

        const log = bridge.stateSync.getSyncLog();

        expect(log.length).toBe(2);
        expect(log[0].key).toBe('key1');
        expect(log[0].source).toBe('modern');
        expect(log[1].source).toBe('legacy');
    });
});

/**
 * ============================================================================
 * TESTS: Component Rendering
 * ============================================================================
 */

describe('Component Rendering', () => {
    test('should render component in legacy container', async () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        const TestComponent = () => {
            const div = document.createElement('div');
            div.textContent = 'Rendered content';
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        await bridge.renderInLegacy('Test', 'test-container', {});

        expect(container.textContent).toContain('Rendered content');

        document.body.removeChild(container);
    });

    test('should throw error for unregistered component', async () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        await expect(
            bridge.renderInLegacy('Unregistered', 'test-container', {})
        ).rejects.toThrow('not registered');

        document.body.removeChild(container);
    });

    test('should throw error for missing container', async () => {
        const TestComponent = () => '<div>Test</div>';
        bridge.registerModernComponent('Test', TestComponent);

        await expect(
            bridge.renderInLegacy('Test', 'non-existent-container', {})
        ).rejects.toThrow('not found');
    });

    test('should pass props to component', async () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        const TestComponent = (props) => {
            const div = document.createElement('div');
            div.textContent = props.message;
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        await bridge.renderInLegacy('Test', 'test-container', {
            message: 'Hello props'
        });

        expect(container.textContent).toBe('Hello props');

        document.body.removeChild(container);
    });

    test('should clear container before rendering', async () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        container.innerHTML = '<p>Old content</p>';
        document.body.appendChild(container);

        const TestComponent = () => {
            const div = document.createElement('div');
            div.textContent = 'New content';
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        await bridge.renderInLegacy('Test', 'test-container', {}, {
            clearContainer: true
        });

        expect(container.innerHTML).not.toContain('Old content');
        expect(container.textContent).toContain('New content');

        document.body.removeChild(container);
    });

    test('should emit component-rendered event', async () => {
        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        const TestComponent = () => '<div>Test</div>';
        bridge.registerModernComponent('Test', TestComponent);

        const eventHandler = jest.fn();
        bridge.on('component-rendered', eventHandler);

        await bridge.renderInLegacy('Test', 'test-container', {});

        expect(eventHandler).toHaveBeenCalledWith(
            expect.objectContaining({
                componentName: 'Test',
                containerId: 'test-container',
                timestamp: expect.any(Number),
                duration: expect.any(Number)
            })
        );

        document.body.removeChild(container);
    });

    test('should emit component-error event on failure', async () => {
        const TestComponent = () => '<div>Test</div>';
        bridge.registerModernComponent('Test', TestComponent);

        const eventHandler = jest.fn();
        bridge.on('component-error', eventHandler);

        await bridge.renderInLegacy('Test', 'non-existent', {})
            .catch(() => {}); // Catch error

        expect(eventHandler).toHaveBeenCalledWith(
            expect.objectContaining({
                componentName: 'Test',
                containerId: 'non-existent',
                error: expect.any(String)
            })
        );
    });
});

/**
 * ============================================================================
 * TESTS: Migration Tracking
 * ============================================================================
 */

describe('Migration Tracking', () => {
    test('should register feature', () => {
        bridge.registerFeature('employees', 'legacy', {
            description: 'Employee management'
        });

        const stats = bridge.getMigrationStats();
        expect(stats.features.employees).toBeDefined();
        expect(stats.features.employees.system).toBe('legacy');
    });

    test('should track component usage', () => {
        bridge.migrationTracker.trackComponentUsage('Alert', 'modern');
        bridge.migrationTracker.trackComponentUsage('Alert', 'modern');

        const stats = bridge.getMigrationStats();
        expect(stats.componentUsage['Alert:modern']).toBe(2);
    });

    test('should track page views', () => {
        bridge.trackPageView('dashboard', 'hybrid');
        bridge.trackPageView('employees', 'legacy');

        const stats = bridge.getMigrationStats();
        expect(stats.pageViews.length).toBe(2);
    });

    test('should calculate migration progress', () => {
        bridge.registerFeature('feature1', 'legacy');
        bridge.registerFeature('feature2', 'legacy');
        bridge.registerFeature('feature3', 'modern');
        bridge.registerFeature('feature4', 'modern');
        bridge.registerFeature('feature5', 'hybrid');

        const progress = bridge.getMigrationProgress();
        // 3 out of 5 are modern/hybrid = 60%
        expect(progress).toBe(60);
    });

    test('should generate migration report', () => {
        bridge.registerFeature('feature1', 'legacy');
        bridge.registerFeature('feature2', 'modern');

        const report = bridge.getMigrationReport();

        expect(report).toContain('MIGRATION STATUS');
        expect(report).toContain('Progress');
        expect(report).toContain('Features by System');
    });

    test('should export migration data', () => {
        bridge.registerFeature('feature1', 'modern');
        bridge.syncState('testKey', 'testValue');

        const data = bridge.exportMigrationData();

        expect(data.timestamp).toBeDefined();
        expect(data.progress).toBe(100); // 1 feature, all modern
        expect(data.stats).toBeDefined();
        expect(data.stateSync).toBeDefined();
    });
});

/**
 * ============================================================================
 * TESTS: Events
 * ============================================================================
 */

describe('Event System', () => {
    test('should register event listener', () => {
        const handler = jest.fn();
        bridge.on('test-event', handler);

        bridge._emitEvent('test-event', { data: 'test' });

        expect(handler).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should remove event listener', () => {
        const handler = jest.fn();
        bridge.on('test-event', handler);
        bridge.off('test-event', handler);

        bridge._emitEvent('test-event', { data: 'test' });

        expect(handler).not.toHaveBeenCalled();
    });

    test('should handle multiple listeners for same event', () => {
        const handler1 = jest.fn();
        const handler2 = jest.fn();

        bridge.on('test-event', handler1);
        bridge.on('test-event', handler2);

        bridge._emitEvent('test-event', { data: 'test' });

        expect(handler1).toHaveBeenCalled();
        expect(handler2).toHaveBeenCalled();
    });

    test('should handle listener errors gracefully', () => {
        const errorHandler = jest.fn(() => {
            throw new Error('Handler error');
        });

        bridge.on('test-event', errorHandler);

        expect(() => {
            bridge._emitEvent('test-event', {});
        }).not.toThrow();
    });
});

/**
 * ============================================================================
 * TESTS: Debug
 * ============================================================================
 */

describe('Debug Mode', () => {
    test('should enable debug mode', () => {
        const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

        bridge.enableDebugMode();
        bridge.registerFeature('test', 'modern');

        expect(consoleSpy).toHaveBeenCalled();

        consoleSpy.mockRestore();
    });

    test('should get debug info', () => {
        const TestComponent = () => '<div>Test</div>';
        bridge.registerModernComponent('Test', TestComponent);
        bridge.registerFeature('feature1', 'modern');

        const debugInfo = bridge.getDebugInfo();

        expect(debugInfo.components).toBeDefined();
        expect(debugInfo.state).toBeDefined();
        expect(debugInfo.migration).toBeDefined();
        expect(debugInfo.renderQueue).toBeDefined();
        expect(debugInfo.uptime).toBeDefined();
    });
});

/**
 * ============================================================================
 * TESTS: Singleton Pattern
 * ============================================================================
 */

describe('Singleton Pattern', () => {
    test('should return same instance', () => {
        const bridge1 = getUnifiedBridge();
        const bridge2 = getUnifiedBridge();

        expect(bridge1).toBe(bridge2);
    });

    test('should expose to window globally', () => {
        initBridge();

        expect(window.UnifiedBridge).toBeDefined();
        expect(window.UnifiedBridge).toBeInstanceOf(Object);
    });
});

/**
 * ============================================================================
 * TESTS: Integration
 * ============================================================================
 */

describe('Integration Tests', () => {
    test('should handle complete workflow', async () => {
        // 1. Register component
        const TestComponent = (props) => {
            const div = document.createElement('div');
            div.id = 'test-output';
            div.textContent = props.message;
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        // 2. Register feature
        bridge.registerFeature('test_workflow', 'modern');

        // 3. Sync state
        bridge.syncState('workflowState', 'initialized');

        // 4. Create container
        const container = document.createElement('div');
        container.id = 'workflow-container';
        document.body.appendChild(container);

        // 5. Render component
        await bridge.renderInLegacy('Test', 'workflow-container', {
            message: 'Workflow complete'
        });

        // 6. Verify
        const output = document.getElementById('test-output');
        expect(output.textContent).toBe('Workflow complete');

        const stats = bridge.getMigrationStats();
        expect(stats.features.test_workflow.system).toBe('modern');

        expect(bridge.getState('workflowState')).toBe('initialized');

        // Cleanup
        document.body.removeChild(container);
    });
});

/**
 * ============================================================================
 * TESTS: Edge Cases
 * ============================================================================
 */

describe('Edge Cases', () => {
    test('should handle rendering same component multiple times', async () => {
        const TestComponent = () => {
            const div = document.createElement('div');
            div.textContent = 'Test';
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        await bridge.renderInLegacy('Test', 'test-container', {});
        await bridge.renderInLegacy('Test', 'test-container', {});
        await bridge.renderInLegacy('Test', 'test-container', {});

        expect(container.textContent).toBe('Test');

        document.body.removeChild(container);
    });

    test('should handle null/undefined props', async () => {
        const TestComponent = (props) => {
            const div = document.createElement('div');
            div.textContent = String(props?.value || 'empty');
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        const container = document.createElement('div');
        container.id = 'test-container';
        document.body.appendChild(container);

        await bridge.renderInLegacy('Test', 'test-container', null);

        expect(container.textContent).toBe('empty');

        document.body.removeChild(container);
    });

    test('should handle concurrent renders', async () => {
        const TestComponent = (props) => {
            const div = document.createElement('div');
            div.textContent = props.id;
            return div;
        };

        bridge.registerModernComponent('Test', TestComponent);

        const containers = ['c1', 'c2', 'c3'].map(id => {
            const div = document.createElement('div');
            div.id = id;
            document.body.appendChild(div);
            return div;
        });

        await Promise.all([
            bridge.renderInLegacy('Test', 'c1', { id: '1' }),
            bridge.renderInLegacy('Test', 'c2', { id: '2' }),
            bridge.renderInLegacy('Test', 'c3', { id: '3' })
        ]);

        expect(containers[0].textContent).toBe('1');
        expect(containers[1].textContent).toBe('2');
        expect(containers[2].textContent).toBe('3');

        containers.forEach(c => document.body.removeChild(c));
    });
});
