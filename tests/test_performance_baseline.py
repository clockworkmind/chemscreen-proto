"""Performance baseline tests for ChemScreen.

These tests establish performance baselines and validate that the system
meets the expected performance requirements for different batch sizes.
"""

import csv
import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import psutil
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
from chemscreen.session_manager import SessionManager


class PerformanceMonitor:
    """Helper class to monitor performance metrics."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_memory = None

    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def stop(self) -> dict[str, float]:
        """Stop monitoring and return metrics."""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        return {
            "execution_time_seconds": end_time - self.start_time,
            "memory_usage_mb": end_memory,
            "memory_delta_mb": end_memory - self.start_memory,
            "peak_memory_mb": self.process.memory_info().rss / 1024 / 1024,
        }


class TestPerformanceBaselines:
    """Establish performance baselines for ChemScreen operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def performance_monitor(self):
        """Provide performance monitoring."""
        return PerformanceMonitor()

    def create_test_csv(self, temp_dir: Path, num_chemicals: int, filename: str) -> Path:
        """Create test CSV file with specified number of chemicals."""
        csv_file = temp_dir / filename

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Chemical Name", "CAS Number"])

            # Use known chemicals for small batches, generated for large
            known_chemicals = [
                ("Caffeine", "58-08-2"),
                ("Aspirin", "50-78-2"),
                ("Glucose", "50-99-7"),
                ("Ethanol", "64-17-5"),
                ("Water", "7732-18-5"),
                ("Sodium chloride", "7647-14-5"),
                ("Carbon dioxide", "124-38-9"),
                ("Oxygen", "7782-44-7"),
                ("Nitrogen", "7727-37-9"),
                ("Methane", "74-82-8"),
            ]

            for i in range(num_chemicals):
                if i < len(known_chemicals):
                    writer.writerow(known_chemicals[i])
                else:
                    # Generate valid CAS numbers
                    cas = f"{i:06d}-{(i % 100):02d}-{(i % 10):01d}"
                    writer.writerow([f"Test_Chemical_{i:03d}", cas])

        return csv_file

    def test_csv_processing_baseline_small(self, temp_dir, performance_monitor):
        """Baseline: CSV processing for 10 chemicals."""
        # Create test data
        csv_file = self.create_test_csv(temp_dir, 10, "small_batch.csv")

        # Monitor performance
        performance_monitor.start()

        # Process CSV
        df = pd.read_csv(csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)

        metrics = performance_monitor.stop()

        # Validate results
        assert len(result.valid_chemicals) == 10

        # Performance assertions
        assert metrics["execution_time_seconds"] < 1.0, (
            f"CSV processing took {metrics['execution_time_seconds']:.2f}s (expected <1.0s)"
        )
        assert metrics["memory_delta_mb"] < 10, (
            f"Memory delta {metrics['memory_delta_mb']:.1f}MB (expected <10MB)"
        )

        print("\n📊 CSV Processing (10 chemicals):")
        print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
        print(
            f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB (Δ{metrics['memory_delta_mb']:.1f}MB)"
        )

    def test_csv_processing_baseline_medium(self, temp_dir, performance_monitor):
        """Baseline: CSV processing for 50 chemicals."""
        csv_file = self.create_test_csv(temp_dir, 50, "medium_batch.csv")

        performance_monitor.start()

        df = pd.read_csv(csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)

        metrics = performance_monitor.stop()

        assert len(result.valid_chemicals) == 50
        assert metrics["execution_time_seconds"] < 2.0, (
            f"CSV processing took {metrics['execution_time_seconds']:.2f}s (expected <2.0s)"
        )
        assert metrics["memory_delta_mb"] < 25, (
            f"Memory delta {metrics['memory_delta_mb']:.1f}MB (expected <25MB)"
        )

        print("\n📊 CSV Processing (50 chemicals):")
        print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
        print(
            f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB (Δ{metrics['memory_delta_mb']:.1f}MB)"
        )

    def test_csv_processing_baseline_large(self, temp_dir, performance_monitor):
        """Baseline: CSV processing for 100 chemicals."""
        csv_file = self.create_test_csv(temp_dir, 100, "large_batch.csv")

        performance_monitor.start()

        df = pd.read_csv(csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)

        metrics = performance_monitor.stop()

        assert len(result.valid_chemicals) == 100
        assert metrics["execution_time_seconds"] < 5.0, (
            f"CSV processing took {metrics['execution_time_seconds']:.2f}s (expected <5.0s)"
        )
        assert metrics["memory_delta_mb"] < 50, (
            f"Memory delta {metrics['memory_delta_mb']:.1f}MB (expected <50MB)"
        )

        print("\n📊 CSV Processing (100 chemicals):")
        print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
        print(
            f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB (Δ{metrics['memory_delta_mb']:.1f}MB)"
        )

    def test_quality_analysis_baseline(self, performance_monitor):
        """Baseline: Quality analysis for batch results."""
        # Create mock results
        chemicals = [
            Chemical(name=f"Chemical_{i}", cas_number=f"{i:06d}-00-0") for i in range(50)
        ]

        mock_results = []
        for i, chemical in enumerate(chemicals):
            result = SearchResult(
                chemical=chemical,
                total_count=15 + (i % 20),  # Vary the counts
                publications=[],  # Empty for speed
                search_time_seconds=1.0,
                error=None,
                from_cache=False,
            )
            mock_results.append(result)

        performance_monitor.start()

        # Calculate quality metrics for all results
        results_with_metrics = []
        for result in mock_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        perf_metrics = performance_monitor.stop()

        assert len(results_with_metrics) == 50
        assert perf_metrics["execution_time_seconds"] < 1.0, (
            f"Quality analysis took {perf_metrics['execution_time_seconds']:.2f}s (expected <1.0s)"
        )

        print("\n📊 Quality Analysis (50 chemicals):")
        print(f"   ⏱️  Time: {perf_metrics['execution_time_seconds']:.3f}s")
        print(
            f"   💾 Memory: {perf_metrics['memory_usage_mb']:.1f}MB (Δ{perf_metrics['memory_delta_mb']:.1f}MB)"
        )

    def test_cache_operations_baseline(self, temp_dir, performance_monitor):
        """Baseline: Cache save/retrieve operations."""
        cache_manager = CacheManager(cache_dir=temp_dir, ttl_seconds=3600)

        # Create test data
        chemicals = [
            Chemical(name=f"Chemical_{i}", cas_number=f"{i:06d}-00-0") for i in range(20)
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
        performance_monitor.start()

        for result in results:
            cache_manager.save(
                result=result, date_range_years=10, max_results=50, include_reviews=True
            )

        save_metrics = performance_monitor.stop()

        # Test cache retrieve performance
        performance_monitor.start()

        retrieved_count = 0
        for chemical in chemicals:
            cached = cache_manager.get(
                chemical=chemical,
                date_range_years=10,
                max_results=50,
                include_reviews=True,
            )
            if cached:
                retrieved_count += 1

        retrieve_metrics = performance_monitor.stop()

        assert retrieved_count == 20
        assert save_metrics["execution_time_seconds"] < 2.0, (
            f"Cache save took {save_metrics['execution_time_seconds']:.2f}s (expected <2.0s)"
        )
        assert retrieve_metrics["execution_time_seconds"] < 1.0, (
            f"Cache retrieve took {retrieve_metrics['execution_time_seconds']:.2f}s (expected <1.0s)"
        )

        print("\n📊 Cache Operations (20 items):")
        print(f"   ⏱️  Save: {save_metrics['execution_time_seconds']:.3f}s")
        print(f"   ⏱️  Retrieve: {retrieve_metrics['execution_time_seconds']:.3f}s")
        print(f"   💾 Memory: {retrieve_metrics['memory_usage_mb']:.1f}MB")

    def test_export_baseline_csv(self, temp_dir, performance_monitor):
        """Baseline: CSV export performance."""
        # Create test session and results
        chemicals = [
            Chemical(name=f"Chemical_{i}", cas_number=f"{i:06d}-00-0") for i in range(50)
        ]

        mock_results = []
        for chemical in chemicals:
            result = SearchResult(
                chemical=chemical,
                total_count=15,
                publications=[],
                search_time_seconds=1.0,
                error=None,
                from_cache=False,
            )
            mock_results.append(result)

        # Calculate metrics
        results_with_metrics = []
        for result in mock_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        # Create session
        results_dict = {r.chemical.name: r for r in mock_results}
        session = BatchSearchSession(
            batch_id="perf_test_export",
            chemicals=chemicals,
            parameters=SearchParameters(),
            results=results_dict,
            status="completed",
        )

        # Test export performance
        export_manager = ExportManager(export_dir=temp_dir)

        performance_monitor.start()

        csv_path = export_manager.export_to_csv(
            results=results_with_metrics, session=session, filename="perf_test.csv"
        )

        metrics = performance_monitor.stop()

        assert csv_path.exists()
        assert csv_path.stat().st_size > 0
        assert metrics["execution_time_seconds"] < 5.0, (
            f"CSV export took {metrics['execution_time_seconds']:.2f}s (expected <5.0s)"
        )

        print("\n📊 CSV Export (50 chemicals):")
        print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
        print(f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB")
        print(f"   📄 Size: {csv_path.stat().st_size / 1024:.1f}KB")

    def test_export_baseline_excel(self, temp_dir, performance_monitor):
        """Baseline: Excel export performance."""
        # Create test data (smaller for Excel due to complexity)
        chemicals = [
            Chemical(name=f"Chemical_{i}", cas_number=f"{i:06d}-00-0") for i in range(25)
        ]

        mock_results = []
        for chemical in chemicals:
            result = SearchResult(
                chemical=chemical,
                total_count=15,
                publications=[],
                search_time_seconds=1.0,
                error=None,
                from_cache=False,
            )
            mock_results.append(result)

        results_with_metrics = []
        for result in mock_results:
            metrics = calculate_quality_metrics(result)
            results_with_metrics.append((result, metrics))

        results_dict = {r.chemical.name: r for r in mock_results}
        session = BatchSearchSession(
            batch_id="perf_test_excel",
            chemicals=chemicals,
            parameters=SearchParameters(),
            results=results_dict,
            status="completed",
        )

        export_manager = ExportManager(export_dir=temp_dir)

        performance_monitor.start()

        excel_path = export_manager.export_to_excel(
            results=results_with_metrics, session=session, filename="perf_test.xlsx"
        )

        metrics = performance_monitor.stop()

        if excel_path:  # Only test if Excel export is available
            assert excel_path.exists()
            assert excel_path.stat().st_size > 0
            assert metrics["execution_time_seconds"] < 10.0, (
                f"Excel export took {metrics['execution_time_seconds']:.2f}s (expected <10.0s)"
            )

            print("\n📊 Excel Export (25 chemicals):")
            print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
            print(f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB")
            print(f"   📄 Size: {excel_path.stat().st_size / 1024:.1f}KB")
        else:
            print("\n📊 Excel Export: Skipped (openpyxl not available)")

    def test_session_management_baseline(self, temp_dir, performance_monitor):
        """Baseline: Session save/load performance."""
        session_manager = SessionManager(session_dir=temp_dir)

        # Create test sessions
        sessions = []
        for i in range(10):
            chemicals = [
                Chemical(name=f"Chem_{j}", cas_number=f"{j:06d}-00-0") for j in range(10)
            ]
            session = BatchSearchSession(
                batch_id=f"perf_session_{i:03d}",
                chemicals=chemicals,
                parameters=SearchParameters(),
                results={},
                status="completed",
            )
            sessions.append(session)

        # Test save performance
        performance_monitor.start()

        for session in sessions:
            session_manager.save_session(session)

        save_metrics = performance_monitor.stop()

        # Test load performance
        performance_monitor.start()

        loaded_sessions = []
        for session in sessions:
            loaded = session_manager.load_session(session.batch_id)
            if loaded:
                loaded_sessions.append(loaded)

        load_metrics = performance_monitor.stop()

        assert len(loaded_sessions) == 10
        assert save_metrics["execution_time_seconds"] < 3.0, (
            f"Session save took {save_metrics['execution_time_seconds']:.2f}s (expected <3.0s)"
        )
        assert load_metrics["execution_time_seconds"] < 2.0, (
            f"Session load took {load_metrics['execution_time_seconds']:.2f}s (expected <2.0s)"
        )

        print("\n📊 Session Management (10 sessions):")
        print(f"   ⏱️  Save: {save_metrics['execution_time_seconds']:.3f}s")
        print(f"   ⏱️  Load: {load_metrics['execution_time_seconds']:.3f}s")
        print(f"   💾 Memory: {load_metrics['memory_usage_mb']:.1f}MB")

    def test_memory_usage_baseline(self, temp_dir, performance_monitor):
        """Baseline: Memory usage with large dataset."""
        # Create large dataset
        csv_file = self.create_test_csv(temp_dir, 200, "memory_test.csv")

        performance_monitor.start()

        # Process large CSV
        df = pd.read_csv(csv_file)
        column_mapping = CSVColumnMapping(
            name_column="Chemical Name", cas_column="CAS Number"
        )
        result = process_csv_data(df, column_mapping)

        # Create mock results
        mock_results = []
        for chemical in result.valid_chemicals:
            search_result = SearchResult(
                chemical=chemical,
                total_count=10,
                publications=[],
                search_time_seconds=1.0,
                error=None,
                from_cache=False,
            )
            mock_results.append(search_result)

        # Calculate metrics
        results_with_metrics = []
        for search_result in mock_results:
            metrics = calculate_quality_metrics(search_result)
            results_with_metrics.append((search_result, metrics))

        # Create session
        results_dict = {r.chemical.name: r for r in mock_results}
        session = BatchSearchSession(
            batch_id="memory_test",
            chemicals=result.valid_chemicals,
            parameters=SearchParameters(),
            results=results_dict,
            status="completed",
        )

        # Save session
        session_manager = SessionManager(session_dir=temp_dir)
        session_manager.save_session(session)

        # Export results
        export_manager = ExportManager(export_dir=temp_dir)
        export_manager.export_to_csv(
            results=results_with_metrics, session=session, filename="memory_test.csv"
        )

        metrics = performance_monitor.stop()

        assert len(result.valid_chemicals) == 200
        assert metrics["memory_usage_mb"] < 512, (
            f"Memory usage {metrics['memory_usage_mb']:.1f}MB (expected <512MB)"
        )
        assert metrics["execution_time_seconds"] < 30.0, (
            f"Full processing took {metrics['execution_time_seconds']:.2f}s (expected <30.0s)"
        )

        print("\n📊 Memory Usage Test (200 chemicals):")
        print(f"   ⏱️  Time: {metrics['execution_time_seconds']:.3f}s")
        print(
            f"   💾 Memory: {metrics['memory_usage_mb']:.1f}MB (Δ{metrics['memory_delta_mb']:.1f}MB)"
        )
        print("   🎯 Target: <512MB")


class TestPerformanceRegression:
    """Test for performance regressions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    def test_no_memory_leaks(self, temp_dir):
        """Test that repeated operations don't leak memory."""
        process = psutil.Process(os.getpid())

        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Perform repeated operations
        for i in range(10):
            # Create and process small CSV
            chemicals = [
                Chemical(name=f"Chemical_{j}", cas_number=f"{j:06d}-00-0")
                for j in range(5)
            ]

            # Quality analysis
            for chemical in chemicals:
                result = SearchResult(
                    chemical=chemical,
                    total_count=10,
                    publications=[],
                    search_time_seconds=1.0,
                    error=None,
                    from_cache=False,
                )
                calculate_quality_metrics(result)

            # Cache operations
            cache_manager = CacheManager(cache_dir=temp_dir, ttl_seconds=3600)
            for chemical in chemicals:
                result = SearchResult(
                    chemical=chemical,
                    total_count=10,
                    publications=[],
                    search_time_seconds=1.0,
                    error=None,
                    from_cache=False,
                )
                cache_manager.save(result, 10, 50, True)
                cache_manager.get(chemical, 10, 50, True)

        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - baseline_memory

        assert memory_growth < 50, (
            f"Memory grew by {memory_growth:.1f}MB (expected <50MB)"
        )

        print("\n📊 Memory Leak Test:")
        print(f"   📊 Baseline: {baseline_memory:.1f}MB")
        print(f"   📊 Final: {final_memory:.1f}MB")
        print(f"   📈 Growth: {memory_growth:.1f}MB")

    def test_concurrent_operations_performance(self, temp_dir):
        """Test performance under concurrent-like load."""
        process = psutil.Process(os.getpid())
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024

        # Simulate concurrent operations
        cache_manager = CacheManager(cache_dir=temp_dir, ttl_seconds=3600)
        session_manager = SessionManager(session_dir=temp_dir)
        export_manager = ExportManager(export_dir=temp_dir)

        # Create multiple batches simultaneously
        for batch_num in range(5):
            chemicals = [
                Chemical(name=f"Batch{batch_num}_Chem_{i}", cas_number=f"{i:06d}-00-0")
                for i in range(10)
            ]

            mock_results = []
            for chemical in chemicals:
                result = SearchResult(
                    chemical=chemical,
                    total_count=15,
                    publications=[],
                    search_time_seconds=1.0,
                    error=None,
                    from_cache=False,
                )
                mock_results.append(result)

                # Cache each result
                cache_manager.save(result, 10, 50, True)

            # Create session
            results_dict = {r.chemical.name: r for r in mock_results}
            session = BatchSearchSession(
                batch_id=f"concurrent_batch_{batch_num}",
                chemicals=chemicals,
                parameters=SearchParameters(),
                results=results_dict,
                status="completed",
            )

            # Save session
            session_manager.save_session(session)

            # Export results
            results_with_metrics = []
            for result in mock_results:
                metrics = calculate_quality_metrics(result)
                results_with_metrics.append((result, metrics))

            export_manager.export_to_csv(
                results=results_with_metrics,
                session=session,
                filename=f"concurrent_export_{batch_num}.csv",
            )

        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024

        total_time = end_time - start_time
        memory_usage = end_memory - start_memory

        assert total_time < 10.0, (
            f"Concurrent operations took {total_time:.2f}s (expected <10.0s)"
        )
        assert memory_usage < 100, f"Memory usage {memory_usage:.1f}MB (expected <100MB)"

        print("\n📊 Concurrent Operations (5 batches × 10 chemicals):")
        print(f"   ⏱️  Time: {total_time:.3f}s")
        print(f"   💾 Memory: {memory_usage:.1f}MB")


def generate_performance_report():
    """Generate a performance report summary."""

    report = """
# ChemScreen Performance Baseline Report

## Expected Performance Targets

### CSV Processing
- **Small (10 chemicals)**: <1.0s, <10MB memory
- **Medium (50 chemicals)**: <2.0s, <25MB memory
- **Large (100 chemicals)**: <5.0s, <50MB memory

### Quality Analysis
- **50 chemicals**: <1.0s

### Cache Operations
- **Save 20 items**: <2.0s
- **Retrieve 20 items**: <1.0s

### Export Operations
- **CSV (50 chemicals)**: <5.0s
- **Excel (25 chemicals)**: <10.0s

### Session Management
- **Save 10 sessions**: <3.0s
- **Load 10 sessions**: <2.0s

### Memory Usage
- **Overall limit**: <512MB for 200 chemicals
- **Memory growth**: <50MB over 10 iterations

### Full Workflow Timing
- **10 chemicals**: 2-5 minutes total
- **50 chemicals**: 10-20 minutes total
- **100 chemicals**: 20-40 minutes total

*Note: Full workflow times include PubMed API calls which are rate-limited*

## Running Performance Tests

```bash
# Run all performance baseline tests
uv run pytest tests/test_performance_baseline.py -v -s

# Run specific performance test
uv run pytest tests/test_performance_baseline.py::TestPerformanceBaselines::test_memory_usage_baseline -v -s

# Generate performance report
uv run pytest tests/test_performance_baseline.py --tb=no -q
```

## Performance Monitoring

The performance tests establish baselines for:
- Execution time for each operation type
- Memory usage and growth patterns
- File sizes for exports
- Cache efficiency
- Session management overhead

These baselines help identify performance regressions and validate that
the system meets the performance requirements for librarian workflows.
"""

    return report


if __name__ == "__main__":
    print(generate_performance_report())
