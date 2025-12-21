/**
 * Export Service Module
 * Proporciona funcionalidades de exportación de datos (CSV, Excel, PDF)
 * @module export-service
 */

/**
 * Clase para gestionar exportación de datos
 */
export class ExportService {
    /**
     * Exporta datos a CSV
     * @param {Array} data - Array de objetos a exportar
     * @param {string} filename - Nombre del archivo
     * @param {Array} columns - Columnas a incluir (opcional)
     */
    exportToCSV(data, filename = 'export.csv', columns = null) {
        if (!data || data.length === 0) {
            console.warn('No data to export');
            return;
        }

        // Determinar columnas
        const keys = columns || Object.keys(data[0]);

        // Crear headers
        const headers = keys.join(',');

        // Crear filas
        const rows = data.map(row => {
            return keys.map(key => {
                const value = row[key];
                // Escapar comillas y envolver en comillas si contiene coma
                const stringValue = String(value === null || value === undefined ? '' : value);
                if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
                    return `"${stringValue.replace(/"/g, '""')}"`;
                }
                return stringValue;
            }).join(',');
        });

        // Combinar headers y rows
        const csv = [headers, ...rows].join('\n');

        // Crear blob y descargar
        this._downloadFile(csv, filename, 'text/csv;charset=utf-8;');
    }

    /**
     * Exporta datos de empleados a CSV con formato específico
     * @param {Array} employees - Array de empleados
     * @param {string} filename - Nombre del archivo
     */
    exportEmployeesToCSV(employees, filename = 'employees.csv') {
        const formatted = employees.map(e => ({
            '社員番号': e.employeeNum,
            '氏名': e.name,
            '派遣先': e.haken || '-',
            'タイプ': e.employeeType === 'genzai' ? '派遣' : e.employeeType === 'ukeoi' ? '請負' : '社員',
            '付与日数': e.granted,
            '使用日数': e.used,
            '残日数': e.balance,
            '使用率': e.usageRate + '%',
            '年度': e.year
        }));

        this.exportToCSV(formatted, filename);
    }

    /**
     * Exporta tabla visible a CSV
     * @param {string} tableId - ID de la tabla
     * @param {string} filename - Nombre del archivo
     */
    exportTableToCSV(tableId, filename = 'table-export.csv') {
        const table = document.getElementById(tableId);
        if (!table) {
            console.error('Table not found:', tableId);
            return;
        }

        const rows = [];

        // Obtener headers
        const headerCells = table.querySelectorAll('thead th');
        const headers = Array.from(headerCells).map(cell => cell.textContent.trim());
        rows.push(headers.join(','));

        // Obtener filas
        const bodyRows = table.querySelectorAll('tbody tr');
        bodyRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const values = Array.from(cells).map(cell => {
                const text = cell.textContent.trim();
                // Escapar y envolver en comillas si es necesario
                if (text.includes(',') || text.includes('"')) {
                    return `"${text.replace(/"/g, '""')}"`;
                }
                return text;
            });
            rows.push(values.join(','));
        });

        const csv = rows.join('\n');
        this._downloadFile(csv, filename, 'text/csv;charset=utf-8;');
    }

    /**
     * Exporta datos a JSON
     * @param {Array|Object} data - Datos a exportar
     * @param {string} filename - Nombre del archivo
     */
    exportToJSON(data, filename = 'export.json') {
        const json = JSON.stringify(data, null, 2);
        this._downloadFile(json, filename, 'application/json;charset=utf-8;');
    }

    /**
     * Prepara datos para exportación a Excel (requiere biblioteca externa)
     * @param {Array} data - Datos a exportar
     * @param {string} sheetName - Nombre de la hoja
     * @returns {Object} - Datos formateados para Excel
     */
    prepareForExcel(data, sheetName = 'Sheet1') {
        // Nota: Esto requiere una biblioteca como SheetJS (xlsx)
        // Esta función prepara los datos, la implementación real requiere la biblioteca
        return {
            sheetName,
            data,
            note: 'Requires SheetJS library to generate Excel file'
        };
    }

    /**
     * Descarga un archivo
     * @private
     * @param {string} content - Contenido del archivo
     * @param {string} filename - Nombre del archivo
     * @param {string} mimeType - Tipo MIME
     */
    _downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';

        document.body.appendChild(link);
        link.click();

        // Cleanup
        setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        }, 100);
    }

    /**
     * Copia datos al portapapeles
     * @param {string} text - Texto a copiar
     * @returns {Promise<boolean>} - true si se copió exitosamente
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy to clipboard:', err);
            // Fallback para navegadores antiguos
            try {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                const success = document.execCommand('copy');
                document.body.removeChild(textarea);
                return success;
            } catch (fallbackErr) {
                console.error('Fallback copy failed:', fallbackErr);
                return false;
            }
        }
    }

    /**
     * Genera reporte de cumplimiento
     * @param {Array} employees - Array de empleados
     * @returns {Object} - Reporte de cumplimiento
     */
    generateComplianceReport(employees) {
        const total = employees.length;
        const compliant = employees.filter(e => e.used >= 5).length;
        const critical = employees.filter(e => e.balance <= 0).length;
        const warning = employees.filter(e => e.balance > 0 && e.balance < 3).length;
        const healthy = employees.filter(e => e.balance >= 5).length;

        const complianceRate = total > 0 ? ((compliant / total) * 100).toFixed(2) : 0;

        return {
            total,
            compliant,
            complianceRate,
            critical,
            warning,
            healthy,
            nonCompliant: total - compliant,
            categories: {
                '0日残': critical,
                '1-2日残': warning,
                '5日以上残': healthy
            }
        };
    }
}

/**
 * Instancia singleton para compatibilidad con código legacy
 */
export const exportService = new ExportService();

export default exportService;
