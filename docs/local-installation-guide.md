# ChemScreen Local Installation Guide

## Overview

This guide walks you through installing and running ChemScreen on your local desktop computer. ChemScreen is designed to run locally to ensure data privacy and provide reliable performance for chemical literature screening.

## System Requirements

### Operating System

- **Windows**: Windows 10 or later
- **macOS**: macOS 10.15 (Catalina) or later
- **Linux**: Ubuntu 18.04+ or equivalent

### Hardware Requirements

- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 2GB free disk space
- **CPU**: Any modern processor (2+ cores recommended)
- **Network**: Internet connection required for PubMed searches

### Software Prerequisites

- Web browser (Chrome, Firefox, Safari, or Edge)
- No other software installation required (Python will be installed automatically)

## Installation Methods

Choose the method that best fits your technical comfort level:

### Method 1: Quick Start (Recommended for Most Users)

This method uses our automated installer script.

#### Windows

1. **Download the installer**:
   - Go to [Release Page URL] (replace with actual URL)
   - Download `chemscreen-windows-installer.exe`

2. **Run the installer**:
   - Double-click the downloaded file
   - Follow the installation wizard
   - The installer will automatically set up Python and all dependencies

3. **Launch ChemScreen**:
   - Find "ChemScreen" in your Start Menu
   - Or double-click the desktop shortcut
   - Your browser will open automatically to the application

#### macOS

1. **Download the installer**:
   - Go to [Release Page URL]
   - Download `chemscreen-macos-installer.dmg`

2. **Install the application**:
   - Open the downloaded DMG file
   - Drag ChemScreen to your Applications folder
   - You may need to allow installation from unidentified developers in System Preferences > Security & Privacy

3. **Launch ChemScreen**:
   - Open Applications folder
   - Double-click ChemScreen
   - Your browser will open automatically to the application

#### Linux (Ubuntu/Debian)

1. **Download and install**:

   ```bash
   wget https://[release-url]/chemscreen-linux-installer.deb
   sudo dpkg -i chemscreen-linux-installer.deb
   sudo apt-get install -f  # Install any missing dependencies
   ```

2. **Launch ChemScreen**:

   ```bash
   chemscreen
   ```

   Or find it in your applications menu.

### Method 2: Manual Installation (For Advanced Users)

If you prefer to install manually or the automated installer doesn't work:

#### Step 1: Install Python

**Windows**:
1. Go to https://www.python.org/downloads/
2. Download Python 3.9 or later
3. Run installer and check "Add Python to PATH"

**macOS**:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

#### Step 2: Install UV Package Manager
```bash
# Install UV (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows, use PowerShell:
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Step 3: Download ChemScreen
```bash
# Option A: Download from GitHub releases
wget https://github.com/[username]/chemscreen-proto/archive/refs/tags/v1.0.0.zip
unzip v1.0.0.zip
cd chemscreen-proto-1.0.0

# Option B: Clone repository (if you have git)
git clone https://github.com/[username]/chemscreen-proto.git
cd chemscreen-proto
```

#### Step 4: Install Dependencies
```bash
# Install all required packages
uv sync

# Verify installation
uv run python -c "import streamlit; print('Installation successful!')"
```

#### Step 5: Create Configuration
```bash
# Copy example configuration
cp .env.example .env

# Edit configuration file (optional)
# See Configuration section below
```

## Configuration

### Basic Configuration (Optional)

ChemScreen works out of the box with default settings, but you can customize it:

1. **Find your configuration file**:
   - Windows: `C:\Users\[username]\AppData\Local\ChemScreen\.env`
   - macOS: `~/Library/Application Support/ChemScreen/.env`
   - Linux: `~/.config/chemscreen/.env`

2. **Common settings to customize**:

```env
# PubMed API Key (optional, but recommended for better performance)
PUBMED_API_KEY=your_api_key_here
PUBMED_EMAIL=your.email@organization.com

# Data storage locations
DATA_DIR=./chemscreen_data
CACHE_DIR=./chemscreen_data/cache
EXPORTS_DIR=./chemscreen_data/exports

# Performance settings
MAX_BATCH_SIZE=100
MAX_RESULTS_PER_CHEMICAL=100
DEFAULT_DATE_RANGE_YEARS=10

# Cache settings (speeds up repeated searches)
CACHE_ENABLED=true
CACHE_TTL=3600

# UI preferences
PAGE_TITLE=ChemScreen - Literature Search
THEME_PRIMARY_COLOR=#0066CC
```

### Getting a PubMed API Key (Recommended)

Having a PubMed API key increases your search speed from 3 to 10 requests per second:

1. Go to https://www.ncbi.nlm.nih.gov/account/
2. Create an NCBI account (free)
3. Go to Account Settings → API Key Management
4. Create a new API key
5. Add it to your configuration file:
   ```env
   PUBMED_API_KEY=your_key_here
   PUBMED_EMAIL=your.email@domain.com
   ```

## Running ChemScreen

### Using the Desktop Application
If you used the automated installer:
- **Windows**: Start Menu → ChemScreen
- **macOS**: Applications → ChemScreen
- **Linux**: Applications Menu → ChemScreen

### Using Command Line
If you installed manually:

```bash
# Navigate to ChemScreen directory
cd /path/to/chemscreen-proto

# Start the application
uv run streamlit run app.py

# The application will open in your default browser
# If it doesn't open automatically, go to: http://localhost:8501
```

### First Time Setup

1. **Verify installation**:
   - ChemScreen should open in your browser
   - You should see the main upload interface
   - Check for any configuration warnings at the top

2. **Test with demo data**:
   - Download demo data: `data/raw/demo_small.csv`
   - Upload the file using the interface
   - Run a test search with 10 chemicals
   - Verify results and export functionality

## Using ChemScreen

### Basic Workflow

1. **Prepare your data**:
   - Create a CSV file with chemical names and CAS numbers
   - Use the template: `Chemical Name, CAS Number`
   - Example:
     ```csv
     Chemical Name,CAS Number
     Caffeine,58-08-2
     Aspirin,50-78-2
     Glucose,50-99-7
     ```

2. **Upload and search**:
   - Drag and drop your CSV file
   - Review the chemical preview
   - Adjust search parameters if needed
   - Click "Start Search"

3. **Review results**:
   - Monitor progress in real-time
   - Review publication counts and quality scores
   - Sort and filter results

4. **Export results**:
   - Choose Excel or CSV format
   - Download the formatted report
   - Use in your regulatory assessments

### Managing Data

**Data Storage Locations**:
- **Input files**: Store in `data/raw/` folder
- **Exports**: Automatically saved to `data/processed/`
- **Cache**: Stored in `data/cache/` (speeds up repeat searches)
- **Sessions**: Search history in `data/sessions/`

**File Management**:
```bash
# View data directory structure
ls data/
# raw/        - Your input CSV files
# processed/  - Exported results
# cache/      - Cached API responses
# sessions/   - Search session history

# Clear cache to free space
rm -rf data/cache/*

# Clean old exports (older than 30 days)
find data/processed/ -name "*.xlsx" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

#### Application Won't Start
**Problem**: Error when launching ChemScreen

**Solutions**:
1. **Check Python installation**:
   ```bash
   python --version  # Should be 3.9+
   ```

2. **Reinstall dependencies**:
   ```bash
   uv sync --reinstall
   ```

3. **Clear cache and restart**:
   ```bash
   rm -rf .uv/  # Clear UV cache
   uv sync
   ```

#### Browser Doesn't Open
**Problem**: ChemScreen starts but browser doesn't open

**Solution**:
1. Manually open your browser
2. Go to: `http://localhost:8501`
3. Bookmark this URL for future use

#### Slow Performance
**Problem**: Searches are taking too long

**Solutions**:
1. **Get a PubMed API key** (most important)
2. **Reduce batch size**:
   ```env
   MAX_BATCH_SIZE=50
   MAX_RESULTS_PER_CHEMICAL=50
   ```
3. **Check internet connection**
4. **Enable caching**:
   ```env
   CACHE_ENABLED=true
   ```

#### Upload Errors
**Problem**: CSV files won't upload

**Solutions**:
1. **Check file format**:
   - Must be CSV (comma-separated)
   - Save from Excel as "CSV (Comma delimited)"
   - Ensure UTF-8 encoding

2. **Check file size**:
   - Maximum 10MB by default
   - For larger files, increase limit:
     ```env
     MAX_UPLOAD_SIZE_MB=50
     ```

3. **Verify column headers**:
   - First column: Chemical names
   - Second column: CAS numbers (optional)

#### Memory Issues
**Problem**: Application crashes with large datasets

**Solutions**:
1. **Process smaller batches** (25-50 chemicals)
2. **Increase memory limit**:
   ```env
   MEMORY_LIMIT_MB=1024
   ```
3. **Clear cache periodically**
4. **Restart application between large searches**

#### Network Errors
**Problem**: PubMed searches failing

**Solutions**:
1. **Check internet connection**
2. **Verify PubMed is accessible**: https://pubmed.ncbi.nlm.nih.gov/
3. **Increase timeout**:
   ```env
   REQUEST_TIMEOUT=60
   ```
4. **Reduce request rate**:
   ```env
   RATE_LIMIT_DELAY=1.0
   ```

### Getting Help

#### Log Files
Check log files for detailed error information:
- **Windows**: `%APPDATA%\ChemScreen\logs\`
- **macOS**: `~/Library/Logs/ChemScreen/`
- **Linux**: `~/.local/share/chemscreen/logs/`

#### Debug Mode
Enable detailed logging:
```env
DEBUG_MODE=true
LOG_LEVEL=DEBUG
ENABLE_PERFORMANCE_LOGGING=true
```

#### System Information
Gather system info for support:
```bash
# Check Python and package versions
uv run python -c "
import sys
import streamlit
import pandas
print(f'Python: {sys.version}')
print(f'Streamlit: {streamlit.__version__}')
print(f'Pandas: {pandas.__version__}')
"
```

## Advanced Usage

### Performance Optimization

#### For Regular Use (20-50 chemicals)
```env
MAX_BATCH_SIZE=50
MAX_RESULTS_PER_CHEMICAL=100
CACHE_ENABLED=true
CONCURRENT_REQUESTS=1
```

#### For Large Batches (100+ chemicals)
```env
MAX_BATCH_SIZE=100
MAX_RESULTS_PER_CHEMICAL=50
MEMORY_LIMIT_MB=1024
EXPORT_CHUNK_SIZE=5000
```

#### For Fast Screening (reduced accuracy)
```env
MAX_RESULTS_PER_CHEMICAL=25
DEFAULT_DATE_RANGE_YEARS=5
DEFAULT_INCLUDE_REVIEWS=false
```

### Batch Processing Scripts

For power users, automate common tasks:

#### Bulk Processing Script
```bash
#!/bin/bash
# Process multiple CSV files automatically

for file in data/raw/*.csv; do
    echo "Processing $file..."
    # Add your automation logic here
done
```

#### Cache Management
```bash
#!/bin/bash
# Clean up old cache files weekly

# Delete cache older than 7 days
find data/cache/ -name "*.json" -mtime +7 -delete

# Delete exports older than 30 days
find data/processed/ -name "*.xlsx" -mtime +30 -delete

echo "Cache cleanup completed"
```

### Custom Workflows

#### Integration with Excel
1. Export from ChemScreen as CSV
2. Import into Excel template
3. Add custom analysis columns
4. Create pivot tables for summary reports

#### Integration with Reference Managers
1. Export detailed results with PMIDs
2. Import PMIDs into Zotero/Mendeley/EndNote
3. Bulk download full-text articles
4. Organize by chemical or assessment project

## Security and Privacy

### Data Privacy
- **All data stays on your computer** - no cloud storage
- **Network traffic** only to PubMed (encrypted HTTPS)
- **No user tracking** or analytics
- **Cache files** contain only publication metadata

### Network Security
- Only connects to official PubMed servers
- Uses secure HTTPS connections
- No external dependencies beyond PubMed
- Firewall rules: Allow outbound HTTPS (port 443)

### File Security
- Configuration files contain only non-sensitive settings
- API keys stored locally (never transmitted except to PubMed)
- Export files contain only publication data
- Regular backup recommended for important results

## Maintenance

### Regular Tasks

#### Weekly
```bash
# Clear expired cache
uv run python -c "
from chemscreen.cache import get_cache_manager
cache = get_cache_manager()
cleared = cache.clear_expired()
print(f'Cleared {cleared} expired cache entries')
"
```

#### Monthly
```bash
# Clean old sessions
uv run python -c "
from chemscreen.session_manager import SessionManager
manager = SessionManager()
deleted = manager.cleanup_old_sessions(30)
print(f'Cleaned up {deleted} old sessions')
"
```

#### Updates
```bash
# Check for updates (if using git)
git pull origin main
uv sync

# Or download new release and reinstall
```

### Backup
```bash
# Backup important data
tar -czf chemscreen-backup-$(date +%Y%m%d).tar.gz \
    data/raw/ \
    data/processed/ \
    .env
```

## Uninstallation

### Automated Installer
- **Windows**: Control Panel → Programs → Uninstall ChemScreen
- **macOS**: Delete ChemScreen from Applications folder
- **Linux**: `sudo apt remove chemscreen`

### Manual Installation
```bash
# Remove ChemScreen directory
rm -rf /path/to/chemscreen-proto

# Remove data (optional)
rm -rf ~/chemscreen_data

# Remove UV package manager (optional)
rm -rf ~/.local/share/uv
```

## Support

### Documentation
- **Developer Guide**: `docs/developer-testing-guide.md`
- **Librarian Guide**: `docs/librarian-testing-guide.md`
- **Project Documentation**: `CLAUDE.md`

### Community
- **Issues**: [GitHub Issues URL]
- **Discussions**: [GitHub Discussions URL]
- **Email**: support@chemscreen.org

### Commercial Support
For institutional deployments or custom requirements:
- **Consulting**: Available for setup and training
- **Custom Development**: Feature additions and integrations
- **Priority Support**: Dedicated support channels

---

**Version**: 1.0.0
**Last Updated**: [Current Date]
**Compatibility**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
