-- Migration: Initial Schema Creation
-- Description: Creates the initial ev_enova schema and core objects
-- Author: Database Team
-- Date: 2025-08-01
-- Version: 1.0.0

-- This migration creates the foundation for the Energy Certificate database

USE [EnergyCertificate]
GO

-- Create version tracking table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SchemaVersions' AND schema_id = SCHEMA_ID('dbo'))
BEGIN
    CREATE TABLE [dbo].[SchemaVersions] (
        [Version] NVARCHAR(50) PRIMARY KEY,
        [Description] NVARCHAR(255) NOT NULL,
        [AppliedDate] DATETIME2 DEFAULT GETDATE(),
        [AppliedBy] NVARCHAR(100) DEFAULT SUSER_SNAME()
    );
    
    PRINT 'Created SchemaVersions table for migration tracking';
END
GO

-- Record this migration
IF NOT EXISTS (SELECT * FROM [dbo].[SchemaVersions] WHERE [Version] = '001_initial_schema')
BEGIN
    INSERT INTO [dbo].[SchemaVersions] ([Version], [Description])
    VALUES ('001_initial_schema', 'Initial schema creation with ev_enova schema and core tables');
    
    PRINT 'Recorded migration: 001_initial_schema';
END
ELSE
BEGIN
    PRINT 'Migration 001_initial_schema already applied';
END
GO

-- Create ev_enova schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ev_enova')
BEGIN
    CREATE SCHEMA [ev_enova] AUTHORIZATION [dbo];
    PRINT 'Created ev_enova schema';
END
ELSE
BEGIN
    PRINT 'ev_enova schema already exists';
END
GO

-- Add schema description
IF NOT EXISTS (
    SELECT * FROM sys.extended_properties 
    WHERE major_id = SCHEMA_ID('ev_enova') 
    AND name = 'MS_Description'
)
BEGIN
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Schema for energy certificate and Enova API related objects',
        @level0type = N'SCHEMA',
        @level0name = N'ev_enova';
    
    PRINT 'Added description to ev_enova schema';
END
GO

PRINT 'Migration 001_initial_schema completed successfully';
