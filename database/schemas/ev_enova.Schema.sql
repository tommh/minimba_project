-- Schema: ev_enova
-- Description: Energy certificate and Enova-related objects
-- Created: 2025-08-01
-- Note: Assumes target database is already selected

-- Create the ev_enova schema
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ev_enova')
BEGIN
    CREATE SCHEMA [ev_enova] AUTHORIZATION [dbo]
    PRINT 'Schema [ev_enova] created successfully'
END
ELSE
BEGIN
    PRINT 'Schema [ev_enova] already exists'
END
GO

-- Add description for documentation
IF NOT EXISTS (
    SELECT * FROM sys.extended_properties 
    WHERE major_id = SCHEMA_ID('ev_enova') 
    AND name = 'MS_Description'
)
BEGIN
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Schema for energy certificate and Enova-related objects',
        @level0type = N'SCHEMA',
        @level0name = N'ev_enova'
END
GO
