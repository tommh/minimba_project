# Energy Certificate Database

This directory contains the complete database schema and deployment scripts for the Energy Certificate project.

## 🏗️ Project Structure

```
database/
├── schemas/                    # Schema creation scripts
│   └── ev_enova.Schema.sql    # Main energy certificate schema
├── schema/                     # Database objects
│   ├── tables/                # All table definitions (12 tables)
│   ├── views/                 # Database views (5 views)
│   ├── stored_procedures/     # Stored procedures (9 procedures)
│   ├── functions/             # User-defined functions
│   └── indexes/               # Index definitions
├── scripts/                   # Deployment and management scripts
│   ├── deploy.py             # Main deployment script
│   ├── deploy_selective.py   # Selective deployment
│   ├── validate.py           # Database validation
│   ├── config.py             # Environment configuration
│   └── README.md             # Scripts documentation
├── migrations/               # Database migration scripts
└── data/                     # Seed data and reference data
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.7+
- SQL Server 2019+ (or Azure SQL Database)
- ODBC Driver 17 for SQL Server
- Required Python packages: `pyodbc`

### 2. Setup Environment
```bash
# Install Python dependencies
pip install pyodbc python-dotenv

# Set connection string
export DATABASE_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=your_server;Database=EnergyCertificate;UID=your_user;PWD=your_password"
```

### 3. Deploy Database
```bash
# Navigate to database directory
cd database

# Test connection
python scripts/validate.py

# Deploy everything
python scripts/deploy.py
```

## 📊 Database Overview

### Schemas
- **dbo**: Default schema for standard objects
- **ev_enova**: Energy certificate and Enova API related objects

### Key Tables (ev_enova schema)
- `Certificate`: Main certificate data
- `EnergyLabelID`: Energy label identifiers  
- `OpenAIAnswers`: AI-processed certificate data
- `EnovaApi_*`: Enova API integration tables
- `PDF_Download_Log`: PDF processing audit trail

### Key Stored Procedures
- `Get_PDF_for_Extract`: Retrieve PDFs for processing
- `Get_Text_To_Clean`: Get text for cleaning pipeline
- `Get_Extracts_From_Cleaned_Text`: Extract structured data
- `MergeCertificates`: Merge certificate data
- `Archive_OpenAIAnswers`: Archive processed answers

### Views
- `SampleTestDataForOpenAI`: Test data for AI processing
- `ViewOpenAIinPowerBI`: Power BI integration view
- `PDFText_Compression_Percent`: Text compression metrics

## 🔧 Management Commands

### Full Deployment
```bash
python scripts/deploy.py
```

### Selective Deployment
```bash
# Deploy only tables
python scripts/deploy_selective.py --types tables

# Deploy specific procedure
python scripts/deploy_selective.py --files schema/stored_procedures/ev_enova.GetPDFforExtract.StoredProcedure.sql
```

### Validation
```bash
# Validate current database state
python scripts/validate.py

# Validate specific environment
python scripts/validate.py production
```

## 🌍 Environment Management

Configure different environments using environment variables:

```bash
# Development
export DEV_DATABASE_CONNECTION_STRING="..."

# Staging
export STAGING_DATABASE_CONNECTION_STRING="..."

# Production  
export PROD_DATABASE_CONNECTION_STRING="..."
```

## 📝 Development Workflow

1. **Make Schema Changes**: Edit SQL files in appropriate folders
2. **Test Locally**: Deploy to development database
3. **Validate**: Run validation scripts
4. **Version Control**: Commit changes to Git
5. **Deploy**: Use deployment scripts for staging/production

## 🛡️ Security Notes

- Never commit connection strings to version control
- Use environment variables for database credentials
- Ensure proper database permissions for deployment accounts
- Review all SQL scripts before deployment

## 📋 Troubleshooting

### Common Issues

**Connection Errors**:
- Verify ODBC driver is installed
- Check firewall settings
- Confirm connection string format

**Deployment Failures**:
- Check database permissions
- Review deployment logs
- Ensure target database exists

**Missing Dependencies**:
- Deploy schemas before tables
- Deploy tables before views/procedures
- Check for circular dependencies

**Permission Issues**:
- Ensure user has `db_owner` permissions
- For production, use dedicated deployment account
- Schema creation requires elevated permissions

### Log Files
- Deployment logs: `database_deployment.log`
- Check logs for detailed error information
- Logs include SQL batch details for debugging

## 🔄 Migration Strategy

For database changes:

1. **Create Migration Script**: Add new script to `migrations/` folder
2. **Update Objects**: Modify existing SQL files as needed
3. **Test Migration**: Run on development database first
4. **Document Changes**: Update this README with new objects

### Migration Script Template
```sql
-- migrations/001_add_new_feature.sql
-- Description: Add new feature XYZ
-- Author: [Your Name]
-- Date: [Date]

-- Add new columns
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('ev_enova.Certificate') AND name = 'NewColumn')
BEGIN
    ALTER TABLE [ev_enova].[Certificate] ADD [NewColumn] NVARCHAR(50) NULL
END
GO

-- Update existing data if needed
UPDATE [ev_enova].[Certificate] SET [NewColumn] = 'DefaultValue' WHERE [NewColumn] IS NULL
GO
```

## 🔗 Integration with Python Application

The database integrates with the main Python application:

```python
# Example: Using database in Python code
import pyodbc
from config import get_config

# Get database config
config = get_config('production')
conn = pyodbc.connect(config['connection_string'])

# Call stored procedure
cursor = conn.cursor()
cursor.execute("EXEC ev_enova.Get_PDF_for_Extract @limit = ?", 10)
results = cursor.fetchall()
```

## 📈 Performance Considerations

- **Indexes**: Add indexes for frequently queried columns
- **Partitioning**: Consider partitioning large tables by date
- **Statistics**: Keep database statistics updated
- **Monitoring**: Monitor query performance and resource usage

## 🧪 Testing

The database includes test data and validation:

```bash
# Run database tests
python scripts/validate.py

# Check object counts
python scripts/validate.py development
```

## 📚 Additional Resources

- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Database Design Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/tables/)

## 🤝 Contributing

1. Create feature branch from main
2. Make database changes in appropriate folders
3. Test changes with deployment scripts
4. Update documentation
5. Submit pull request

---

**Last Updated**: August 2025  
**Database Version**: Compatible with SQL Server 2019+  
**Python Version**: 3.7+ Deploy schemas before other objects
- Create tables before views that reference them
- Functions must exist before procedures that call them

**Permission Issues**:
- Ensure user has `db_ddladmin` role for schema changes
- `db_datawriter` and `db_datareader` for data operations
- `db_owner` for full deployment capabilities

### Log Files
- Deployment logs: `database_deployment.log`
- Check logs for detailed error information
- Logs include both INFO and ERROR level messages

## 🔗 Integration with Python Application

The database integrates with the main Python application through:

- **PDF Processing Pipeline**: Tables store PDF metadata and extracted text
- **OpenAI Integration**: `OpenAIAnswers` table stores AI-processed results
- **Enova API**: Tables support API data synchronization
- **Power BI**: Views provide analytics-ready data

### Connection in Python Code
```python
import pyodbc
import os

# Use same connection string as deployment scripts
conn_str = os.getenv('DATABASE_CONNECTION_STRING')
conn = pyodbc.connect(conn_str)

# Example: Get certificates for processing
cursor = conn.cursor()
cursor.execute("EXEC ev_enova.Get_PDF_for_Extract")
results = cursor.fetchall()
```

## 📈 Monitoring and Maintenance

### Regular Tasks
- Monitor `PDF_Download_Log` for processing status
- Archive old `OpenAIAnswers` using the archive procedure
- Check `EnovaApi_*_log` tables for API sync issues
- Review database size and performance

### Performance Monitoring
```sql
-- Check table sizes
SELECT 
    s.name AS schema_name,
    t.name AS table_name,
    p.rows AS row_count
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE s.name = 'ev_enova'
ORDER BY p.rows DESC;
```

## 🤝 Contributing

When making database changes:

1. **Follow naming conventions**:
   - Tables: PascalCase (e.g., `Certificate`)
   - Procedures: Verb_Object pattern (e.g., `Get_PDF_for_Extract`)
   - Views: Descriptive names (e.g., `SampleTestDataForOpenAI`)

2. **Include documentation**:
   - Add comments to complex procedures
   - Document parameter meanings
   - Explain business logic

3. **Test thoroughly**:
   - Deploy to development first
   - Run validation scripts
   - Test with sample data

4. **Version control**:
   - One object per file
   - Meaningful commit messages
   - Include migration scripts for breaking changes

## 📞 Support

For database-related issues:
1. Check this README and scripts/README.md
2. Review deployment logs
3. Run validation script to diagnose issues
4. Check SQL Server error logs

---

**Last Updated**: August 2025  
**Database Version**: SQL Server 2025 compatible  
**Python Version**: 3.7+
