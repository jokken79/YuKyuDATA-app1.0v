/**
 * Unit Tests for Utils Module
 * Testing critical security and utility functions
 */

import { 
    escapeHtml, 
    escapeAttr, 
    safeNumber, 
    isValidYear, 
    isValidString,
    formatNumber,
    debounce,
    throttle,
    rafThrottle,
    debounceImmediate,
    createCancelableDebounce,
    prefersReducedMotion,
    getAnimationDelay
} from '../../static/js/modules/utils.js';

// Mock window.matchMedia for reduced motion tests
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 16));

describe('Utils Module', () => {
    describe('Security Functions', () => {
        describe('escapeHtml', () => {
            it('should escape HTML entities correctly', () => {
                expect(escapeHtml('<script>alert("xss")</script>')).toBe('&lt;script&gt;alert("xss")&lt;/script&gt;');
                expect(escapeHtml('<div>content</div>')).toBe('&lt;div&gt;content&lt;/div&gt;');
                expect(escapeHtml('&')).toBe('&amp;');
            });

            it('should handle null and undefined values', () => {
                expect(escapeHtml(null)).toBe('');
                expect(escapeHtml(undefined)).toBe('');
            });

            it('should convert numbers to strings', () => {
                expect(escapeHtml(123)).toBe('123');
                expect(escapeHtml(0)).toBe('0');
            });
        });

        describe('escapeAttr', () => {
            it('should escape attribute values correctly', () => {
                expect(escapeAttr('data-value="test"')).toBe('data-value=&quot;test&quot;');
                expect(escapeAttr("class='my-class'")).toBe('class=&#39;my-class&#39;');
                expect(escapeAttr('onclick="alert(1)"')).toBe('onclick=&quot;alert(1)&quot;');
            });

            it('should handle null and undefined values', () => {
                expect(escapeAttr(null)).toBe('');
                expect(escapeAttr(undefined)).toBe('');
            });
        });
    });

    describe('Validation Functions', () => {
        describe('safeNumber', () => {
            it('should return valid numbers', () => {
                expect(safeNumber(42)).toBe(42);
                expect(safeNumber(3.14)).toBe(3.14);
                expect(safeNumber('123')).toBe(123);
                expect(safeNumber('45.67')).toBe(45.67);
            });

            it('should return default value for invalid numbers', () => {
                expect(safeNumber(NaN)).toBe(0);
                expect(safeNumber(Infinity)).toBe(0);
                expect(safeNumber(-Infinity)).toBe(0);
                expect(safeNumber('not-a-number')).toBe(0);
                expect(safeNumber(null)).toBe(0);
                expect(safeNumber(undefined)).toBe(0);
                expect(safeNumber({})).toBe(0);
            });

            it('should use custom default value', () => {
                expect(safeNumber(NaN, 99)).toBe(99);
                expect(safeNumber('invalid', -1)).toBe(-1);
            });
        });

        describe('isValidYear', () => {
            it('should validate years correctly', () => {
                expect(isValidYear(2023)).toBe(true);
                expect(isValidYear('2024')).toBe(true);
                expect(isValidYear(2000)).toBe(true);
                expect(isValidYear(2100)).toBe(true);
            });

            it('should reject invalid years', () => {
                expect(isValidYear(1999)).toBe(false);
                expect(isValidYear(2101)).toBe(false);
                expect(isValidYear('abc')).toBe(false);
                expect(isValidYear(null)).toBe(false);
                expect(isValidYear(undefined)).toBe(false);
                expect(isValidYear(202.5)).toBe(false);
            });
        });

        describe('isValidString', () => {
            it('should validate non-empty strings', () => {
                expect(isValidString('hello')).toBe(true);
                expect(isValidString('  trimmed  ')).toBe(true);
                expect(isValidString('0')).toBe(true);
                expect(isValidString(false)).toBe(true); // 'false'
            });

            it('should reject empty or invalid strings', () => {
                expect(isValidString('')).toBe(false);
                expect(isValidString('   ')).toBe(false);
                expect(isValidString(null)).toBe(false);
                expect(isValidString(undefined)).toBe(false);
            });
        });
    });

    describe('Format Functions', () => {
        describe('formatNumber', () => {
            it('should format numbers correctly', () => {
                expect(formatNumber(1234)).toBe('1,234');
                expect(formatNumber(1234567)).toBe('1,234,567');
                expect(formatNumber(0)).toBe('0');
            });

            it('should handle decimals', () => {
                expect(formatNumber(3.14159, 2)).toBe('3.14');
                expect(formatNumber(2.5, 1)).toBe('2.5');
                expect(formatNumber(1, 3)).toBe('1.000');
            });

            it('should handle invalid numbers', () => {
                expect(formatNumber(NaN)).toBe('0');
                expect(formatNumber(null)).toBe('0');
                expect(formatNumber('invalid')).toBe('0');
            });
        });
    });

    describe('Performance Functions', () => {
        describe('debounce', () => {
            jest.useFakeTimers();

            it('should delay function execution', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounce(mockFn, 100);

                debouncedFn();
                expect(mockFn).not.toHaveBeenCalled();

                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledTimes(1);
            });

            it('should cancel previous calls', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounce(mockFn, 100);

                debouncedFn('first');
                debouncedFn('second');
                debouncedFn('third');

                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledTimes(1);
                expect(mockFn).toHaveBeenCalledWith('third');
            });

            afterEach(() => {
                jest.clearAllTimers();
            });
        });

        describe('throttle', () => {
            jest.useFakeTimers();

            it('should limit function execution frequency', () => {
                const mockFn = jest.fn(() => 'result');
                const throttledFn = throttle(mockFn, 100);

                const result1 = throttledFn('call1');
                expect(mockFn).toHaveBeenCalledTimes(1);
                expect(result1).toBe('result');

                const result2 = throttledFn('call2');
                expect(mockFn).toHaveBeenCalledTimes(1);
                expect(result2).toBe('result');

                jest.advanceTimersByTime(100);
                const result3 = throttledFn('call3');
                expect(mockFn).toHaveBeenCalledTimes(2);
                expect(result3).toBe('result');
            });

            afterEach(() => {
                jest.clearAllTimers();
            });
        });

        describe('rafThrottle', () => {
            it('should use requestAnimationFrame', () => {
                const mockFn = jest.fn();
                const rafThrottledFn = rafThrottle(mockFn);

                rafThrottledFn('test');
                expect(requestAnimationFrame).toHaveBeenCalled();

                jest.advanceTimersByTime(16);
                expect(mockFn).toHaveBeenCalledWith('test');
            });

            it('should ignore repeated calls while pending', () => {
                const mockFn = jest.fn();
                const rafThrottledFn = rafThrottle(mockFn);

                rafThrottledFn('first');
                rafThrottledFn('second');
                expect(requestAnimationFrame).toHaveBeenCalledTimes(1);
            });
        });

        describe('debounceImmediate', () => {
            jest.useFakeTimers();

            it('should execute immediately when immediate is true', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounceImmediate(mockFn, 100, true);

                debouncedFn('immediate');
                expect(mockFn).toHaveBeenCalledWith('immediate');
            });

            it('should not execute again after immediate call', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounceImmediate(mockFn, 100, true);

                debouncedFn('immediate');
                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledTimes(1);
            });

            it('should delay execution when immediate is false', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounceImmediate(mockFn, 100, false);

                debouncedFn('delayed');
                expect(mockFn).not.toHaveBeenCalled();

                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledWith('delayed');
            });

            it('should clear pending timeouts on repeat', () => {
                const mockFn = jest.fn();
                const debouncedFn = debounceImmediate(mockFn, 100, false);

                debouncedFn('first');
                debouncedFn('second');
                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledTimes(1);
            });

            afterEach(() => {
                jest.clearAllTimers();
            });
        });

        describe('createCancelableDebounce', () => {
            jest.useFakeTimers();

            it('should provide cancelable debounce functionality', () => {
                const mockFn = jest.fn();
                const cancelableDebounce = createCancelableDebounce(mockFn, 100);

                cancelableDebounce.execute('test');
                expect(cancelableDebounce.isPending()).toBe(true);

                cancelableDebounce.cancel();
                expect(cancelableDebounce.isPending()).toBe(false);

                jest.advanceTimersByTime(100);
                expect(mockFn).not.toHaveBeenCalled();
            });

            it('should execute when not cancelled', () => {
                const mockFn = jest.fn();
                const cancelableDebounce = createCancelableDebounce(mockFn, 100);

                cancelableDebounce.execute('test');
                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledWith('test');
            });

            it('should reset timer when executed again', () => {
                const mockFn = jest.fn();
                const cancelableDebounce = createCancelableDebounce(mockFn, 100);

                cancelableDebounce.execute('first');
                cancelableDebounce.execute('second');
                jest.advanceTimersByTime(100);
                expect(mockFn).toHaveBeenCalledTimes(1);
            });

            it('cancel is safe when nothing is pending', () => {
                const mockFn = jest.fn();
                const cancelableDebounce = createCancelableDebounce(mockFn, 100);

                cancelableDebounce.cancel();
                expect(cancelableDebounce.isPending()).toBe(false);
            });

            afterEach(() => {
                jest.clearAllTimers();
            });
        });
    });

    describe('Accessibility Functions', () => {
        describe('prefersReducedMotion', () => {
            it('should detect reduced motion preference', () => {
                expect(prefersReducedMotion()).toBe(true);
            });
        });

        describe('getAnimationDelay', () => {
            it('should return 0 when reduced motion is preferred', () => {
                expect(getAnimationDelay(300)).toBe(0);
            });

            it('should return normal delay when reduced motion is not preferred', () => {
                window.matchMedia.mockImplementationOnce(() => ({
                    matches: false,
                    media: '(prefers-reduced-motion: reduce)',
                    onchange: null,
                    addListener: jest.fn(),
                    removeListener: jest.fn(),
                    addEventListener: jest.fn(),
                    removeEventListener: jest.fn(),
                    dispatchEvent: jest.fn(),
                }));

                expect(getAnimationDelay(300)).toBe(300);
            });
        });
    });
});
