# 📊 Reports & Analytics

This directory contains Power BI reports and other analytics assets for the Energy Certificate project.

## 📋 Available Reports

### Energy Certificate Analysis Dashboard (`energy_certificate_analysis.pbix`)
**Purpose**: Visualizes OpenAI-generated insights from energy certificate data

**Data Sources**:
- `[ev_enova].[OpenAIAnswers]` - AI-processed certificate analysis
- `[ev_enova].[ViewOpenAIinPowerBI]` - Optimized view for Power BI integration
- `[ev_enova].[Certificate]` - Base certificate data

**Key Visualizations**:
- AI analysis completion rates by prompt version
- Distribution of energy certificate evaluations
- Positive aspects identified across properties
- Estate type analysis and trends
- Processing performance metrics

**How to Use**:
1. **Prerequisites**: 
   - Power BI Desktop installed
   - Access to SQL Server database with appropriate permissions
   - Database connection configured

2. **Open Report**:
   ```bash
   # Double-click to open in Power BI Desktop
   reports/energy_certificate_analysis.pbix
   ```

3. **Refresh Data**:
   - Click "Refresh" in Power BI to get latest data
   - Ensure database connection is active

4. **Customize**:
   - Modify visuals as needed
   - Add filters for specific date ranges or certificate types
   - Export to Power BI Service for sharing

## 🔧 Database Views for Power BI

The project includes optimized database views for Power BI reporting:

### `[ev_enova].[ViewOpenAIinPowerBI]`
Pre-aggregated view optimized for Power BI performance with:
- Cleaned AI response data
- Calculated metrics
- Proper data types for visualization
- Filtered for valid responses only

### Example Query:
```sql
-- Sample data for Power BI development
SELECT TOP 100 *
FROM [ev_enova].[ViewOpenAIinPowerBI]
WHERE ProcessedDate >= DATEADD(month, -3, GETDATE())
ORDER BY ProcessedDate DESC;
```

## 📈 Report Maintenance

### Updating Reports
1. **Data Changes**: If database schema changes, update data source connections
2. **New Fields**: Add new columns from OpenAI responses as they become available
3. **Performance**: Monitor query performance and optimize as data grows

### Best Practices
- **Scheduled Refresh**: Set up automatic data refresh in Power BI Service
- **Security**: Use appropriate database credentials with read-only access
- **Documentation**: Update this README when adding new reports or visuals

### Troubleshooting
**Connection Issues**:
- Verify database server is accessible
- Check SQL Server authentication settings
- Ensure ODBC drivers are installed

**Performance Issues**:
- Use the optimized `ViewOpenAIinPowerBI` view instead of raw tables
- Consider data filtering by date ranges
- Monitor query execution times in SQL Server

**Data Issues**:
- Validate OpenAI data quality with `python main.py openai-stats`
- Check for missing or incomplete AI responses
- Review data processing logs

## 🚀 Integration with Python Pipeline

The Power BI reports integrate seamlessly with the Python processing pipeline:

```bash
# Process OpenAI data
python main.py openai --limit 100

# Check processing statistics  
python main.py openai-stats

# Refresh Power BI report to see new data
# (Open report and click Refresh)
```

## 📁 File Organization

```
reports/
├── energy_certificate_analysis.pbix    # Main dashboard
├── README.md                           # This file
├── templates/                          # Report templates
│   └── certificate_template.pbit      # Power BI template file
├── exports/                            # Exported reports
│   ├── monthly_summary.pdf            # Monthly PDF exports
│   └── data_exports/                   # CSV/Excel exports
└── documentation/                      # Report documentation
    ├── report_guide.md                 # User guide
    └── data_dictionary.md              # Field definitions
```

## 🎯 Future Reports

Consider adding these reports as the project grows:
- **Processing Performance Dashboard** - Pipeline execution metrics
- **Data Quality Report** - AI response completeness and accuracy
- **Certificate Trends Analysis** - Energy efficiency trends over time
- **Geographic Analysis** - Regional energy certificate patterns
- **API Usage Dashboard** - Enova API call statistics and performance

## 📚 Additional Resources

- [Power BI Documentation](https://docs.microsoft.com/en-us/power-bi/)
- [SQL Server Integration](https://docs.microsoft.com/en-us/power-bi/connect-data/service-azure-sql-database-with-direct-connect)
- [Best Practices for Power BI](https://docs.microsoft.com/en-us/power-bi/guidance/)

---

**Note**: Power BI reports require appropriate database permissions and may need connection string updates when moving between environments.
