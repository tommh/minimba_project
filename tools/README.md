# 🛠️ Tools & Utilities

This directory contains diagnostic tools, utilities, and maintenance scripts for the Energy Certificate project.

## 📋 Available Tools

### `diagnose_pdf_scanner.py`
**Purpose**: Diagnose PDF scanner issues and database/filesystem discrepancies

**Usage**:
```bash
python tools/diagnose_pdf_scanner.py
```

**What it checks**:
- PDF directory existence and file counts
- Database connection and record counts
- Files present on disk vs. database
- Duplicate filename detection
- File overlap analysis

**When to use**:
- PDF processing pipeline issues
- Database sync problems
- File count discrepancies
- Missing file investigations

## 🚀 Running Tools

All tools can be run from the project root directory:

```bash
# Run PDF scanner diagnostics
python tools/diagnose_pdf_scanner.py

# Future tools can be added here...
```

## 🔧 Adding New Tools

When adding new diagnostic or utility tools:

1. **Create the script** in this `tools/` directory
2. **Add documentation** to this README
3. **Include usage examples** and purpose
4. **Use descriptive filenames** (e.g., `diagnose_`, `check_`, `fix_`, `analyze_`)

## 📁 Tool Categories

### Diagnostic Tools
- `diagnose_pdf_scanner.py` - PDF processing diagnostics

### Future Tool Ideas
- `check_database_health.py` - Database performance and integrity checks
- `analyze_processing_pipeline.py` - End-to-end pipeline analysis
- `fix_orphaned_records.py` - Clean up orphaned database records
- `benchmark_api_performance.py` - API endpoint performance testing

## 🛡️ Best Practices

- **Non-destructive**: Tools should be read-only unless explicitly documented
- **Safe to run**: Should not modify production data without confirmation
- **Informative output**: Provide clear, actionable information
- **Error handling**: Handle exceptions gracefully with helpful messages
- **Logging**: Use appropriate logging levels for troubleshooting

---

**Note**: These are operational tools for maintenance and troubleshooting, not automated tests. For tests, see the `tests/` directory.
