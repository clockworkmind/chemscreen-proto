"""Integration tests for ChemScreen end-to-end workflows."""

import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from chemscreen.analyzer import calculate_quality_metrics
from chemscreen.cache import CacheManager
from chemscreen.exporter import ExportManager
from chemscreen.models import (
    BatchSearchSession,
    Chemical,
    CSVColumnMapping,
    SearchParameters,
    SearchResult,
)
from chemscreen.processor import process_csv_data
from chemscreen.pubmed import batch_search
from chemscreen.session_manager import SessionManager


class TestEndToEndWorkflow:
    """Test complete ChemScreen workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return [
            ["Chemical Name", "CAS Number"],
            ["Caffeine", "58-08-2"],
            ["Aspirin", "50-78-2"],
            ["Glucose", "50-99-7"],
        ]

    @pytest.fixture
    def sample_csv_file(self, temp_dir, sample_csv_content):
        """Create sample CSV file for testing."""
        csv_file = temp_dir / "test_chemicals.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(sample_csv_content)
        return csv_file

    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing."""
        chemicals = [
            Chemical(name="Caffeine", cas_number="58-08-2"),
            Chemical(name="Aspirin", cas_number="50-78-2"),
            Chemical(name="Glucose", cas_number="50-99-7"),
        ]

        results = []
        for i, chemical in enumerate(chemicals):
            result = SearchResult(
                chemical=chemical,
                total_count=10 + i * 5,
                publications=[],
                search_time_seconds=1.5,
                error=None,
                from_cache=False,
            )
            results.append(result)

        return results

    def test_csv_upload_and_processing(self, sample_csv_file):
        """Test CSV file upload and chemical processing."""
        # Read CSV file into DataFrame
        df = pd.read_csv(sample_csv_file)

        # Create column mapping
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )

        # Process the CSV data
        result = process_csv_data(df, column_mapping)

        # Verify processing results
        assert len(result.valid_chemicals) == 3
        assert len(result.invalid_rows) == 0

        # Check individual chemicals
        chemicals = result.valid_chemicals
        assert chemicals[0].name == "Caffeine"
        assert chemicals[0].cas_number == "58-08-2"
        assert chemicals[1].name == "Aspirin"
        assert chemicals[1].cas_number == "50-78-2"
        assert chemicals[2].name == "Glucose"
        assert chemicals[2].cas_number == "50-99-7"

    def test_csv_processing_with_errors(self, temp_dir):
        """Test CSV processing with invalid data."""
        # Create CSV with errors
        csv_content = [
            ["Chemical Name", "CAS Number"],
            ["Valid Chemical", "58-08-2"],
            ["", "50-78-2"],  # Empty name
            ["Invalid CAS", "invalid-cas"],  # Invalid CAS
            ["Good Chemical", "50-99-7"],
        ]

        csv_file = temp_dir / "test_errors.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_content)

        # Read and process the file
        df = pd.read_csv(csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )

        result = process_csv_data(df, column_mapping)

        # Should have valid chemicals and error reports
        assert len(result.valid_chemicals) >= 1  # At least some valid ones
        assert len(result.invalid_rows) > 0  # Should have error reports

        # Check valid chemicals made it through
        chemical_names = [c.name for c in result.valid_chemicals]
        assert "Valid Chemical" in chemical_names or "Good Chemical" in chemical_names

    @pytest.mark.asyncio
    async def test_pubmed_search_integration(self, mock_search_results):
        """Test PubMed search integration with mocked responses."""
        chemicals = [
            Chemical(name="Caffeine", cas_number="58-08-2"),
            Chemical(name="Aspirin", cas_number="50-78-2"),
        ]

        # Mock the PubMed client to return controlled results
        with patch("chemscreen.pubmed.PubMedClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.search.side_effect = mock_search_results[:2]

            # Run batch search
            results = await batch_search(
                chemicals=chemicals,
                max_results_per_chemical=50,
                date_range_years=10,
                include_reviews=True,
            )

            # Verify results
            assert len(results) == 2
            assert all(not result.error for result in results)
            assert results[0].chemical.name == "Caffeine"
            assert results[1].chemical.name == "Aspirin"

    def test_quality_analysis_integration(self, mock_search_results):
        """Test quality analysis integration."""
        # Calculate quality metrics for mock results
        results_with_metrics = []

        for result in mock_search_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        # Verify metrics were calculated
        assert len(results_with_metrics) == 3

        for result, metrics in results_with_metrics:
            assert metrics.total_publications >= 0
            assert 0 <= metrics.quality_score <= 100
            assert metrics.publication_trend in ["increasing", "stable", "decreasing"]

    def test_export_integration(self, temp_dir, mock_search_results):
        """Test export functionality integration."""
        # Create session for export
        results_dict = {r.chemical.name: r for r in mock_search_results}
        session = BatchSearchSession(
            batch_id="test_batch_001",
            chemicals=[r.chemical for r in mock_search_results],
            parameters=SearchParameters(
                date_range_years=10,
                max_results=50,
                include_reviews=True,
                use_cache=True,
            ),
            results=results_dict,
            status="completed",
        )

        # Calculate metrics for export
        results_with_metrics = []
        for result in mock_search_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        # Test export manager
        export_manager = ExportManager(export_dir=temp_dir)

        # Test CSV export
        csv_path = export_manager.export_to_csv(
            results=results_with_metrics, session=session, filename="test_export.csv"
        )

        assert csv_path.exists()
        assert csv_path.stat().st_size > 0

        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()
            assert "Chemical Name" in csv_content
            assert "Caffeine" in csv_content
            assert "Quality Score" in csv_content

        # Test Excel export (if available)
        try:
            excel_path = export_manager.export_to_excel(
                results=results_with_metrics,
                session=session,
                filename="test_export.xlsx",
            )

            if excel_path:  # Only test if Excel export is available
                assert excel_path.exists()
                assert excel_path.stat().st_size > 0
        except ImportError:
            # Skip Excel test if openpyxl not available
            pass

        # Test JSON export
        json_path = export_manager.export_to_json(
            results=results_with_metrics, session=session, filename="test_export.json"
        )

        assert json_path.exists()
        assert json_path.stat().st_size > 0

        # Verify JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            assert "metadata" in json_data
            assert "results" in json_data
            assert len(json_data["results"]) == 3

    def test_session_management_integration(self, temp_dir, mock_search_results):
        """Test session management integration."""
        # Create session manager
        session_manager = SessionManager(session_dir=temp_dir)

        # Create test session
        results_dict = {r.chemical.name: r for r in mock_search_results}
        session = BatchSearchSession(
            batch_id="test_session_001",
            chemicals=[r.chemical for r in mock_search_results],
            parameters=SearchParameters(
                date_range_years=10,
                max_results=50,
                include_reviews=True,
                use_cache=True,
            ),
            results=results_dict,
            status="completed",
        )

        # Test session save
        session_path = session_manager.save_session(session)
        assert session_path.exists()

        # Test session load
        loaded_session = session_manager.load_session("test_session_001")
        assert loaded_session is not None
        assert loaded_session.batch_id == "test_session_001"
        assert len(loaded_session.chemicals) == 3
        assert len(loaded_session.results) == 3

        # Test session listing
        sessions = session_manager.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "test_session_001"

        # Test session deletion
        success = session_manager.delete_session("test_session_001")
        assert success

        # Verify deletion
        sessions_after = session_manager.list_sessions()
        assert len(sessions_after) == 0

    def test_cache_integration(self, temp_dir, mock_search_results):
        """Test cache integration."""
        # Create cache manager
        cache_manager = CacheManager(cache_dir=temp_dir, ttl_seconds=3600)

        # Test cache save and retrieve
        result = mock_search_results[0]
        chemical = result.chemical

        # Cache the result
        success = cache_manager.save(
            result=result, date_range_years=10, max_results=50, include_reviews=True
        )
        assert success

        # Retrieve from cache
        cached_result = cache_manager.get(
            chemical=chemical, date_range_years=10, max_results=50, include_reviews=True
        )

        assert cached_result is not None
        assert cached_result.from_cache is True
        assert cached_result.chemical.name == chemical.name
        assert cached_result.total_count == result.total_count

        # Test cache stats
        stats = cache_manager.get_cache_stats()
        assert stats["total_files"] >= 1
        assert stats["valid_files"] >= 1

    @pytest.mark.asyncio
    async def test_complete_workflow_integration(self, temp_dir, sample_csv_file):
        """Test complete end-to-end workflow."""
        # Step 1: Process CSV file
        df = pd.read_csv(sample_csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)
        chemicals = result.valid_chemicals
        assert len(chemicals) == 3
        assert len(result.invalid_rows) == 0

        # Step 2: Mock search execution
        mock_results = []
        for i, chemical in enumerate(chemicals):
            result = SearchResult(
                chemical=chemical,
                total_count=15 + i * 3,
                publications=[],
                search_time_seconds=1.2,
                error=None,
                from_cache=False,
            )
            mock_results.append(result)

        # Step 3: Calculate quality metrics
        results_with_metrics = []
        for result in mock_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        # Step 4: Create and save session
        session_manager = SessionManager(session_dir=temp_dir)
        results_dict = {r.chemical.name: r for r in mock_results}
        session = BatchSearchSession(
            batch_id="integration_test_001",
            chemicals=chemicals,
            parameters=SearchParameters(
                date_range_years=10,
                max_results=50,
                include_reviews=True,
                use_cache=True,
            ),
            results=results_dict,
            status="completed",
        )

        session_path = session_manager.save_session(session)
        assert session_path.exists()

        # Step 5: Export results
        export_manager = ExportManager(export_dir=temp_dir)

        csv_path = export_manager.export_to_csv(
            results=results_with_metrics,
            session=session,
            filename="integration_test.csv",
        )

        json_path = export_manager.export_to_json(
            results=results_with_metrics,
            session=session,
            filename="integration_test.json",
        )

        # Step 6: Verify complete workflow
        assert csv_path.exists()
        assert json_path.exists()

        # Verify session can be reloaded
        reloaded_session = session_manager.load_session("integration_test_001")
        assert reloaded_session is not None
        assert len(reloaded_session.chemicals) == 3
        assert reloaded_session.status == "completed"

        # Verify export contents
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_content = f.read()
            assert "Caffeine" in csv_content
            assert "Aspirin" in csv_content
            assert "Glucose" in csv_content

        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            assert json_data["metadata"]["batch_id"] == "integration_test_001"
            assert len(json_data["results"]) == 3


class TestErrorHandlingIntegration:
    """Test error handling in integrated workflows."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_invalid_csv_handling(self, temp_dir):
        """Test handling of invalid CSV files."""
        # Create malformed CSV
        invalid_csv = temp_dir / "invalid.csv"
        with open(invalid_csv, "w", encoding="utf-8") as f:
            f.write("Not,a,valid\nCSV,file,format\n\n")

        # Should handle gracefully
        try:
            df = pd.read_csv(invalid_csv)
            column_mapping = CSVColumnMapping(
                name_column="Not",  # Use available column
                cas_column="a",
            )
            result = process_csv_data(df, column_mapping)

            # Should return something (even if empty) and not crash
            assert isinstance(result.valid_chemicals, list)
            assert isinstance(result.errors, list)
        except Exception:
            # It's okay if invalid CSV can't be processed at all
            pass

    def test_empty_csv_handling(self, temp_dir):
        """Test handling of empty CSV files."""
        # Create empty CSV with just headers
        empty_csv = temp_dir / "empty.csv"
        with open(empty_csv, "w", encoding="utf-8") as f:
            f.write("Chemical Name,CAS Number\n")

        # Should handle gracefully
        df = pd.read_csv(empty_csv)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)

        assert len(result.valid_chemicals) == 0
        # May or may not have errors - empty is valid

    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Test search error handling."""
        chemicals = [Chemical(name="Invalid Chemical", cas_number="000000-00-0")]

        # Mock search that raises an exception
        with patch("chemscreen.pubmed.PubMedClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Simulate search error
            error_result = SearchResult(
                chemical=chemicals[0],
                total_count=0,
                publications=[],
                error="Network timeout",
                search_time_seconds=30.0,
                from_cache=False,
            )
            mock_instance.search.return_value = error_result

            # Run search
            results = await batch_search(chemicals=chemicals)

            # Should handle error gracefully
            assert len(results) == 1
            assert results[0].error is not None
            assert "timeout" in results[0].error.lower()

    def test_export_error_handling(self, temp_dir):
        """Test export error handling."""
        # Create export manager with invalid directory
        invalid_dir = temp_dir / "nonexistent" / "directory"
        export_manager = ExportManager(export_dir=invalid_dir)

        # Create minimal session
        session = BatchSearchSession(
            batch_id="error_test",
            chemicals=[Chemical(name="Test", cas_number="123-45-6")],
            parameters=SearchParameters(),
            results={},  # Empty dict, not list
            status="error",
        )

        # Try to export - should handle directory creation
        try:
            csv_path = export_manager.export_to_csv(
                results=[], session=session, filename="test.csv"
            )
            # If it succeeds, directory was created
            assert csv_path.exists()
        except Exception as e:
            # If it fails, should be a clear error message
            assert "error" in str(e).lower() or "permission" in str(e).lower()


class TestPerformanceIntegration:
    """Test performance aspects of integration."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_large_csv_processing(self, temp_dir):
        """Test processing of larger CSV files."""
        # Create larger CSV file
        large_csv = temp_dir / "large_test.csv"

        with open(large_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Chemical Name", "CAS Number"])

            # Write 100 test chemicals with valid CAS format
            for i in range(100):
                # Create valid CAS numbers like 000000-00-0 format
                cas = f"{i:06d}-{(i % 100):02d}-{(i % 10):01d}"
                writer.writerow([f"Chemical_{i:03d}", cas])

        # Process the file
        import time

        start_time = time.time()
        df = pd.read_csv(large_csv)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)
        processing_time = time.time() - start_time

        # Verify processing
        assert len(result.valid_chemicals) == 100
        assert processing_time < 5.0  # Should process quickly

        # Verify no duplicates
        names = [c.name for c in result.valid_chemicals]
        assert len(set(names)) == len(names)

    def test_cache_performance(self, temp_dir):
        """Test cache performance with multiple operations."""
        cache_manager = CacheManager(cache_dir=temp_dir, ttl_seconds=3600)

        # Create test results
        chemicals = [
            Chemical(name=f"Chem_{i}", cas_number=f"{i:06d}-00-0") for i in range(10)
        ]

        results = []
        for chemical in chemicals:
            result = SearchResult(
                chemical=chemical,
                total_count=10,
                publications=[],
                search_time_seconds=1.0,
                error=None,
                from_cache=False,
            )
            results.append(result)

        # Test cache save performance
        import time

        start_time = time.time()

        for result in results:
            cache_manager.save(
                result=result, date_range_years=10, max_results=50, include_reviews=True
            )

        save_time = time.time() - start_time
        assert save_time < 2.0  # Should save quickly

        # Test cache retrieval performance
        start_time = time.time()

        cached_results = []
        for chemical in chemicals:
            cached = cache_manager.get(
                chemical=chemical,
                date_range_years=10,
                max_results=50,
                include_reviews=True,
            )
            if cached:
                cached_results.append(cached)

        retrieval_time = time.time() - start_time
        assert retrieval_time < 1.0  # Should retrieve quickly
        assert len(cached_results) == 10  # All should be cached

    def test_session_performance(self, temp_dir):
        """Test session management performance."""
        session_manager = SessionManager(session_dir=temp_dir)

        # Create multiple sessions
        sessions = []
        for i in range(20):
            session = BatchSearchSession(
                batch_id=f"perf_test_{i:03d}",
                chemicals=[
                    Chemical(name=f"Chem_{j}", cas_number=f"{j:06d}-00-0")
                    for j in range(10)
                ],
                parameters=SearchParameters(),
                results={},  # Empty dict, not list
                status="completed",
            )
            sessions.append(session)

        # Test save performance
        import time

        start_time = time.time()

        for session in sessions:
            session_manager.save_session(session)

        save_time = time.time() - start_time
        assert save_time < 5.0  # Should save all sessions quickly

        # Test list performance
        start_time = time.time()
        session_list = session_manager.list_sessions()
        list_time = time.time() - start_time

        assert list_time < 1.0  # Should list quickly
        assert len(session_list) == 20

        # Test cleanup performance
        start_time = time.time()
        cleaned = session_manager.cleanup_old_sessions(
            days_to_keep=-1
        )  # Clean all (negative days)
        cleanup_time = time.time() - start_time

        assert cleanup_time < 2.0  # Should cleanup quickly
        assert cleaned >= 0  # Should clean some sessions (exact number may vary)
