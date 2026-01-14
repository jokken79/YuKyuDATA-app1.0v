"""
YuKyu Premium API Tests
テスト用スクリプト - 主要APIエンドポイントの動作確認
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient


class TestBasicEndpoints:
    """基本エンドポイントのテスト"""

    def test_root_returns_html(self, client: TestClient):
        """ルートページがHTMLを返すこと"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "YuKyu" in response.text

    def test_get_employees(self, client: TestClient, auth_headers):
        """従業員リストAPIが正常に動作すること"""
        response = client.get("/api/employees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "available_years" in data
        assert isinstance(data["data"], list)

    def test_get_employees_with_year_filter(self, client: TestClient, auth_headers):
        """年度フィルターが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(f"/api/employees?year={current_year}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestGenzaiEndpoints:
    """派遣社員(Genzai)エンドポイントのテスト"""

    def test_get_genzai(self, client: TestClient, auth_headers):
        """派遣社員リストAPIが正常に動作すること"""
        response = client.get("/api/genzai", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"

    def test_get_genzai_with_status_filter(self, client: TestClient, auth_headers):
        """ステータスフィルターが正常に動作すること"""
        response = client.get("/api/genzai?status=在職中", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestUkeoiEndpoints:
    """請負社員(Ukeoi)エンドポイントのテスト"""

    def test_get_ukeoi(self, client: TestClient, auth_headers):
        """請負社員リストAPIが正常に動作すること"""
        response = client.get("/api/ukeoi", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert data["status"] == "success"


class TestLeaveRequestEndpoints:
    """休暇申請エンドポイントのテスト"""

    def test_get_leave_requests(self, client: TestClient, auth_headers):
        """休暇申請リストAPIが正常に動作すること"""
        response = client.get("/api/leave-requests", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_pending_requests(self, client: TestClient, auth_headers):
        """審査中申請のフィルターが正常に動作すること"""
        response = client.get("/api/leave-requests?status=PENDING", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_employee_search(self, client: TestClient, auth_headers):
        """従業員検索APIが正常に動作すること"""
        response = client.get("/api/employees/search?q=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


class TestComplianceEndpoints:
    """コンプライアンスエンドポイントのテスト"""

    def test_5day_compliance_check(self, client: TestClient, auth_headers):
        """5日取得義務チェックAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/compliance/5day-check/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "summary" in data

    def test_compliance_alerts(self, client: TestClient, auth_headers):
        """コンプライアンスアラートAPIが正常に動作すること"""
        response = client.get("/api/compliance/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_annual_ledger(self, client: TestClient, auth_headers):
        """年次有給休暇管理簿APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/compliance/annual-ledger/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "entries" in data


class TestCalendarEndpoints:
    """カレンダーエンドポイントのテスト"""

    def test_get_calendar_events(self, client: TestClient, auth_headers):
        """カレンダーイベントAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/calendar/events?year={current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_get_calendar_month_summary(self, client: TestClient, auth_headers):
        """月別サマリーAPIが正常に動作すること"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        response = client.get(
            f"/api/calendar/summary/{current_year}/{current_month}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "daily_summary" in data


class TestAnalyticsEndpoints:
    """分析エンドポイントのテスト"""

    def test_dashboard_analytics(self, client: TestClient, auth_headers):
        """ダッシュボード分析APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/analytics/dashboard/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "summary" in data
        assert "department_stats" in data

    def test_predictions(self, client: TestClient, auth_headers):
        """予測APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/analytics/predictions/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "predictions" in data


class TestSystemEndpoints:
    """システムエンドポイントのテスト"""

    def test_system_snapshot(self, client: TestClient, auth_headers):
        """システムスナップショットAPIが正常に動作すること"""
        response = client.get("/api/system/snapshot", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "snapshot" in data

    def test_audit_log(self, client: TestClient, auth_headers):
        """監査ログAPIが正常に動作すること"""
        response = client.get("/api/system/audit-log", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestExportEndpoints:
    """エクスポートエンドポイントのテスト"""

    def test_export_employees_excel(self, client: TestClient, auth_headers):
        """従業員データExcelエクスポートが正常に動作すること"""
        current_year = datetime.now().year
        response = client.post(
            f"/api/export/excel?export_type=employees&year={current_year}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "filename" in data

    def test_export_requests_excel(self, client: TestClient, auth_headers):
        """申請データExcelエクスポートが正常に動作すること"""
        current_year = datetime.now().year
        response = client.post(
            f"/api/export/excel?export_type=requests&year={current_year}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestYukyuUsageEndpoints:
    """有給休暇使用詳細エンドポイントのテスト"""

    def test_get_usage_details(self, client: TestClient, auth_headers):
        """使用日詳細APIが正常に動作すること"""
        response = client.get("/api/yukyu/usage-details", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data

    def test_monthly_summary(self, client: TestClient, auth_headers):
        """月別サマリーAPIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/yukyu/monthly-summary/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


class TestMonthlyReportsEndpoints:
    """月次レポート (21日〜20日) エンドポイントのテスト"""

    def test_get_monthly_report(self, client: TestClient, auth_headers):
        """月次レポートAPIが正常に動作すること"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        response = client.get(
            f"/api/reports/monthly/{current_year}/{current_month}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "report_period" in data
        assert "summary" in data
        assert "employees" in data
        assert "by_factory" in data
        assert "by_date" in data

    def test_monthly_report_period_calculation(self, client: TestClient, auth_headers):
        """月次レポートの期間計算が正しいこと (21日〜20日)"""
        response = client.get("/api/reports/monthly/2025/1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # January 2025 report should be: Dec 21, 2024 - Jan 20, 2025
        assert data["report_period"]["start_date"] == "2024-12-21"
        assert data["report_period"]["end_date"] == "2025-01-20"

    def test_get_monthly_report_list(self, client: TestClient, auth_headers):
        """年間月次レポート一覧APIが正常に動作すること"""
        current_year = datetime.now().year
        response = client.get(
            f"/api/reports/monthly-list/{current_year}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "reports" in data
        assert len(data["reports"]) == 12  # 12 months

    def test_custom_report(self, client: TestClient, auth_headers):
        """カスタム期間レポートAPIが正常に動作すること"""
        response = client.get(
            "/api/reports/custom?start_date=2025-01-16&end_date=2025-02-20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "report_period" in data
        assert "summary" in data
        assert "employees" in data
        assert data["report_period"]["start_date"] == "2025-01-16"
        assert data["report_period"]["end_date"] == "2025-02-20"
        assert data["report_period"]["days_in_period"] == 36  # 16 days in Jan + 20 days in Feb

    def test_custom_report_invalid_dates(self, client: TestClient, auth_headers):
        """カスタムレポートで終了日が開始日より前の場合エラーになること"""
        response = client.get(
            "/api/reports/custom?start_date=2025-02-20&end_date=2025-01-16",
            headers=auth_headers,
        )
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
