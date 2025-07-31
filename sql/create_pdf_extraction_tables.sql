-- PDF Text Extraction Database Setup
-- Creates the stored procedure and table for PDF text extraction

USE [EnergyCertificate]
GO

-- =====================================================
-- Table: EnergyLabelFileExtract
-- Purpose: Store extracted text from PDF files
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EnergyLabelFileExtract' AND xtype='U')
BEGIN
    CREATE TABLE [ev_enova].[EnergyLabelFileExtract](
        [file_id] [int] NOT NULL,
        [filename] [nvarchar](255) NOT NULL,
        [extracted_text] [nvarchar](max) NULL,
        [extraction_date] [datetime] NOT NULL,
        [extraction_method] [nvarchar](100) NULL,
        [extraction_status] [nvarchar](50) NULL,
        [character_count] [int] NULL,
        [page_count] [int] NULL,
     CONSTRAINT [PK_EnergyLabelFileExtract] PRIMARY KEY CLUSTERED 
    (
        [file_id] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
    
    PRINT 'Created table [ev_enova].[EnergyLabelFileExtract]'
END
ELSE
BEGIN
    PRINT 'Table [ev_enova].[EnergyLabelFileExtract] already exists'
END
GO

-- =====================================================
-- Stored Procedure: Get_PDF_for_Extract
-- Purpose: Get PDF files that need text extraction
-- =====================================================
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[ev_enova].[Get_PDF_for_Extract]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [ev_enova].[Get_PDF_for_Extract]
    PRINT 'Dropped existing procedure [ev_enova].[Get_PDF_for_Extract]'
END
GO

CREATE OR ALTER PROCEDURE [ev_enova].[Get_PDF_for_Extract] 
    @TopRows INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SELECT TOP (@TopRows) 
            p.[file_id], 
            p.[filename], 
            p.[full_path]
        FROM [ev_enova].[EnergylabelIDFiles] p
        WHERE NOT EXISTS (
            SELECT 1 
            FROM [ev_enova].[EnergyLabelFileExtract] fe 
            WHERE fe.[file_id] = p.[file_id]
        )
        AND p.[file_extension] = '.pdf'  -- Only PDF files
        ORDER BY p.[filename];
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO

PRINT 'Created stored procedure [ev_enova].[Get_PDF_for_Extract]'
GO

-- =====================================================
-- Create indexes for better performance
-- =====================================================

-- Index on file_id in extract table for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnergyLabelFileExtract_FileId')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnergyLabelFileExtract_FileId] ON [ev_enova].[EnergyLabelFileExtract]
    (
        [file_id] ASC
    )
    PRINT 'Created index [IX_EnergyLabelFileExtract_FileId]'
END
GO

-- Index on extraction_date for reporting
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnergyLabelFileExtract_ExtractionDate')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnergyLabelFileExtract_ExtractionDate] ON [ev_enova].[EnergyLabelFileExtract]
    (
        [extraction_date] DESC
    )
    PRINT 'Created index [IX_EnergyLabelFileExtract_ExtractionDate]'
END
GO

-- Index on extraction_status for filtering
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnergyLabelFileExtract_Status')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnergyLabelFileExtract_Status] ON [ev_enova].[EnergyLabelFileExtract]
    (
        [extraction_status] ASC
    )
    PRINT 'Created index [IX_EnergyLabelFileExtract_Status]'
END
GO

PRINT ''
PRINT '========================================='
PRINT 'PDF Text Extraction Setup Complete!'
PRINT '========================================='
PRINT 'Created:'
PRINT '  - [ev_enova].[EnergyLabelFileExtract] table'
PRINT '  - [ev_enova].[Get_PDF_for_Extract] procedure'
PRINT '  - Performance indexes'
PRINT ''
PRINT 'Ready to extract text from PDF files!'
PRINT '========================================='
