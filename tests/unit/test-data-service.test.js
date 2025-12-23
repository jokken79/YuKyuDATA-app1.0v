/**
 * Unit Tests for DataService Module
 * Testing critical data fetching and synchronization functionality
 */

import { jest } from '@jest/globals';
import { DataService } from '../../static/js/modules/data-service.js';

// Mock fetch globally
global.fetch = jest.fn();

describe('DataService', () => {
    let dataService;
    let mockState;
    let mockUpdateUI;
    let mockShowToast;

    beforeEach(() => {
        dataService = new DataService('http://localhost:8000/api');
        mockState = {
            data: [],
            availableYears: [],
            year: null
        };
        mockUpdateUI = jest.fn();
        mockShowToast = jest.fn();
        
        // Reset fetch mock
        fetch.mockClear();
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    describe('fetchEmployees', () => {
        it('should fetch employees successfully and update state', async () => {
            const mockResponse = {
                data: [
                    { employee_num: '001', name: 'Test Employee', granted: 10, used: 5, employee_type: 'staff' }
                ],
                available_years: [2023, 2024]
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            await dataService.fetchEmployees(2024, true, mockState, mockUpdateUI, mockShowToast);

            expect(fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/employees?enhanced=true&active_only=true&year=2024'
            );
            expect(mockState.data).toHaveLength(1);
            expect(mockState.data[0]).toMatchObject({
                employeeNum: '001',
                name: 'Test Employee',
                usageRate: 50
            });
            expect(mockState.availableYears).toEqual([2023, 2024]);
            expect(mockUpdateUI).toHaveBeenCalled();
            expect(mockShowToast).toHaveBeenCalledWith('success', 'Data refresh complete');
        });

        it('should handle race conditions correctly', async () => {
            const firstResponse = {
                data: [{ employee_num: '001', name: 'First' }],
                available_years: [2023]
            };
            const secondResponse = {
                data: [{ employee_num: '002', name: 'Second' }],
                available_years: [2024]
            };

            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => firstResponse
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => secondResponse
                });

            // Start two requests simultaneously
            const firstPromise = dataService.fetchEmployees(2023, true, mockState, mockUpdateUI, mockShowToast);
            const secondPromise = dataService.fetchEmployees(2024, true, mockState, mockUpdateUI, mockShowToast);

            await Promise.all([firstPromise, secondPromise]);

            // Only the second (latest) request should update the state
            expect(mockState.data[0].name).toBe('Second');
            expect(mockState.year).toBe(2024);
        });

        it('should handle fetch errors gracefully', async () => {
            fetch.mockRejectedValueOnce(new Error('Network error'));

            await dataService.fetchEmployees(2024, true, mockState, mockUpdateUI, mockShowToast);

            expect(mockShowToast).toHaveBeenCalledWith('error', 'Failed to load data');
        });

        it('should select current year automatically if not provided', async () => {
            const currentYear = new Date().getFullYear();
            const mockResponse = {
                data: [],
                available_years: [currentYear - 1, currentYear]
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            await dataService.fetchEmployees(null, true, mockState, mockUpdateUI, mockShowToast);

            expect(mockState.year).toBe(currentYear);
        });

        it('should allow missing update callbacks', async () => {
            const mockResponse = {
                data: [{ employee_num: '005', name: 'NoCallbacks', granted: 1, used: 0 }],
                available_years: [2024]
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            await dataService.fetchEmployees(2024, true, null, null, null);
            expect(fetch).toHaveBeenCalled();
        });

        it('selects fallback year and refetches when needed', async () => {
            const mockResponse = {
                data: [{ employee_num: '003', name: 'Third', granted: 0, used: 0 }],
                available_years: [2019, 2020]
            };

            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => mockResponse
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => mockResponse
                });

            await dataService.fetchEmployees(null, true, mockState, mockUpdateUI, mockShowToast);
            expect(mockState.year).toBe(2019);
            expect(fetch).toHaveBeenCalledTimes(2);
        });

        it('skips UI updates when request becomes stale after parsing', async () => {
            const mockResponse = {
                data: [{ employee_num: '004', name: 'Late' }],
                available_years: [2024]
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => {
                    dataService._fetchRequestId += 1;
                    return mockResponse;
                }
            });

            await dataService.fetchEmployees(2024, true, null, mockUpdateUI, mockShowToast);
            expect(mockUpdateUI).not.toHaveBeenCalled();
            expect(mockShowToast).not.toHaveBeenCalled();
        });
    });

    describe('sync', () => {
        it('should sync data successfully', async () => {
            const mockResponse = { count: 42 };
            const mockSetBtnLoading = jest.fn();
            const mockRefetchData = jest.fn();

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse
            });

            // Mock DOM element
            document.getElementById = jest.fn(() => ({ id: 'btn-sync-main' }));

            await dataService.sync(mockSetBtnLoading, mockShowToast, mockRefetchData);

            expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/sync', { method: 'POST' });
            expect(mockSetBtnLoading).toHaveBeenCalledWith({ id: 'btn-sync-main' }, true);
            expect(mockShowToast).toHaveBeenCalledWith('success', '✅ 42件の有給データを同期しました', 5000);
            expect(mockRefetchData).toHaveBeenCalled();
            expect(mockSetBtnLoading).toHaveBeenCalledWith({ id: 'btn-sync-main' }, false);
        });

        it('should handle network errors', async () => {
            const mockSetBtnLoading = jest.fn();
            fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

            document.getElementById = jest.fn(() => ({ id: 'btn-sync-main' }));

            await dataService.sync(mockSetBtnLoading, mockShowToast);

            expect(mockShowToast).toHaveBeenCalledWith(
                'error',
                '🌐 ネットワークエラー: サーバーに接続できません',
                6000
            );
        });

        it('should handle server errors', async () => {
            const mockSetBtnLoading = jest.fn();
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                text: async () => 'Internal Server Error'
            });

            document.getElementById = jest.fn(() => ({ id: 'btn-sync-main' }));

            await dataService.sync(mockSetBtnLoading, mockShowToast);

            expect(mockShowToast).toHaveBeenCalledWith(
                'error',
                '❌ 同期失敗: Internal Server Error',
                6000
            );
        });

        it('syncs without optional callbacks', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ count: 1 })
            });

            document.getElementById = jest.fn(() => ({ id: 'btn-sync-main' }));

            await dataService.sync();
        });
    });

    describe('syncGenzai and syncUkeoi', () => {
        it('syncs genzai and ukeoi successfully', async () => {
            const mockSetBtnLoading = jest.fn();
            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ count: 2 })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ count: 3 })
                });

            document.getElementById = jest.fn((id) => ({ id }));

            await dataService.syncGenzai(mockSetBtnLoading, mockShowToast);
            await dataService.syncUkeoi(mockSetBtnLoading, mockShowToast);

            expect(mockShowToast).toHaveBeenCalledWith(
                'success',
                expect.stringContaining('派遣社員データを同期しました (2件)'),
                5000
            );
            expect(mockShowToast).toHaveBeenCalledWith(
                'success',
                expect.stringContaining('請負社員データを同期しました (3件)'),
                5000
            );
        });

        it('handles genzai and ukeoi errors', async () => {
            const mockSetBtnLoading = jest.fn();
            fetch
                .mockResolvedValueOnce({
                    ok: false,
                    status: 500,
                    json: async () => ({})
                })
                .mockRejectedValueOnce(new Error('network error'));

            document.getElementById = jest.fn((id) => ({ id }));

            await dataService.syncGenzai(mockSetBtnLoading, mockShowToast);
            await dataService.syncUkeoi(mockSetBtnLoading, mockShowToast);

            expect(mockShowToast).toHaveBeenCalledWith(
                'error',
                expect.stringContaining('派遣社員の同期に失敗しました'),
                6000
            );
            expect(mockShowToast).toHaveBeenCalledWith(
                'error',
                expect.stringContaining('請負社員の同期に失敗しました'),
                6000
            );
        });

        it('syncs genzai and ukeoi without callbacks', async () => {
            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ count: 1 })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ count: 1 })
                });

            document.getElementById = jest.fn((id) => ({ id }));

            await dataService.syncGenzai();
            await dataService.syncUkeoi();
        });
    });

    describe('getFiltered', () => {
        it('should filter data by year correctly', () => {
            const testData = [
                { year: 2023, name: 'Employee 1' },
                { year: 2024, name: 'Employee 2' },
                { year: 2024, name: 'Employee 3' }
            ];

            const filtered = dataService.getFiltered(testData, 2024);

            expect(filtered).toHaveLength(2);
            expect(filtered.every(emp => emp.year === 2024)).toBe(true);
        });

        it('should return all data when no year filter is provided', () => {
            const testData = [
                { year: 2023, name: 'Employee 1' },
                { year: 2024, name: 'Employee 2' }
            ];

            const filtered = dataService.getFiltered(testData, null);

            expect(filtered).toEqual(testData);
        });
    });

    describe('getFactoryStats', () => {
        it('should calculate factory statistics correctly', () => {
            const testData = [
                { haken: 'Factory A', used: 5 },
                { haken: 'Factory B', used: 3 },
                { haken: 'Factory A', used: 2 },
                { haken: 'Factory C', used: 4 },
                { haken: '0', used: 1 }, // Should be filtered out
                { haken: '', used: 1 },   // Should be filtered out
                { haken: 'Unknown', used: 1 } // Should be filtered out
            ];

            const stats = dataService.getFactoryStats(testData);

            expect(stats).toEqual([
                ['Factory A', 7],
                ['Factory C', 4],
                ['Factory B', 3]
            ]);
        });

        it('should handle empty data', () => {
            const stats = dataService.getFactoryStats([]);
            expect(stats).toEqual([]);
        });
    });
});
