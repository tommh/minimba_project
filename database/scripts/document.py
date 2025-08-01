#!/usr/bin/env python3
"""
Generate documentation for database objects
"""

import os
import pyodbc
from pathlib import Path
import json
from config import get_config

class DatabaseDocumenter:
    def __init__(self, connection_string):
        self.connection_string = connection_string
    
    def generate_schema_documentation(self):
        """Generate comprehensive schema documentation"""
        conn = pyodbc.connect(self.connection_string)
        cursor = conn.cursor()
        
        documentation = {
            'database_info': self._get_database_info(cursor),
            'schemas': self._get_schemas(cursor),
            'tables': self._get_tables_info(cursor),
            'views': self._get_views_info(cursor),
            'procedures': self._get_procedures_info(cursor),
            'functions': self._get_functions_info(cursor)
        }
        
        cursor.close()
        conn.close()
        
        return documentation
    
    def _get_database_info(self, cursor):
        """Get basic database information"""
        cursor.execute("SELECT DB_NAME(), @@VERSION, GETDATE()")
        result = cursor.fetchone()
        return {
            'name': result[0],
            'version': result[1].split('\n')[0],
            'documentation_generated': str(result[2])
        }
    
    def _get_schemas(self, cursor):
        """Get schema information"""
        cursor.execute("""
            SELECT s.name, p.name as owner,
                   ep.value as description
            FROM sys.schemas s
            JOIN sys.database_principals p ON s.principal_id = p.principal_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = s.schema_id 
                AND ep.name = 'MS_Description'
            WHERE s.schema_id > 4  -- Skip system schemas
            ORDER BY s.name
        """)
        return [{'name': row[0], 'owner': row[1], 'description': row[2]} for row in cursor.fetchall()]
    
    def _get_tables_info(self, cursor):
        """Get detailed table information"""
        cursor.execute("""
            SELECT s.name as schema_name, 
                   t.name as table_name,
                   ep.value as description,
                   p.rows as row_count
            FROM sys.tables t
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = t.object_id 
                AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            LEFT JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0,1)
            ORDER BY s.name, t.name
        """)
        
        tables = []
        for row in cursor.fetchall():
            table_info = {
                'schema': row[0],
                'name': row[1], 
                'description': row[2],
                'row_count': row[3],
                'columns': self._get_table_columns(cursor, row[0], row[1])
            }
            tables.append(table_info)
        
        return tables
    
    def _get_table_columns(self, cursor, schema_name, table_name):
        """Get column information for a table"""
        cursor.execute("""
            SELECT c.name, 
                   t.name as data_type,
                   c.max_length,
                   c.precision,
                   c.scale,
                   c.is_nullable,
                   c.is_identity,
                   dc.definition as default_value,
                   ep.value as description
            FROM sys.columns c
            JOIN sys.types t ON c.user_type_id = t.user_type_id
            JOIN sys.tables tb ON c.object_id = tb.object_id
            JOIN sys.schemas s ON tb.schema_id = s.schema_id
            LEFT JOIN sys.default_constraints dc ON c.object_id = dc.parent_object_id 
                AND c.column_id = dc.parent_column_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id 
                AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
            WHERE s.name = ? AND tb.name = ?
            ORDER BY c.column_id
        """, schema_name, table_name)
        
        return [{
            'name': row[0],
            'data_type': row[1],
            'max_length': row[2],
            'precision': row[3],
            'scale': row[4],
            'nullable': bool(row[5]),
            'identity': bool(row[6]),
            'default_value': row[7],
            'description': row[8]
        } for row in cursor.fetchall()]
    
    def _get_views_info(self, cursor):
        """Get view information"""
        cursor.execute("""
            SELECT s.name as schema_name, 
                   v.name as view_name,
                   ep.value as description
            FROM sys.views v
            JOIN sys.schemas s ON v.schema_id = s.schema_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = v.object_id 
                AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            ORDER BY s.name, v.name
        """)
        return [{'schema': row[0], 'name': row[1], 'description': row[2]} for row in cursor.fetchall()]
    
    def _get_procedures_info(self, cursor):
        """Get stored procedure information"""
        cursor.execute("""
            SELECT s.name as schema_name, 
                   p.name as procedure_name,
                   ep.value as description,
                   p.create_date,
                   p.modify_date
            FROM sys.procedures p
            JOIN sys.schemas s ON p.schema_id = s.schema_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = p.object_id 
                AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            WHERE p.type = 'P'
            ORDER BY s.name, p.name
        """)
        return [{
            'schema': row[0], 
            'name': row[1], 
            'description': row[2],
            'created': str(row[3]),
            'modified': str(row[4])
        } for row in cursor.fetchall()]
    
    def _get_functions_info(self, cursor):
        """Get function information"""
        cursor.execute("""
            SELECT s.name as schema_name, 
                   o.name as function_name,
                   o.type_desc,
                   ep.value as description
            FROM sys.objects o
            JOIN sys.schemas s ON o.schema_id = s.schema_id
            LEFT JOIN sys.extended_properties ep ON ep.major_id = o.object_id 
                AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            WHERE o.type IN ('FN', 'IF', 'TF')  -- Scalar, Inline Table, Table functions
            ORDER BY s.name, o.name
        """)
        return [{
            'schema': row[0], 
            'name': row[1], 
            'type': row[2],
            'description': row[3]
        } for row in cursor.fetchall()]
    
    def save_documentation(self, documentation, output_path='database_documentation.json'):
        """Save documentation to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(documentation, f, indent=2, ensure_ascii=False)
        print(f"📄 Documentation saved to: {output_path}")
    
    def generate_markdown_report(self, documentation, output_path='database_report.md'):
        """Generate a markdown report"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Database Documentation\n\n")
            f.write(f"**Database**: {documentation['database_info']['name']}\n")
            f.write(f"**Generated**: {documentation['database_info']['documentation_generated']}\n\n")
            
            # Schemas
            f.write("## Schemas\n\n")
            for schema in documentation['schemas']:
                f.write(f"- **{schema['name']}**: {schema['description'] or 'No description'}\n")
            
            # Tables
            f.write("\n## Tables\n\n")
            for table in documentation['tables']:
                f.write(f"### {table['schema']}.{table['name']}\n")
                f.write(f"{table['description'] or 'No description'}\n\n")
                f.write(f"**Rows**: {table['row_count'] or 0}\n\n")
                
                if table['columns']:
                    f.write("| Column | Type | Nullable | Description |\n")
                    f.write("|--------|------|----------|-------------|\n")
                    for col in table['columns']:
                        nullable = "Yes" if col['nullable'] else "No"
                        f.write(f"| {col['name']} | {col['data_type']} | {nullable} | {col['description'] or ''} |\n")
                f.write("\n")
            
            # Views
            f.write("## Views\n\n")
            for view in documentation['views']:
                f.write(f"- **{view['schema']}.{view['name']}**: {view['description'] or 'No description'}\n")
            
            # Procedures
            f.write("\n## Stored Procedures\n\n")
            for proc in documentation['procedures']:
                f.write(f"- **{proc['schema']}.{proc['name']}**: {proc['description'] or 'No description'}\n")
        
        print(f"📄 Markdown report saved to: {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate database documentation')
    parser.add_argument('--environment', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Environment to document')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both',
                       help='Output format')
    
    args = parser.parse_args()
    
    config = get_config(args.environment)
    if not config['connection_string']:
        print(f"❌ No connection string for {args.environment}")
        exit(1)
    
    documenter = DatabaseDocumenter(config['connection_string'])
    documentation = documenter.generate_schema_documentation()
    
    if args.format in ['json', 'both']:
        documenter.save_documentation(documentation)
    
    if args.format in ['markdown', 'both']:
        documenter.generate_markdown_report(documentation)
    
    print("✅ Documentation generation completed!")

if __name__ == "__main__":
    main()
