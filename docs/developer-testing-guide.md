# Developer Testing Guide

## Overview

This guide provides comprehensive testing procedures for developers working on ChemScreen. Follow these steps before committing code or creating pull requests.

## Prerequisites

```bash
# Ensure development environment is set up
uv sync
uv run pre-commit install

# Verify environment
uv run python -c "from chemscreen.config import get_config; print('Config loaded successfully')"
```

## Automated Testing Checklist

### Code Quality Checks

Run these commands in order and ensure all pass:

```bash
# 1. Lint code
uv run ruff check .

# 2. Format code
uv run ruff format .

# 3. Type checking
uv run mypy chemscreen/

# 4. Run test suite
uv run pytest

# 5. Verbose test run (if needed)
uv run pytest -xvs

# 6. Markdown linting
uv run pymarkdownlnt **/*.md
```

### Performance Checks

```bash
# Check memory usage during large batch
uv run python -c "
import psutil
import os
print(f'Memory usage: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.1f} MB')
"
```

## Manual Testing Procedures

### 1. Configuration System Testing

#### Environment Variable Loading
```bash
# Test with no .env file
mv .env .env.backup 2>/dev/null || true
uv run streamlit run app.py --server.headless true &
sleep 5
pkill -f streamlit
mv .env.backup .env 2>/dev/null || true

# Test with .env file
cp .env.example .env
# Edit PUBMED_API_KEY if you have one
uv run streamlit run app.py --server.headless true &
sleep 5
pkill -f streamlit
```

#### Configuration Validation
```bash
# Test configuration validation
uv run python -c "
from chemscreen.config import get_config
config = get_config()
warnings = config.validate_configuration()
for warning in warnings:
    print(f'⚠️  {warning}')
print(f'✅ Configuration validated with {len(warnings)} warnings')
"
```

### 2. Core Functionality Testing

#### Chemical Processing
```bash
# Test chemical validation
uv run python -c "
from chemscreen.processor import validate_cas
test_cases = ['75-09-2', '64-17-5', 'invalid', '']
for cas in test_cases:
    result = validate_cas(cas)
    print(f'{cas}: {result}')
"
```

#### Cache System
```bash
# Test cache functionality
uv run python -c "
from chemscreen.cache import get_cache_manager
from chemscreen.models import Chemical

cache = get_cache_manager()
stats = cache.get_cache_stats()
print(f'Cache stats: {stats}')

# Clear expired cache
cleared = cache.clear_expired()
print(f'Cleared {cleared} expired entries')
"
```

### 3. Application Testing

#### Basic Startup
```bash
# Start application
uv run streamlit run app.py

# In browser: http://localhost:8501
# Verify:
# - Page loads without errors
# - Configuration warnings (if any) are displayed
# - Upload area is visible
# - All UI elements render correctly
```

#### Demo Data Testing
- [ ] Upload `data/raw/demo_small.csv` (10 chemicals)
- [ ] Verify all 10 chemicals are displayed in preview
- [ ] Start search with default parameters
- [ ] Verify progress updates every few chemicals
- [ ] Check results show non-zero publication counts
- [ ] Export results to Excel
- [ ] Open exported file to verify formatting

#### Large Batch Testing
- [ ] Upload `data/raw/demo_medium.csv` (50 chemicals)
- [ ] Monitor memory usage during processing
- [ ] Verify processing completes within 15 minutes
- [ ] Check cache hit rates improve on second run
- [ ] Export large results successfully

#### Error Handling Testing
```bash
# Create invalid CSV for testing
echo "invalid,headers" > /tmp/test_invalid.csv
echo "bad,data" >> /tmp/test_invalid.csv
```
- [ ] Upload invalid CSV file
- [ ] Verify helpful error message
- [ ] Test with empty CSV file
- [ ] Test with very large file (>10MB)

### 4. API Integration Testing

#### PubMed Connectivity
```bash
# Test basic PubMed connectivity
uv run python -c "
import asyncio
from chemscreen.pubmed import PubMedClient
from chemscreen.models import Chemical

async def test_search():
    chemical = Chemical(name='caffeine', cas_number='58-08-2')
    async with PubMedClient() as client:
        result = await client.search(chemical)
        print(f'Search for {chemical.name}: {result.total_count} results')
        if result.error:
            print(f'Error: {result.error}')
        else:
            print(f'✅ PubMed search successful')

asyncio.run(test_search())
"
```

#### Rate Limiting
```bash
# Test rate limiting behavior
uv run python -c "
import asyncio
import time
from chemscreen.pubmed import RateLimiter

async def test_rate_limit():
    limiter = RateLimiter(3.0)  # 3 requests/second
    start = time.time()

    for i in range(5):
        await limiter.wait()
        print(f'Request {i+1} at {time.time() - start:.2f}s')

asyncio.run(test_rate_limit())
"
```

### 5. Session Management Testing

#### Session Persistence
- [ ] Start a search with demo data
- [ ] Close browser/restart app during processing
- [ ] Verify session can be resumed
- [ ] Check session history shows previous searches

#### Session Cleanup
```bash
# Test session cleanup
uv run python -c "
from chemscreen.session_manager import SessionManager
manager = SessionManager()
deleted = manager.cleanup_old_sessions(1)  # Delete sessions older than 1 day
print(f'Cleaned up {deleted} old sessions')
"
```

### 6. Export Testing

#### Format Testing
- [ ] Export to CSV format
- [ ] Export to Excel format (.xlsx)
- [ ] Export to JSON format
- [ ] Verify all formats contain same data
- [ ] Test export with abstracts included
- [ ] Test export without abstracts

#### Large Export Testing
- [ ] Export 100+ chemical results
- [ ] Verify Excel file opens without corruption
- [ ] Check file size is reasonable (<50MB)
- [ ] Verify all data is preserved

## Performance Benchmarks

### Expected Performance Metrics

| Metric | Target | Maximum |
|--------|--------|---------|
| Startup time | < 5 seconds | < 10 seconds |
| 10 chemical search | < 2 minutes | < 5 minutes |
| 50 chemical search | < 10 minutes | < 20 minutes |
| 100 chemical search | < 20 minutes | < 30 minutes |
| Memory usage (100 chemicals) | < 256MB | < 512MB |
| Export time (100 chemicals) | < 5 seconds | < 10 seconds |
| Cache hit rate (second run) | > 90% | > 80% |

### Performance Testing Script

```bash
# Run performance test
uv run python -c "
import time
import psutil
import os
from pathlib import Path

def measure_performance():
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024
    start_time = time.time()

    # Your test code here
    # e.g., batch search with demo data

    end_time = time.time()
    end_memory = process.memory_info().rss / 1024 / 1024

    print(f'Execution time: {end_time - start_time:.2f} seconds')
    print(f'Memory usage: {end_memory:.1f} MB (delta: {end_memory - start_memory:.1f} MB)')

measure_performance()
"
```

## Common Issues and Solutions

### Issue: High Memory Usage
- Check for large result sets not being cleared
- Verify cache is not growing unbounded
- Monitor Streamlit session state size

### Issue: Slow Performance
- Check PubMed rate limiting configuration
- Verify cache hit rates
- Monitor network connectivity

### Issue: Configuration Problems
- Verify .env file format
- Check file permissions on data directories
- Validate environment variable types

### Issue: Export Failures
- Check disk space in export directory
- Verify openpyxl installation
- Test with smaller result sets

## Git Workflow Testing

### Before Committing
```bash
# Full test suite
uv run ruff check .
uv run ruff format .
uv run mypy chemscreen/
uv run pytest
uv run pymarkdownlnt **/*.md

# Manual smoke test
uv run streamlit run app.py --server.headless true &
sleep 10
curl -f http://localhost:8501 >/dev/null
pkill -f streamlit
```

### Pre-commit Hook Testing
```bash
# Test pre-commit hooks
uv run pre-commit run --all-files
```

## Test Data Management

### Demo Data Files
- `demo_small.csv` - 10 chemicals for quick testing
- `demo_medium.csv` - 50 chemicals for medium load testing
- `simple_chemicals.csv` - Basic chemicals with known results
- `chemicals_with_errors.csv` - Test error handling

### Creating Test Data
```bash
# Generate custom test data
uv run python -c "
import csv
chemicals = [
    ('Caffeine', '58-08-2'),
    ('Aspirin', '50-78-2'),
    ('Glucose', '50-99-7'),
]

with open('/tmp/custom_test.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Chemical Name', 'CAS Number'])
    writer.writerows(chemicals)
print('Created /tmp/custom_test.csv')
"
```

## Debugging Tips

### Enable Debug Mode
```bash
# Set debug mode in .env
echo "DEBUG_MODE=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env
echo "ENABLE_PERFORMANCE_LOGGING=true" >> .env
```

### View Logs
```bash
# Monitor application logs
tail -f ~/.streamlit/logs/streamlit.log

# Or run with verbose output
uv run streamlit run app.py --logger.level debug
```

### Profile Performance
```bash
# Profile memory usage
uv run python -m memory_profiler app.py

# Profile execution time
uv run python -m cProfile -o profile.out app.py
```

## Sign-off Checklist

Before marking development complete:

- [ ] All automated tests pass
- [ ] Manual testing procedures completed
- [ ] Performance benchmarks met
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Code review completed
- [ ] Demo data tests successful
- [ ] Export functionality verified
- [ ] Session management tested
- [ ] Configuration system validated
- [ ] Git hooks pass
- [ ] Memory usage within limits
- [ ] No sensitive data in logs
- [ ] Cache functionality working
- [ ] Rate limiting effective

## Contact

For testing issues or questions:
- Check CLAUDE.md for project-specific guidance
- Review PRD for requirements clarification
- Test with librarian feedback scenarios
