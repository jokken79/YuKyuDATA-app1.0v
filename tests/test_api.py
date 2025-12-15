"""
YuKyu Premium API Tests
テスト用スクリプト - 主要APIエンドポイントの動作確認
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


class TestBasicEndpoints:
    """基本エンドポイントのテスト"""

    def test_root_returns_html(self):
        """ルートページがHTMLを返すこと"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "YuKyu" in response.text

    def test_get_employees(self):
        """従業員リストAPIが正常に動作すること"""
        response = client.get("/api/employees")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "available_years" in data
        assert isinstance(data["data"], list)

    def test_get_employees_with_year_filter(self):
        """年度フィルターが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/employees?year={current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestGenzaiEndpoints:
    """派遣社員(Genzai)エンドポイントのテスト"""

    def test_get_genzai(self):
        """派遣社員リストAPIが正常に動作すること"""
        response = client.get("/api/genzai")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"

    def test_get_genzai_with_status_filter(self):
        """ステータスフィルターが正常に動作すること"""
        response = client.get("/api/genzai?status=在職中")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestUkeoiEndpoints:
    """請負社員(Ukeoi)エンドポイントのテスト"""

    def test_get_ukeoi(self):
        """請負社員リストAPIが正常に動作すること"""
        response = client.get("/api/ukeoi")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"


class TestLeaveRequestEndpoints:
    """休暇申請エンドポイントのテスト"""

    def test_get_leave_requests(self):
        """休暇申請リストAPIが正常に動作すること"""
        response = client.get("/api/leave-requests")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_pending_requests(self):
        """審査中申請のフィルターが正常に動作すること"""
        response = client.get("/api/leave-requests?status=PENDING")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_employee_search(self):
        """従業員検索APIが正常に動作すること"""
        response = client.get("/api/employees/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


class TestComplianceEndpoints:
    """コンプライアンスエンドポイントのテスト"""

    def test_5day_compliance_check(self):
        """5日取得義務チェックAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/compliance/5day-check/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "summary" in data

    def test_compliance_alerts(self):
        """コンプライアンスアラートAPIが正常に動作すること"""
        response = client.get("/api/compliance/alerts")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_annual_ledger(self):
        """年次有給休暇管理簿APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/compliance/annual-ledger/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "entries" in data


class TestCalendarEndpoints:
    """カレンダーエンドポイントのテスト"""

    def test_get_calendar_events(self):
        """カレンダーイベントAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/calendar/events?year={current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_get_calendar_month_summary(self):
        """月別サマリーAPIが正常に動作すること"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        response = client.get(f"/api/calendar/summary/{current_year}/{current_month}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "daily_summary" in data


class TestAnalyticsEndpoints:
    """分析エンドポイントのテスト"""

    def test_dashboard_analytics(self):
        """ダッシュボード分析APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/analytics/dashboard/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "summary" in data
        assert "department_stats" in data

    def test_predictions(self):
        """予測APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/analytics/predictions/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "predictions" in data


class TestSystemEndpoints:
    """システムエンドポイントのテスト"""

    def test_system_snapshot(self):
        """システムスナップショットAPIが正常に動作すること"""
        response = client.get("/api/system/snapshot")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "snapshot" in data

    def test_audit_log(self):
        """監査ログAPIが正常に動作すること"""
        response = client.get("/api/system/audit-log")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestExportEndpoints:
    """エクスポートエンドポイントのテスト"""

    def test_export_employees_excel(self):
        """従業員データExcelエクスポートが正常に動作すること"""
        current_year = datetime.now().year
        response = client.post(f"/api/export/excel?export_type=employees&year={current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "filename" in data

    def test_export_requests_excel(self):
        """申請データExcelエクスポートが正常に動作すること"""
        current_year = datetime.now().year
        response = client.post(f"/api/export/excel?export_type=requests&year={current_year}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestYukyuUsageEndpoints:
    """有給休暇使用詳細エンドポイントのテスト"""

    def test_get_usage_details(self):
        """使用日詳細APIが正常に動作すること"""
        response = client.get("/api/yukyu/usage-details")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data

    def test_monthly_summary(self):
        """月別サマリーAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/yukyu/monthly-summary/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


class TestMonthlyReportsEndpoints:
    """月次レポート (21日〜20日) エンドポイントのテスト"""

    def test_get_monthly_report(self):
        """月次レポートAPIが正常に動作すること"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        response = client.get(f"/api/reports/monthly/{current_year}/{current_month}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "report_period" in data
        assert "summary" in data
        assert "employees" in data
        assert "by_factory" in data
        assert "by_date" in data

    def test_monthly_report_period_calculation(self):
        """月次レポートの期間計算が正しいこと (21日〜20日)"""
        response = client.get("/api/reports/monthly/2025/1")
        assert response.status_code == 200
        data = response.json()
        # January 2025 report should be: Dec 21, 2024 - Jan 20, 2025
        assert data["report_period"]["start_date"] == "2024-12-21"
        assert data["report_period"]["end_date"] == "2025-01-20"

    def test_get_monthly_report_list(self):
        """年間月次レポート一覧APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/reports/monthly-list/{current_year}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "reports" in data
        assert len(data["reports"]) == 12  # 12 months


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
