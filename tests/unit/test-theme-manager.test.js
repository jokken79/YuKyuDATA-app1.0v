import { ThemeManager } from '../../static/js/modules/theme-manager.js';

describe('ThemeManager', () => {
    let manager;

    beforeEach(() => {
        document.body.innerHTML = `
            <span id="theme-icon"></span>
            <span id="theme-label"></span>
            <input class="flatpickr-input" />
        `;
        manager = new ThemeManager();
        localStorage.getItem.mockReset();
        localStorage.setItem.mockReset();
    });

    it('initializes from storage and applies theme', () => {
        localStorage.getItem.mockReturnValue('light');
        manager.init();
        expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    it('falls back to default theme when storage is empty', () => {
        localStorage.getItem.mockReturnValue(null);
        manager.init();
        expect(manager.getCurrent()).toBe('dark');
    });

    it('toggles theme and updates UI', () => {
        const toast = jest.fn();
        manager.toggle(toast);
        expect(localStorage.setItem).toHaveBeenCalled();
        expect(document.getElementById('theme-label').textContent).not.toBe('');

        manager.toggle(toast);
        expect(toast).toHaveBeenCalledTimes(2);
    });

    it('handles missing theme elements safely', () => {
        document.body.innerHTML = '';
        expect(() => manager.updateThemeButton()).not.toThrow();
        expect(() => manager.toggle()).not.toThrow();
    });

    it('updates flatpickr instances', () => {
        const input = document.querySelector('.flatpickr-input');
        const destroy = jest.fn();
        input._flatpickr = { config: { foo: 'bar' }, destroy };
        window.flatpickr = jest.fn();

        manager.updateFlatpickr();
        expect(destroy).toHaveBeenCalled();
        expect(window.flatpickr).toHaveBeenCalled();
    });

    it('sets theme explicitly and validates', () => {
        manager.setTheme('light');
        expect(manager.getCurrent()).toBe('light');
        expect(manager.isDark()).toBe(false);

        manager.setTheme('invalid');
        expect(manager.getCurrent()).toBe('light');
    });
});
