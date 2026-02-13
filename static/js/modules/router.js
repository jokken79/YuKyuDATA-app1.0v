/**
 * YuKyu Router Module
 * Simple Hash-based routing.
 */

export const Router = {
    routes: {},
    currentRoute: null,

    init(routesCallback) {
        this.routesCallback = routesCallback;
        window.addEventListener('hashchange', () => this.handleRouting());

        // Initial route
        if (!window.location.hash) {
            window.location.hash = 'dashboard';
        } else {
            this.handleRouting();
        }
    },

    handleRouting() {
        const hash = window.location.hash.substring(1); // remove #
        // Default to dashboard if empty
        const route = hash || 'dashboard';

        this.currentRoute = route;

        if (this.routesCallback) {
            this.routesCallback(route);
        }

        window.dispatchEvent(new CustomEvent('router:change', { detail: { route } }));
    }
};
