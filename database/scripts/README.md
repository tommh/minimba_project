# Database Management Scripts

This directory contains scripts for managing the Energy Certificate database.

## Scripts

### `deploy.py`
Main deployment script that deploys all database objects in correct dependency order.

**Usage:**
```bash
# Set environment variable first
export DATABASE_CONNECTION_STRING="Driver={ODBC Driver 17 for SQL Server};Server=your_server;Database=EnergyCertificate;UID=your_user;PWD=your_password"

# Deploy everything
python scripts/deploy.py
```

### `deploy_selective.py`
Deploy specific object types or files.

**Usage:**
```bash
# Deploy only tables and views
python scripts/deploy_selective.py --types tables views

# Deploy specific stored procedure
python scripts/deploy_selective.py --files schema/stored_procedures/ev_enova.GetCertificateData.StoredProcedure.sql

# Deploy to staging environment
python scripts/deploy_selective.py --types tables --environment staging
```

### `validate.py`
Validate database connection and object deployment.

**Usage:**
```bash
# Validate development database
python scripts/validate.py

# Validate production database
python scripts/validate.py production
```

### `config.py`
Configuration management for different environments.

**Usage:**
```python
from config import get_config

config = get_config('production')
print(config['database_name'])
```

## Environment Configuration

Set environment variables for different environments:

```bash
# Development
export DEV_DATABASE_CONNECTION_STRING="..."

# Staging  
export STAGING_DATABASE_CONNECTION_STRING="..."

# Production
export PROD_DATABASE_CONNECTION_STRING="..."

# Or use generic (will be used as fallback)
export DATABASE_CONNECTION_STRING="..."
```

## Deployment Order

The deployment script follows this order to handle dependencies:

1. **Schemas** - Create schema objects first
2. **Tables** - Create all tables
3. **Indexes** - Add indexes after tables exist
4. **Functions** - Create functions before views/procedures that use them
5. **Views** - Create views after tables and functions
6. **Stored Procedures** - Create procedures last

## Error Handling

- All deployments are wrapped in transactions
- If any step fails, changes are rolled back
- Detailed logging is written to `database_deployment.log`
- Both console and file logging are enabled

## Requirements

Make sure these Python packages are installed:
```bash
pip install pyodbc python-dotenv
```

And that you have the appropriate ODBC driver installed on your system.
