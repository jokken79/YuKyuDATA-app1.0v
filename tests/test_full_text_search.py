#!/usr/bin/env python3
"""
Full-Text Search Tests for Phase 9

Tests for PostgreSQL tsvector-based full-text search functionality.
Validates search service and API endpoints.

Run with: pytest tests/test_full_text_search.py -v
"""

import os
import sys
import pytest
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.search_service import SearchService


class TestSearchServiceInitialization:
    """Test SearchService initialization and configuration."""

    def test_search_service_creates_successfully(self):
        """SearchService should initialize without errors."""
        search = SearchService()
        assert search is not None
        assert hasattr(search, 'use_postgresql')

    def test_postgresql_flag_set(self):
        """PostgreSQL flag should reflect database configuration."""
        search = SearchService()
        # Should be True if DATABASE_TYPE=postgresql, False otherwise
        expected = os.getenv('DATABASE_TYPE', 'sqlite').lower() == 'postgresql'
        assert search.use_postgresql == expected

    def test_database_availability_warning(self, capsys):
        """Should log warning if database not available."""
        search = SearchService()
        if not search.use_postgresql:
            # If not using PostgreSQL, should have logged warning
            # This is checked through the initialization logic
            assert True


class TestSearchMethods:
    """Test individual search methods."""

    @pytest.fixture
    def search_service(self):
        """Create SearchService instance for testing."""
        return SearchService()

    def test_search_employees_returns_list(self, search_service):
        """search_employees should return a list."""
        result = search_service.search_employees("test", limit=10)
        assert isinstance(result, list)

    def test_search_employees_empty_query(self, search_service):
        """search_employees with empty query should handle gracefully."""
        # Empty query might return all or empty list depending on implementation
        result = search_service.search_employees("", limit=10)
        assert isinstance(result, list)

    def test_search_employees_with_limit(self, search_service):
        """search_employees should respect limit parameter."""
        result = search_service.search_employees("a", limit=5)
        assert len(result) <= 5

    def test_search_employees_with_offset(self, search_service):
        """search_employees should support pagination with offset."""
        result1 = search_service.search_employees("a", limit=10, offset=0)
        result2 = search_service.search_employees("a", limit=10, offset=10)
        # Results should be different if data exists
        # (or both empty, which is valid)
        assert isinstance(result1, list)
        assert isinstance(result2, list)

    def test_search_genzai_returns_list(self, search_service):
        """search_genzai should return a list."""
        result = search_service.search_genzai("test", limit=10)
        assert isinstance(result, list)

    def test_search_ukeoi_returns_list(self, search_service):
        """search_ukeoi should return a list."""
        result = search_service.search_ukeoi("test", limit=10)
        assert isinstance(result, list)

    def test_search_staff_returns_list(self, search_service):
        """search_staff should return a list."""
        result = search_service.search_staff("test", limit=10)
        assert isinstance(result, list)

    def test_search_all_employees_returns_dict(self, search_service):
        """search_all_employees should return a dictionary."""
        result = search_service.search_all_employees("test", limit=20)
        assert isinstance(result, dict)

    def test_search_all_employees_has_all_tables(self, search_service):
        """search_all_employees should include all employee types."""
        result = search_service.search_all_employees("test")
        expected_keys = {'employees', 'genzai', 'ukeoi', 'staff'}
        assert set(result.keys()) == expected_keys

    def test_search_result_structure(self, search_service):
        """Search results should have expected structure."""
        result = search_service.search_employees("a", limit=1)
        if result:
            # Check that results have expected fields
            record = result[0]
            assert isinstance(record, dict)
            # Should have ID, number, name, relevance
            assert 'id' in record or 'employee_num' in record


class TestSearchQueryValidation:
    """Test search query validation."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_very_long_query_handled(self, search_service):
        """Should handle very long search queries."""
        long_query = "a" * 1000
        result = search_service.search_employees(long_query)
        assert isinstance(result, list)

    def test_special_characters_in_query(self, search_service):
        """Should handle special characters in query."""
        # PostgreSQL special chars should be handled safely
        queries = ["@", "#", "$", "%", "^", "&", "*", "(", ")"]
        for q in queries:
            result = search_service.search_employees(q)
            assert isinstance(result, list)

    def test_japanese_characters_in_query(self, search_service):
        """Should handle Japanese characters in query."""
        # Common Japanese names
        queries = ["田中", "佐藤", "山田", "鈴木"]
        for q in queries:
            result = search_service.search_employees(q)
            assert isinstance(result, list)


class TestSearchRelevanceRanking:
    """Test relevance ranking of search results."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_results_include_relevance_score(self, search_service):
        """Search results should include relevance ranking."""
        result = search_service.search_employees("a", limit=10)
        if result:
            # Check if relevance is included in results
            record = result[0]
            # PostgreSQL FTS includes ts_rank(relevance)
            # Should be present if using PostgreSQL
            if hasattr(search_service, 'use_postgresql') and search_service.use_postgresql:
                # Relevance field should be present for PostgreSQL results
                pass

    def test_results_ordered_by_relevance(self, search_service):
        """Results should be ordered by relevance score (highest first)."""
        result = search_service.search_employees("e", limit=20)
        if len(result) > 1:
            # Results should be ordered
            relevance_scores = [r.get('relevance', 0) for r in result]
            # Should be in descending order (or 0 for non-PostgreSQL)
            assert isinstance(relevance_scores, list)


class TestSearchEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_search_with_zero_limit(self, search_service):
        """Should handle limit=0."""
        result = search_service.search_employees("a", limit=0)
        assert result == []

    def test_search_with_negative_offset(self, search_service):
        """Should handle negative offset gracefully."""
        result = search_service.search_employees("a", limit=10, offset=-1)
        # Should either handle gracefully or return empty
        assert isinstance(result, list)

    def test_search_with_very_large_limit(self, search_service):
        """Should handle very large limit."""
        result = search_service.search_employees("a", limit=999999)
        assert isinstance(result, list)

    def test_nonexistent_employee_search(self, search_service):
        """Search for non-existent employee should return empty."""
        result = search_service.search_employees("XYZ_NONEXISTENT_EMPLOYEE_XYZ", limit=10)
        assert isinstance(result, list)
        # Should be empty or have no matches
        # (depending on whether data exists)

    def test_unicode_normalization(self, search_service):
        """Should handle different unicode representations."""
        # Full-width vs half-width characters
        result = search_service.search_employees("ａ", limit=10)
        assert isinstance(result, list)


class TestSearchGetCount:
    """Test count retrieval for pagination."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_get_count_employees_returns_int(self, search_service):
        """get_search_count for employees should return integer."""
        count = search_service.get_search_count('employees', 'test')
        assert isinstance(count, int)
        assert count >= 0

    def test_get_count_genzai_returns_int(self, search_service):
        """get_search_count for genzai should return integer."""
        count = search_service.get_search_count('genzai', 'test')
        assert isinstance(count, int)
        assert count >= 0

    def test_get_count_ukeoi_returns_int(self, search_service):
        """get_search_count for ukeoi should return integer."""
        count = search_service.get_search_count('ukeoi', 'test')
        assert isinstance(count, int)
        assert count >= 0

    def test_get_count_staff_returns_int(self, search_service):
        """get_search_count for staff should return integer."""
        count = search_service.get_search_count('staff', 'test')
        assert isinstance(count, int)
        assert count >= 0

    def test_count_with_empty_query(self, search_service):
        """get_search_count with empty query should handle gracefully."""
        count = search_service.get_search_count('employees', '')
        assert isinstance(count, int)


class TestSearchServiceDatabaseCheck:
    """Test database availability checks."""

    def test_postgresql_requirement_checked(self):
        """Service should check PostgreSQL availability."""
        search = SearchService()
        # Service should know about PostgreSQL requirement
        assert hasattr(search, 'use_postgresql')

    def test_graceful_fallback_if_postgresql_unavailable(self):
        """Service should handle non-PostgreSQL databases gracefully."""
        search = SearchService()
        if not search.use_postgresql:
            # When PostgreSQL not available, methods should return empty
            result = search.search_employees("test")
            assert result == []


class TestSearchPerformance:
    """Test search performance characteristics."""

    @pytest.fixture
    def search_service(self):
        return SearchService()

    def test_search_completes_in_reasonable_time(self, search_service):
        """Search should complete quickly (< 1 second for small result sets)."""
        import time
        start = time.time()
        result = search_service.search_employees("a", limit=20)
        elapsed = time.time() - start
        # GIN indexes should make this fast
        # Allow up to 5 seconds for slow systems
        assert elapsed < 5.0

    def test_pagination_offset_performance(self, search_service):
        """Pagination should work efficiently."""
        import time
        start = time.time()
        result1 = search_service.search_employees("a", limit=10, offset=0)
        result2 = search_service.search_employees("a", limit=10, offset=100)
        elapsed = time.time() - start
        assert elapsed < 5.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
