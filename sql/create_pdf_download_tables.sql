-- Create log table for PDF download attempts
USE [EnergyCertificate]
GO

-- Create log table for PDF download attempts
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='PDF_Download_Log' AND xtype='U')
BEGIN
    CREATE TABLE [ev_enova].[PDF_Download_Log](
        [download_log_id] [bigint] IDENTITY(1,1) NOT NULL,
        [attest_url] [nvarchar](1000) NOT NULL,
        [filename] [nvarchar](255) NULL,
        [download_date] [datetime] NOT NULL,
        [status] [nvarchar](50) NOT NULL, -- 'Success', 'Failed', 'Invalid URL', 'File Too Large', etc.
        [status_message] [nvarchar](500) NULL,
        [file_size] [bigint] NULL,
        [http_status_code] [int] NULL,
        [created] [datetime] NOT NULL DEFAULT GETDATE(),
     CONSTRAINT [PK_PDF_Download_Log] PRIMARY KEY CLUSTERED 
    (
        [download_log_id] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
    
    PRINT 'Created table [ev_enova].[PDF_Download_Log]'
END
ELSE
BEGIN
    PRINT 'Table [ev_enova].[PDF_Download_Log] already exists'
END
GO

-- Create index on attest_url for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_PDF_Download_Log_AttestUrl')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_PDF_Download_Log_AttestUrl] ON [ev_enova].[PDF_Download_Log]
    (
        [attest_url] ASC
    )
    PRINT 'Created index [IX_PDF_Download_Log_AttestUrl]'
END
GO

-- Create the stored procedure
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[ev_enova].[Get_Enova_BLOB_url]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [ev_enova].[Get_Enova_BLOB_url]
    PRINT 'Dropped existing procedure [ev_enova].[Get_Enova_BLOB_url]'
END
GO

CREATE PROCEDURE [ev_enova].[Get_Enova_BLOB_url] 
    @TopRows INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP (@TopRows)
        ea.[attest_url],
        RIGHT(PARSENAME(REPLACE(ea.[attest_url], '/', '.'), 1), 40) as expected_filename
    FROM [EnergyCertificate].[ev_enova].[EnovaApi_Energiattest_url] ea
    WHERE NOT EXISTS (
        SELECT 1
        FROM [EnergyCertificate].[ev_enova].[EnergylabelIDFiles] f
        WHERE f.[filename] = RIGHT(PARSENAME(REPLACE(ea.[attest_url], '/', '.'), 1), 40)
    )
    AND ea.[attest_url] IS NOT NULL
    -- Exclude URLs we've already attempted to download (optional - remove if you want to retry failed downloads)
    AND NOT EXISTS (
        SELECT 1 
        FROM [ev_enova].[PDF_Download_Log] dl 
        WHERE dl.[attest_url] = ea.[attest_url] 
          AND dl.[status] = 'Success'
    )
    GROUP BY ea.[attest_url];
END
GO

PRINT 'Created stored procedure [ev_enova].[Get_Enova_BLOB_url]'
GO

PRINT ''
PRINT '========================================='
PRINT 'PDF Download Setup Complete!'
PRINT '========================================='
PRINT 'Created:'
PRINT '  - [ev_enova].[PDF_Download_Log] table'
PRINT '  - [ev_enova].[Get_Enova_BLOB_url] procedure'
PRINT ''
PRINT 'Ready to use the Python PDF downloader!'
PRINT '========================================='
