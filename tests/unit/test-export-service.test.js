import { ExportService } from '../../static/js/modules/export-service.js';

describe('ExportService', () => {
    let service;
    let originalClipboard;

    beforeEach(() => {
        document.body.innerHTML = '<div id="root"></div>';
        service = new ExportService();
        window.URL = global.URL;
        originalClipboard = navigator.clipboard;
    });

    afterEach(() => {
        navigator.clipboard = originalClipboard;
        jest.restoreAllMocks();
    });

    it('exports CSV data with escaping', () => {
        const downloadSpy = jest.spyOn(service, '_downloadFile').mockImplementation(() => {});
        service.exportToCSV([
            { name: 'Alice', note: 'Hello, "world"' },
            { name: 'Bob', note: 'Line\nbreak' }
        ], 'test.csv');

        expect(downloadSpy).toHaveBeenCalled();
        const csv = downloadSpy.mock.calls[0][0];
        expect(csv).toContain('"Hello, ""world"""');
        expect(csv).toContain('"Line\nbreak"');
    });

    it('handles empty exports and missing table', () => {
        const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
        service.exportToCSV([], 'empty.csv');
        service.exportToCSV(null, 'null.csv');
        expect(warnSpy).toHaveBeenCalled();

        const errorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        service.exportTableToCSV('missing-table', 'missing.csv');
        expect(errorSpy).toHaveBeenCalled();
    });

    it('exports CSV with custom columns and null values', () => {
        const downloadSpy = jest.spyOn(service, '_downloadFile').mockImplementation(() => {});
        service.exportToCSV(
            [{ name: null, count: 2, extra: 'skip' }],
            'custom.csv',
            ['name', 'count']
        );

        const csv = downloadSpy.mock.calls[0][0];
        expect(csv).toContain('name,count');
        expect(csv).toContain(',2');
    });

    it('exports employees with formatted fields', () => {
        const csvSpy = jest.spyOn(service, 'exportToCSV').mockImplementation(() => {});
        service.exportEmployeesToCSV([{
            employeeNum: '001',
            name: 'Test',
            haken: 'Factory',
            employeeType: 'staff',
            granted: 10,
            used: 5,
            balance: 5,
            usageRate: 50,
            year: 2024
        }, {
            employeeNum: '002',
            name: 'Gen',
            haken: 'Plant',
            employeeType: 'genzai',
            granted: 10,
            used: 5,
            balance: 5,
            usageRate: 50,
            year: 2024
        }, {
            employeeNum: '003',
            name: 'Uke',
            haken: 'Plant',
            employeeType: 'ukeoi',
            granted: 10,
            used: 5,
            balance: 5,
            usageRate: 50,
            year: 2024
        }]);

        expect(csvSpy).toHaveBeenCalled();
    });

    it('exports table to CSV', () => {
        document.body.innerHTML = `
            <table id="test-table">
                <thead><tr><th>Name</th><th>Value</th></tr></thead>
                <tbody>
                    <tr><td>Alice, Inc</td><td>1</td></tr>
                    <tr><td>Bob</td><td>2</td></tr>
                </tbody>
            </table>
        `;
        const downloadSpy = jest.spyOn(service, '_downloadFile').mockImplementation(() => {});
        service.exportTableToCSV('test-table', 'table.csv');
        expect(downloadSpy).toHaveBeenCalled();
        expect(downloadSpy.mock.calls[0][0]).toContain('"Alice, Inc",1');
    });

    it('exports JSON and prepares Excel data', () => {
        const downloadSpy = jest.spyOn(service, '_downloadFile').mockImplementation(() => {});
        service.exportToJSON({ key: 'value' }, 'data.json');
        expect(downloadSpy).toHaveBeenCalled();

        const excel = service.prepareForExcel([{ a: 1 }], 'SheetA');
        expect(excel.sheetName).toBe('SheetA');
        expect(excel.data).toHaveLength(1);

        const excelDefault = service.prepareForExcel([{ b: 2 }]);
        expect(excelDefault.sheetName).toBe('Sheet1');
    });

    it('copies to clipboard with fallback', async () => {
        navigator.clipboard = {
            writeText: jest.fn().mockResolvedValue(undefined)
        };
        expect(await service.copyToClipboard('hello')).toBe(true);

        navigator.clipboard = {
            writeText: jest.fn().mockRejectedValue(new Error('no clipboard'))
        };
        document.execCommand = jest.fn().mockReturnValue(true);
        expect(await service.copyToClipboard('fallback')).toBe(true);

        document.execCommand = jest.fn(() => {
            throw new Error('fail');
        });
        expect(await service.copyToClipboard('fail')).toBe(false);
    });

    it('generates compliance report', () => {
        const report = service.generateComplianceReport([
            { used: 5, balance: 0 },
            { used: 4, balance: 2 },
            { used: 10, balance: 6 }
        ]);

        expect(report.total).toBe(3);
        expect(report.compliant).toBe(2);
        expect(report.critical).toBe(1);
    });

    it('generates compliance report for empty data', () => {
        const report = service.generateComplianceReport([]);
        expect(report.total).toBe(0);
        expect(report.complianceRate).toBe(0);
        expect(report.nonCompliant).toBe(0);
    });

    it('downloads files and cleans up links', () => {
        jest.useFakeTimers();
        HTMLAnchorElement.prototype.click = jest.fn();

        service.exportToCSV([{ name: 'A', note: 'a,b' }], 'export.csv');
        expect(document.querySelectorAll('a').length).toBe(1);

        jest.runAllTimers();
        expect(document.querySelectorAll('a').length).toBe(0);
        jest.useRealTimers();
    });
});
