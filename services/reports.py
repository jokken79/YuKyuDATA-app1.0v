"""
Modulo de generacion de reportes PDF para YuKyuDATA-app

Funcionalidades:
- Reporte individual de empleado (historial de vacaciones)
- Reporte anual 年次有給休暇管理簿 (requerido por ley japonesa)
- Reporte mensual con resumen de uso
- Reporte de cumplimiento de 5 dias (5日取得義務)
- Reportes personalizados

Formato: PDF profesional con logo, tablas y graficos opcionales
"""

import os
import io
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sqlite3

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Directorio de reportes
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

# Directorio de assets (logo, fuentes)
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'assets')

DB_NAME = "yukyu.db"

# Intentar registrar fuentes japonesas si estan disponibles
JAPANESE_FONT_AVAILABLE = False
try:
    # Buscar fuentes japonesas comunes
    font_paths = [
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
        'C:/Windows/Fonts/msgothic.ttc',
        'C:/Windows/Fonts/meiryo.ttc',
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('JapaneseFont', font_path))
            JAPANESE_FONT_AVAILABLE = True
            break
except Exception:
    pass

# Colores corporativos
COLORS = {
    'primary': colors.HexColor('#4472C4'),
    'secondary': colors.HexColor('#6C757D'),
    'success': colors.HexColor('#28A745'),
    'warning': colors.HexColor('#FFC107'),
    'danger': colors.HexColor('#DC3545'),
    'dark': colors.HexColor('#1A1F2E'),
    'light': colors.HexColor('#F8F9FA'),
    'white': colors.white,
    'black': colors.black,
    'header_bg': colors.HexColor('#4472C4'),
    'alt_row': colors.HexColor('#F2F6FC'),
}


from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Obtiene conexion a la base de datos como context manager.

    Uso:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT ...")
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class ReportGenerator:
    """
    Generador de reportes PDF para el sistema de vacaciones.

    Uso:
        generator = ReportGenerator()
        pdf_bytes = generator.generate_employee_report('001', 2025)
    """

    def __init__(self, company_name: str = "UNS Corporation", logo_path: str = None):
        """
        Inicializa el generador de reportes.

        Args:
            company_name: Nombre de la empresa para el encabezado
            logo_path: Ruta al logo de la empresa (opcional)
        """
        self.company_name = company_name
        self.logo_path = logo_path or os.path.join(ASSETS_DIR, 'logo.png')
        self.styles = self._setup_styles()

    def _setup_styles(self) -> dict:
        """Configura estilos de parrafos para el PDF"""
        styles = getSampleStyleSheet()

        # Estilo de titulo principal
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=12*mm,
            spaceBefore=6*mm,
        ))

        # Estilo de subtitulo
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=COLORS['dark'],
            alignment=TA_LEFT,
            spaceAfter=6*mm,
            spaceBefore=8*mm,
        ))

        # Estilo de seccion
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=COLORS['primary'],
            alignment=TA_LEFT,
            spaceAfter=4*mm,
            spaceBefore=6*mm,
            borderWidth=1,
            borderColor=COLORS['primary'],
            borderPadding=2*mm,
        ))

        # Estilo de cuerpo
        styles.add(ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['dark'],
            alignment=TA_JUSTIFY,
            spaceAfter=3*mm,
        ))

        # Estilo de pie de pagina
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=COLORS['secondary'],
            alignment=TA_CENTER,
        ))

        # Estilo de tabla header
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=9,
            textColor=COLORS['white'],
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))

        # Estilo de tabla celda
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            textColor=COLORS['dark'],
            alignment=TA_LEFT,
        ))

        return styles

    def _create_header(self, title: str, subtitle: str = None) -> list:
        """Crea el encabezado del reporte con logo y titulo"""
        elements = []

        # Logo (si existe)
        if os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=30*mm, height=15*mm)
                logo.hAlign = 'LEFT'
                elements.append(logo)
            except Exception:
                pass

        # Nombre de empresa
        elements.append(Paragraph(self.company_name, self.styles['ReportTitle']))

        # Titulo del reporte
        elements.append(Paragraph(title, self.styles['ReportSubtitle']))

        # Subtitulo (opcional)
        if subtitle:
            elements.append(Paragraph(subtitle, self.styles['ReportBody']))

        # Fecha de generacion
        gen_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        elements.append(Paragraph(
            f"<font color='gray'>Generado: {gen_date}</font>",
            self.styles['Footer']
        ))

        # Linea separadora
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=COLORS['primary'],
            spaceBefore=4*mm,
            spaceAfter=6*mm
        ))

        return elements

    def _create_table(self, data: List[List], col_widths: List = None,
                      header_rows: int = 1) -> Table:
        """
        Crea una tabla con estilo profesional.

        Args:
            data: Lista de listas con los datos
            col_widths: Anchos de columnas (opcional)
            header_rows: Numero de filas de encabezado
        """
        table = Table(data, colWidths=col_widths)

        # Estilo base
        style = TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, header_rows - 1), COLORS['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, header_rows - 1), COLORS['white']),
            ('FONTNAME', (0, 0), (-1, header_rows - 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, header_rows - 1), 9),
            ('ALIGN', (0, 0), (-1, header_rows - 1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, header_rows - 1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, header_rows - 1), 6),
            ('TOPPADDING', (0, 0), (-1, header_rows - 1), 6),

            # Cuerpo
            ('FONTNAME', (0, header_rows), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, header_rows), (-1, -1), 9),
            ('ALIGN', (0, header_rows), (-1, -1), 'LEFT'),
            ('VALIGN', (0, header_rows), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, header_rows), (-1, -1), 4),
            ('TOPPADDING', (0, header_rows), (-1, -1), 4),

            # Bordes
            ('GRID', (0, 0), (-1, -1), 0.5, COLORS['secondary']),
            ('BOX', (0, 0), (-1, -1), 1, COLORS['primary']),
        ])

        # Filas alternadas
        for i in range(header_rows, len(data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), COLORS['alt_row'])

        table.setStyle(style)
        return table

    def _add_page_number(self, canvas, doc):
        """Agrega numero de pagina al pie"""
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(COLORS['secondary'])
        page_num = canvas.getPageNumber()
        text = f"Pagina {page_num}"
        canvas.drawCentredString(doc.pagesize[0] / 2, 15*mm, text)
        canvas.restoreState()

    def _get_employee_data(self, employee_num: str, year: int = None) -> Dict[str, Any]:
        """Obtiene datos de un empleado de la base de datos"""
        with get_db_connection() as conn:
            c = conn.cursor()

            # Datos basicos del empleado (de genzai, ukeoi o staff)
            # Validamos tablas permitidas para evitar SQL injection
            ALLOWED_TABLES = {'genzai', 'ukeoi', 'staff'}
            employee = None
            for table in ALLOWED_TABLES:
                c.execute(f"SELECT * FROM {table} WHERE employee_num = ?", (employee_num,))
                row = c.fetchone()
                if row:
                    employee = dict(row)
                    employee['source_table'] = table
                    break

            if not employee:
                return None

            # Datos de vacaciones por ano
            if year:
                c.execute("""
                    SELECT * FROM employees
                    WHERE employee_num = ? AND year = ?
                """, (employee_num, year))
            else:
                c.execute("""
                    SELECT * FROM employees
                    WHERE employee_num = ?
                    ORDER BY year DESC
                """, (employee_num,))

            vacation_rows = c.fetchall()
            employee['vacation_data'] = [dict(r) for r in vacation_rows]

            # Detalles de uso (fechas individuales)
            if year:
                c.execute("""
                    SELECT * FROM yukyu_usage_details
                    WHERE employee_num = ? AND year = ?
                    ORDER BY use_date
                """, (employee_num, year))
            else:
                c.execute("""
                    SELECT * FROM yukyu_usage_details
                    WHERE employee_num = ?
                    ORDER BY use_date DESC
                """, (employee_num,))

            usage_rows = c.fetchall()
            employee['usage_details'] = [dict(r) for r in usage_rows]

            return employee

    def generate_employee_report(self, employee_num: str, year: int = None) -> bytes:
        """
        Genera reporte individual de un empleado.

        Args:
            employee_num: Numero de empleado
            year: Ano fiscal (opcional, si no se especifica muestra todos)

        Returns:
            Bytes del PDF generado
        """
        employee = self._get_employee_data(employee_num, year)
        if not employee:
            raise ValueError(f"Empleado {employee_num} no encontrado")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # Encabezado
        title = "Reporte Individual de Vacaciones"
        subtitle = f"Empleado: {employee.get('name', 'N/A')} ({employee_num})"
        if year:
            subtitle += f" - Ano Fiscal {year}"
        elements.extend(self._create_header(title, subtitle))

        # Seccion: Informacion del empleado
        elements.append(Paragraph("1. Informacion del Empleado", self.styles['SectionHeader']))

        info_data = [
            ["Campo", "Valor"],
            ["Numero de empleado", employee_num],
            ["Nombre", employee.get('name', 'N/A')],
            ["Departamento/派遣先", employee.get('haken', employee.get('dispatch_name', 'N/A'))],
            ["Fecha de entrada", employee.get('hire_date', 'N/A')],
            ["Estado", employee.get('status', 'Activo')],
        ]

        info_table = self._create_table(info_data, col_widths=[50*mm, 100*mm])
        elements.append(info_table)
        elements.append(Spacer(1, 8*mm))

        # Seccion: Resumen de vacaciones
        elements.append(Paragraph("2. Resumen de Vacaciones (有給休暇)", self.styles['SectionHeader']))

        vacation_data = [["Ano", "Otorgados", "Usados", "Balance", "Tasa Uso (%)"]]

        for vac in employee.get('vacation_data', []):
            granted = vac.get('granted', 0) or 0
            used = vac.get('used', 0) or 0
            balance = vac.get('balance', granted - used)
            rate = (used / granted * 100) if granted > 0 else 0

            vacation_data.append([
                str(vac.get('year', 'N/A')),
                f"{granted:.1f}",
                f"{used:.1f}",
                f"{balance:.1f}",
                f"{rate:.1f}%"
            ])

        if len(vacation_data) > 1:
            vac_table = self._create_table(
                vacation_data,
                col_widths=[25*mm, 30*mm, 30*mm, 30*mm, 30*mm]
            )
            elements.append(vac_table)
        else:
            elements.append(Paragraph(
                "No hay datos de vacaciones registrados.",
                self.styles['ReportBody']
            ))

        elements.append(Spacer(1, 8*mm))

        # Seccion: Detalle de uso
        elements.append(Paragraph("3. Detalle de Uso de Vacaciones", self.styles['SectionHeader']))

        usage_data = [["Fecha", "Dias", "Mes", "Ano"]]

        for usage in employee.get('usage_details', [])[:50]:  # Limitar a 50 registros
            usage_data.append([
                usage.get('use_date', 'N/A'),
                f"{usage.get('days_used', 1.0):.2f}",
                str(usage.get('month', 'N/A')),
                str(usage.get('year', 'N/A'))
            ])

        if len(usage_data) > 1:
            usage_table = self._create_table(
                usage_data,
                col_widths=[40*mm, 25*mm, 25*mm, 25*mm]
            )
            elements.append(usage_table)
        else:
            elements.append(Paragraph(
                "No hay registros de uso detallados.",
                self.styles['ReportBody']
            ))

        # Construir PDF
        doc.build(elements, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.getvalue()

    def generate_annual_ledger(self, year: int) -> bytes:
        """
        Genera el reporte anual oficial 年次有給休暇管理簿 (requerido por ley).

        Este reporte cumple con los requisitos legales japoneses de
        mantenimiento de registros de vacaciones pagadas.

        Args:
            year: Ano fiscal

        Returns:
            Bytes del PDF generado
        """
        conn = get_db_connection()
        c = conn.cursor()

        # Obtener todos los empleados del ano
        c.execute("""
            SELECT
                e.*,
                COALESCE(g.hire_date, u.hire_date, s.hire_date) as hire_date,
                COALESCE(g.status, u.status, s.status) as emp_status
            FROM employees e
            LEFT JOIN genzai g ON e.employee_num = g.employee_num
            LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
            LEFT JOIN staff s ON e.employee_num = s.employee_num
            WHERE e.year = ?
            ORDER BY e.employee_num
        """, (year,))

        employees = [dict(r) for r in c.fetchall()]

        # Obtener detalles de uso
        c.execute("""
            SELECT * FROM yukyu_usage_details
            WHERE year = ?
            ORDER BY employee_num, use_date
        """, (year,))

        all_usage = {}
        for row in c.fetchall():
            emp_num = row['employee_num']
            if emp_num not in all_usage:
                all_usage[emp_num] = []
            all_usage[emp_num].append(dict(row))

        conn.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )

        elements = []

        # Encabezado
        title = f"年次有給休暇管理簿 (Registro Anual de Vacaciones Pagadas)"
        subtitle = f"Ano Fiscal: {year} (Abril {year} - Marzo {year + 1})"
        elements.extend(self._create_header(title, subtitle))

        # Informacion legal
        elements.append(Paragraph(
            "<b>Base Legal:</b> Articulo 39 de la Ley de Normas Laborales de Japon (労働基準法第39条)",
            self.styles['ReportBody']
        ))
        elements.append(Paragraph(
            "<b>Obligacion de 5 dias:</b> Empleados con 10+ dias deben usar minimo 5 dias/ano",
            self.styles['ReportBody']
        ))
        elements.append(Spacer(1, 6*mm))

        # Estadisticas generales
        total_employees = len(employees)
        total_granted = sum(e.get('granted', 0) or 0 for e in employees)
        total_used = sum(e.get('used', 0) or 0 for e in employees)
        avg_rate = (total_used / total_granted * 100) if total_granted > 0 else 0

        # Cumplimiento de 5 dias
        compliant = sum(1 for e in employees
                       if (e.get('granted', 0) or 0) >= 10 and (e.get('used', 0) or 0) >= 5)
        obligated = sum(1 for e in employees if (e.get('granted', 0) or 0) >= 10)
        compliance_rate = (compliant / obligated * 100) if obligated > 0 else 100

        stats_data = [
            ["Estadistica", "Valor"],
            ["Total Empleados", str(total_employees)],
            ["Total Dias Otorgados", f"{total_granted:.1f}"],
            ["Total Dias Usados", f"{total_used:.1f}"],
            ["Tasa de Uso Promedio", f"{avg_rate:.1f}%"],
            ["Cumplimiento 5 Dias", f"{compliant}/{obligated} ({compliance_rate:.1f}%)"],
        ]

        stats_table = self._create_table(stats_data, col_widths=[60*mm, 50*mm])
        elements.append(stats_table)
        elements.append(Spacer(1, 8*mm))

        # Tabla principal de empleados
        elements.append(Paragraph("Registro Detallado por Empleado", self.styles['SectionHeader']))

        main_data = [[
            "No.", "Empleado", "Nombre", "Fecha Entrada",
            "Otorgados", "Usados", "Balance", "Tasa %", "5日義務"
        ]]

        for i, emp in enumerate(employees, 1):
            granted = emp.get('granted', 0) or 0
            used = emp.get('used', 0) or 0
            balance = emp.get('balance', granted - used)
            rate = (used / granted * 100) if granted > 0 else 0

            # Estado de obligacion de 5 dias
            if granted >= 10:
                five_day_status = "OK" if used >= 5 else "PENDIENTE"
            else:
                five_day_status = "N/A"

            main_data.append([
                str(i),
                emp.get('employee_num', 'N/A'),
                emp.get('name', 'N/A')[:15],  # Truncar nombre largo
                emp.get('hire_date', 'N/A') or 'N/A',
                f"{granted:.1f}",
                f"{used:.1f}",
                f"{balance:.1f}",
                f"{rate:.0f}%",
                five_day_status
            ])

        col_widths = [12*mm, 25*mm, 40*mm, 28*mm, 22*mm, 22*mm, 22*mm, 20*mm, 25*mm]
        main_table = self._create_table(main_data, col_widths=col_widths)
        elements.append(main_table)

        # Firma
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph(
            f"Certificado por: ______________________ Fecha: {datetime.now().strftime('%Y-%m-%d')}",
            self.styles['ReportBody']
        ))

        # Construir PDF
        doc.build(elements, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.getvalue()

    def generate_monthly_summary(self, year: int, month: int) -> bytes:
        """
        Genera reporte mensual de uso de vacaciones.

        Args:
            year: Ano
            month: Mes (1-12)

        Returns:
            Bytes del PDF generado
        """
        conn = get_db_connection()
        c = conn.cursor()

        # Obtener uso del mes
        c.execute("""
            SELECT
                ud.employee_num,
                ud.name,
                SUM(ud.days_used) as total_days,
                COUNT(*) as num_requests
            FROM yukyu_usage_details ud
            WHERE ud.year = ? AND ud.month = ?
            GROUP BY ud.employee_num, ud.name
            ORDER BY total_days DESC
        """, (year, month))

        usage_summary = [dict(r) for r in c.fetchall()]

        # Estadisticas por departamento
        c.execute("""
            SELECT
                COALESCE(e.haken, 'Sin Asignar') as department,
                COUNT(DISTINCT ud.employee_num) as employees,
                SUM(ud.days_used) as total_days
            FROM yukyu_usage_details ud
            LEFT JOIN employees e ON ud.employee_num = e.employee_num AND e.year = ?
            WHERE ud.year = ? AND ud.month = ?
            GROUP BY e.haken
            ORDER BY total_days DESC
        """, (year, year, month))

        dept_summary = [dict(r) for r in c.fetchall()]

        conn.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # Encabezado
        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        title = f"Reporte Mensual de Vacaciones"
        subtitle = f"{month_names.get(month, 'N/A')} {year}"
        elements.extend(self._create_header(title, subtitle))

        # Resumen
        total_employees = len(usage_summary)
        total_days = sum(u.get('total_days', 0) for u in usage_summary)

        elements.append(Paragraph("Resumen del Mes", self.styles['SectionHeader']))

        summary_data = [
            ["Metrica", "Valor"],
            ["Empleados con uso de vacaciones", str(total_employees)],
            ["Total dias usados", f"{total_days:.1f}"],
            ["Promedio por empleado", f"{total_days/total_employees:.1f}" if total_employees > 0 else "0"],
        ]

        summary_table = self._create_table(summary_data, col_widths=[80*mm, 50*mm])
        elements.append(summary_table)
        elements.append(Spacer(1, 8*mm))

        # Por departamento
        if dept_summary:
            elements.append(Paragraph("Uso por Departamento/派遣先", self.styles['SectionHeader']))

            dept_data = [["Departamento", "Empleados", "Dias Usados"]]
            for dept in dept_summary:
                dept_data.append([
                    dept.get('department', 'N/A')[:25],
                    str(dept.get('employees', 0)),
                    f"{dept.get('total_days', 0):.1f}"
                ])

            dept_table = self._create_table(dept_data, col_widths=[80*mm, 30*mm, 30*mm])
            elements.append(dept_table)
            elements.append(Spacer(1, 8*mm))

        # Detalle por empleado
        elements.append(Paragraph("Detalle por Empleado", self.styles['SectionHeader']))

        detail_data = [["No.", "Empleado", "Nombre", "Dias Usados", "Solicitudes"]]

        for i, usage in enumerate(usage_summary[:50], 1):  # Limitar a 50
            detail_data.append([
                str(i),
                usage.get('employee_num', 'N/A'),
                usage.get('name', 'N/A')[:20],
                f"{usage.get('total_days', 0):.1f}",
                str(usage.get('num_requests', 0))
            ])

        if len(detail_data) > 1:
            detail_table = self._create_table(
                detail_data,
                col_widths=[15*mm, 30*mm, 55*mm, 30*mm, 25*mm]
            )
            elements.append(detail_table)
        else:
            elements.append(Paragraph(
                "No hubo uso de vacaciones en este mes.",
                self.styles['ReportBody']
            ))

        # Construir PDF
        doc.build(elements, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.getvalue()

    def generate_compliance_report(self, year: int) -> bytes:
        """
        Genera reporte de cumplimiento de la obligacion de 5 dias (5日取得義務).

        Args:
            year: Ano fiscal

        Returns:
            Bytes del PDF generado
        """
        conn = get_db_connection()
        c = conn.cursor()

        # Empleados con obligacion (10+ dias otorgados)
        c.execute("""
            SELECT
                e.employee_num,
                e.name,
                e.haken,
                e.granted,
                e.used,
                e.balance,
                COALESCE(g.hire_date, u.hire_date, s.hire_date) as hire_date
            FROM employees e
            LEFT JOIN genzai g ON e.employee_num = g.employee_num
            LEFT JOIN ukeoi u ON e.employee_num = u.employee_num
            LEFT JOIN staff s ON e.employee_num = s.employee_num
            WHERE e.year = ? AND e.granted >= 10
            ORDER BY e.used ASC
        """, (year,))

        employees = [dict(r) for r in c.fetchall()]
        conn.close()

        # Clasificar empleados
        compliant = []
        at_risk = []
        non_compliant = []

        for emp in employees:
            used = emp.get('used', 0) or 0
            if used >= 5:
                compliant.append(emp)
            elif used >= 3:
                at_risk.append(emp)
            else:
                non_compliant.append(emp)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # Encabezado
        title = "Reporte de Cumplimiento 5日取得義務"
        subtitle = f"Ano Fiscal: {year}"
        elements.extend(self._create_header(title, subtitle))

        # Explicacion
        elements.append(Paragraph(
            "<b>Obligacion Legal:</b> Segun el Art. 39 de la Ley de Normas Laborales, "
            "los empleados con 10 o mas dias de vacaciones anuales deben usar al menos 5 dias. "
            "El empleador tiene la obligacion de garantizar este uso.",
            self.styles['ReportBody']
        ))
        elements.append(Spacer(1, 6*mm))

        # Resumen
        total = len(employees)
        compliance_rate = (len(compliant) / total * 100) if total > 0 else 100

        summary_data = [
            ["Estado", "Cantidad", "Porcentaje"],
            ["Cumple (5+ dias)", str(len(compliant)), f"{len(compliant)/total*100:.1f}%" if total > 0 else "N/A"],
            ["En Riesgo (3-4.9 dias)", str(len(at_risk)), f"{len(at_risk)/total*100:.1f}%" if total > 0 else "N/A"],
            ["No Cumple (<3 dias)", str(len(non_compliant)), f"{len(non_compliant)/total*100:.1f}%" if total > 0 else "N/A"],
            ["TOTAL con Obligacion", str(total), "100%"],
        ]

        summary_table = self._create_table(summary_data, col_widths=[60*mm, 40*mm, 40*mm])
        elements.append(summary_table)
        elements.append(Spacer(1, 8*mm))

        # Tasa de cumplimiento destacada
        status_color = "green" if compliance_rate >= 80 else ("orange" if compliance_rate >= 50 else "red")
        elements.append(Paragraph(
            f"<font size='14' color='{status_color}'><b>Tasa de Cumplimiento: {compliance_rate:.1f}%</b></font>",
            self.styles['ReportBody']
        ))
        elements.append(Spacer(1, 10*mm))

        # Lista de no cumplimiento (prioridad)
        if non_compliant:
            elements.append(Paragraph(
                "<font color='red'><b>ATENCION: Empleados que NO cumplen</b></font>",
                self.styles['SectionHeader']
            ))

            nc_data = [["No.", "Empleado", "Nombre", "Departamento", "Usado", "Faltante"]]
            for i, emp in enumerate(non_compliant, 1):
                used = emp.get('used', 0) or 0
                nc_data.append([
                    str(i),
                    emp.get('employee_num', 'N/A'),
                    emp.get('name', 'N/A')[:15],
                    emp.get('haken', 'N/A')[:15] if emp.get('haken') else 'N/A',
                    f"{used:.1f}",
                    f"{5 - used:.1f}"
                ])

            nc_table = self._create_table(
                nc_data,
                col_widths=[12*mm, 25*mm, 40*mm, 40*mm, 20*mm, 20*mm]
            )
            elements.append(nc_table)
            elements.append(Spacer(1, 8*mm))

        # Lista de en riesgo
        if at_risk:
            elements.append(Paragraph(
                "<font color='orange'><b>En Riesgo: Requieren atencion</b></font>",
                self.styles['SectionHeader']
            ))

            ar_data = [["No.", "Empleado", "Nombre", "Departamento", "Usado", "Faltante"]]
            for i, emp in enumerate(at_risk, 1):
                used = emp.get('used', 0) or 0
                ar_data.append([
                    str(i),
                    emp.get('employee_num', 'N/A'),
                    emp.get('name', 'N/A')[:15],
                    emp.get('haken', 'N/A')[:15] if emp.get('haken') else 'N/A',
                    f"{used:.1f}",
                    f"{5 - used:.1f}"
                ])

            ar_table = self._create_table(
                ar_data,
                col_widths=[12*mm, 25*mm, 40*mm, 40*mm, 20*mm, 20*mm]
            )
            elements.append(ar_table)

        # Construir PDF
        doc.build(elements, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.getvalue()

    def generate_custom_report(self, config: Dict[str, Any]) -> bytes:
        """
        Genera un reporte personalizado basado en configuracion.

        Args:
            config: Diccionario con configuracion:
                - title: Titulo del reporte
                - filters: Filtros a aplicar (year, department, status, etc.)
                - columns: Columnas a incluir
                - sort_by: Campo de ordenacion
                - include_stats: Incluir estadisticas
                - include_charts: Incluir graficos

        Returns:
            Bytes del PDF generado
        """
        conn = get_db_connection()
        c = conn.cursor()

        # Construir query segun filtros
        filters = config.get('filters', {})
        year = filters.get('year')
        department = filters.get('department')
        min_balance = filters.get('min_balance')
        max_balance = filters.get('max_balance')
        status = filters.get('status')

        query = """
            SELECT
                e.employee_num,
                e.name,
                e.haken,
                e.granted,
                e.used,
                e.balance,
                e.usage_rate,
                e.year
            FROM employees e
            WHERE 1=1
        """
        params = []

        if year:
            query += " AND e.year = ?"
            params.append(year)
        if department:
            query += " AND e.haken LIKE ?"
            params.append(f"%{department}%")
        if min_balance is not None:
            query += " AND e.balance >= ?"
            params.append(min_balance)
        if max_balance is not None:
            query += " AND e.balance <= ?"
            params.append(max_balance)

        sort_by = config.get('sort_by', 'employee_num')
        query += f" ORDER BY e.{sort_by}"

        c.execute(query, params)
        employees = [dict(r) for r in c.fetchall()]
        conn.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=25*mm
        )

        elements = []

        # Encabezado
        title = config.get('title', 'Reporte Personalizado')
        subtitle = f"Filtros aplicados: {len(filters)} | Registros: {len(employees)}"
        elements.extend(self._create_header(title, subtitle))

        # Estadisticas (si se solicitan)
        if config.get('include_stats', True):
            elements.append(Paragraph("Estadisticas", self.styles['SectionHeader']))

            total = len(employees)
            total_granted = sum(e.get('granted', 0) or 0 for e in employees)
            total_used = sum(e.get('used', 0) or 0 for e in employees)
            avg_balance = sum(e.get('balance', 0) or 0 for e in employees) / total if total > 0 else 0

            stats_data = [
                ["Metrica", "Valor"],
                ["Total Empleados", str(total)],
                ["Total Dias Otorgados", f"{total_granted:.1f}"],
                ["Total Dias Usados", f"{total_used:.1f}"],
                ["Balance Promedio", f"{avg_balance:.1f}"],
            ]

            stats_table = self._create_table(stats_data, col_widths=[70*mm, 50*mm])
            elements.append(stats_table)
            elements.append(Spacer(1, 8*mm))

        # Tabla de datos
        columns = config.get('columns', ['employee_num', 'name', 'granted', 'used', 'balance'])

        column_labels = {
            'employee_num': 'No. Empleado',
            'name': 'Nombre',
            'haken': 'Departamento',
            'granted': 'Otorgados',
            'used': 'Usados',
            'balance': 'Balance',
            'usage_rate': 'Tasa %',
            'year': 'Ano'
        }

        header_row = [column_labels.get(col, col) for col in columns]
        table_data = [header_row]

        for emp in employees[:100]:  # Limitar a 100 registros
            row = []
            for col in columns:
                val = emp.get(col, '')
                if col in ['granted', 'used', 'balance']:
                    row.append(f"{val:.1f}" if val else '0.0')
                elif col == 'usage_rate':
                    row.append(f"{val:.1f}%" if val else '0%')
                else:
                    row.append(str(val)[:20] if val else 'N/A')
            table_data.append(row)

        if len(table_data) > 1:
            col_widths = [170*mm // len(columns)] * len(columns)
            data_table = self._create_table(table_data, col_widths=col_widths)
            elements.append(data_table)
        else:
            elements.append(Paragraph(
                "No se encontraron registros con los filtros especificados.",
                self.styles['ReportBody']
            ))

        # Construir PDF
        doc.build(elements, onFirstPage=self._add_page_number,
                  onLaterPages=self._add_page_number)

        buffer.seek(0)
        return buffer.getvalue()


def save_report(pdf_bytes: bytes, filename: str) -> str:
    """
    Guarda el reporte PDF en el directorio de reportes.

    Args:
        pdf_bytes: Bytes del PDF
        filename: Nombre del archivo (sin extension)

    Returns:
        Ruta completa del archivo guardado
    """
    filepath = os.path.join(REPORTS_DIR, f"{filename}.pdf")
    with open(filepath, 'wb') as f:
        f.write(pdf_bytes)
    return filepath


def list_reports() -> List[Dict[str, Any]]:
    """
    Lista todos los reportes generados.

    Returns:
        Lista de diccionarios con informacion de los reportes
    """
    reports = []
    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.pdf'):
            filepath = os.path.join(REPORTS_DIR, filename)
            stat = os.stat(filepath)
            reports.append({
                'filename': filename,
                'size_kb': round(stat.st_size / 1024, 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    return sorted(reports, key=lambda x: x['modified'], reverse=True)


def cleanup_old_reports(days: int = 30) -> int:
    """
    Elimina reportes mas antiguos que X dias.

    Args:
        days: Dias de antiguedad para eliminar

    Returns:
        Numero de archivos eliminados
    """
    import time

    cutoff = time.time() - (days * 86400)
    deleted = 0

    for filename in os.listdir(REPORTS_DIR):
        if filename.endswith('.pdf'):
            filepath = os.path.join(REPORTS_DIR, filename)
            if os.stat(filepath).st_mtime < cutoff:
                os.remove(filepath)
                deleted += 1

    return deleted
