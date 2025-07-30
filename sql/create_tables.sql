-- Database tables for Enova Energy Certificate API processing
-- Run this script to create the required tables and stored procedure

USE [EnergyCertificate]
GO

-- Create schema if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'ev_enova')
BEGIN
    EXEC('CREATE SCHEMA [ev_enova]')
END
GO

-- =====================================================
-- Table: EnovaApi_Energiattest_url_log
-- Purpose: Log all API parameter calls for tracking
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EnovaApi_Energiattest_url_log' AND xtype='U')
BEGIN
    CREATE TABLE [ev_enova].[EnovaApi_Energiattest_url_log](
        [EnovaAPILogID] [bigint] IDENTITY(1,1) NOT NULL,
        [CertificateID] [bigint] NOT NULL,
        [LogDate] [datetime] NOT NULL,
        [kommunenummer] [nvarchar](20) NULL,
        [gardsnummer] [nvarchar](20) NULL,
        [bruksnummer] [nvarchar](20) NULL,
        [seksjonsnummer] [nvarchar](20) NULL,
        [bruksenhetnummer] [nvarchar](50) NULL,
        [bygningsnummer] [nvarchar](50) NULL,
        [records_returned] [int] NULL,
        [status_message] [nvarchar](255) NULL,
        [Created] [datetime] NOT NULL,
        [Attestnummer] [nvarchar](50) NOT NULL,
     CONSTRAINT [PK_EnovaApi_Energiattest_url_log] PRIMARY KEY CLUSTERED 
    (
        [EnovaAPILogID] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
    
    PRINT 'Created table [ev_enova].[EnovaApi_Energiattest_url_log]'
END
ELSE
BEGIN
    PRINT 'Table [ev_enova].[EnovaApi_Energiattest_url_log] already exists'
END
GO

-- =====================================================
-- Table: EnovaApi_Energiattest_url
-- Purpose: Store API response data from Energiattest API
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='EnovaApi_Energiattest_url' AND xtype='U')
BEGIN
    CREATE TABLE [ev_enova].[EnovaApi_Energiattest_url](
        [EnovaApiImportID] [bigint] IDENTITY(1,1) NOT NULL,
        [ImportDate] [datetime] NOT NULL,
        [CertificateID] [bigint] NULL,
        [paramKommunenummer] [nvarchar](20) NULL,
        [paramGardsnummer] [nvarchar](20) NULL,
        [paramBruksnummer] [nvarchar](20) NULL,
        [paramSeksjonsnummer] [nvarchar](20) NULL,
        [paramBruksenhetnummer] [nvarchar](50) NULL,
        [paramBygningsnummer] [nvarchar](50) NULL,
        [attestnummer] [nvarchar](100) NULL,
        [merkenummer] [nvarchar](100) NULL,
        [bruksareal] [decimal](12, 2) NULL,
        [energikarakter] [nvarchar](100) NULL,
        [oppvarmingskarakter] [nvarchar](100) NULL,
        [attest_url] [nvarchar](1000) NULL,
        [matrikkel_kommunenummer] [nvarchar](20) NULL,
        [matrikkel_gardsnummer] [nvarchar](20) NULL,
        [matrikkel_bruksnummer] [nvarchar](20) NULL,
        [matrikkel_festenummer] [nvarchar](20) NULL,
        [matrikkel_seksjonsnummer] [nvarchar](20) NULL,
        [matrikkel_andelsnummer] [nvarchar](50) NULL,
        [matrikkel_bruksenhetsnummer] [nvarchar](50) NULL,
        [bygg_bygningsnummer] [nvarchar](50) NULL,
        [bygg_byggear] [nvarchar](4) NULL,
        [bygg_kategori] [nvarchar](100) NULL,
        [bygg_type] [nvarchar](100) NULL,
        [utstedelsesdato] [datetime] NULL,
        [adresse_gatenavn] [nvarchar](100) NULL,
        [adresse_postnummer] [nvarchar](5) NULL,
        [adresse_poststed] [nvarchar](100) NULL,
        [registering_RegisteringType] [nvarchar](10) NULL,
        [registering_BeregnetLevertEnergiTotaltkWhm2] [decimal](12, 2) NULL,
        [registering_BeregnetLevertEnergiTotaltkWh] [decimal](12, 2) NULL,
        [registering_HarEnergivurdering] [nvarchar](5) NULL,
        [registering_Energivurderingdato] [datetime] NULL,
        [registering_BeregnetFossilandel] [decimal](12, 2) NULL,
        [registering_Materialvalg] [nvarchar](20) NULL,
        [OrganisasjonsNummer] [nvarchar](50) NULL,
        [Created] [datetime] NOT NULL,
     CONSTRAINT [PK_EnovaApi_Energiattest_url] PRIMARY KEY CLUSTERED 
    (
        [EnovaApiImportID] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
    
    PRINT 'Created table [ev_enova].[EnovaApi_Energiattest_url]'
END
ELSE
BEGIN
    PRINT 'Table [ev_enova].[EnovaApi_Energiattest_url] already exists'
END
GO

-- =====================================================
-- Table: Certificate (Sample structure - adjust as needed)
-- Purpose: Main certificate table that feeds the API calls
-- =====================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Certificate' AND xtype='U')
BEGIN
    CREATE TABLE [ev_enova].[Certificate](
        [CertificateID] [bigint] IDENTITY(1,1) NOT NULL,
        [Knr] [int] NULL,
        [Gnr] [int] NULL,
        [Bnr] [int] NULL,
        [Snr] [int] NULL,
        [BruksEnhetsNummer] [nvarchar](50) NULL,
        [Bygningsnummer] [nvarchar](50) NULL,
        [Attestnummer] [nvarchar](100) NULL,
        [Utstedelsesdato] [datetime] NULL,
        [TypeRegistrering] [nvarchar](20) NULL,
        [Created] [datetime] NOT NULL DEFAULT GETDATE(),
        [Updated] [datetime] NULL,
     CONSTRAINT [PK_Certificate] PRIMARY KEY CLUSTERED 
    (
        [CertificateID] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
    
    PRINT 'Created table [ev_enova].[Certificate]'
END
ELSE
BEGIN
    PRINT 'Table [ev_enova].[Certificate] already exists'
END
GO

-- =====================================================
-- Stored Procedure: Get_Enova_API_Parameters
-- Purpose: Get parameters for API calls
-- =====================================================
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[ev_enova].[Get_Enova_API_Parameters]') AND type in (N'P', N'PC'))
BEGIN
    DROP PROCEDURE [ev_enova].[Get_Enova_API_Parameters]
    PRINT 'Dropped existing procedure [ev_enova].[Get_Enova_API_Parameters]'
END
GO

CREATE PROCEDURE [ev_enova].[Get_Enova_API_Parameters] 
    @TopRows INT = 10  -- Optional parameter with default 10
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP (@TopRows)
           IH.CertificateID AS CertificateID,
           RIGHT('0000' + CAST(IH.Knr AS VARCHAR(4)), 4) AS kommunenummer,           
           IH.Gnr AS gardsnummer,
           IH.Bnr AS bruksnummer,
           IH.Snr AS seksjonsnummer,
           IH.BruksEnhetsNummer AS bruksenhetnummer,
           IH.Bygningsnummer AS bygningsnummer,
           IH.[Attestnummer]
    FROM [ev_enova].[Certificate] IH
    WHERE
        YEAR(IH.Utstedelsesdato) = 2025
        --AND LEN(IH.Attestnummer) = 36
        AND TypeRegistrering = 'Schema'
        AND NOT EXISTS (
            SELECT 1 FROM [ev_enova].[EnovaApi_Energiattest_url_log] EU
            WHERE EU.[CertificateID] = IH.[CertificateID]
        )
    ORDER BY IH.Utstedelsesdato DESC;
END
GO

PRINT 'Created stored procedure [ev_enova].[Get_Enova_API_Parameters]'
GO

-- =====================================================
-- Create indexes for better performance
-- =====================================================

-- Index on CertificateID in log table for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnovaApi_Log_CertificateID')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnovaApi_Log_CertificateID] ON [ev_enova].[EnovaApi_Energiattest_url_log]
    (
        [CertificateID] ASC
    )
    PRINT 'Created index [IX_EnovaApi_Log_CertificateID]'
END
GO

-- Index on CertificateID in main table for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnovaApi_Url_CertificateID')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnovaApi_Url_CertificateID] ON [ev_enova].[EnovaApi_Energiattest_url]
    (
        [CertificateID] ASC
    )
    PRINT 'Created index [IX_EnovaApi_Url_CertificateID]'
END
GO

-- Index on Utstedelsesdato and TypeRegistrering for the stored procedure
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Certificate_UtstedelsesdatoType')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Certificate_UtstedelsesdatoType] ON [ev_enova].[Certificate]
    (
        [Utstedelsesdato] DESC,
        [TypeRegistrering] ASC
    )
    PRINT 'Created index [IX_Certificate_UtstedelsesdatoType]'
END
GO

-- Index on Attestnummer for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_EnovaApi_Url_Attestnummer')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_EnovaApi_Url_Attestnummer] ON [ev_enova].[EnovaApi_Energiattest_url]
    (
        [attestnummer] ASC
    )
    PRINT 'Created index [IX_EnovaApi_Url_Attestnummer]'
END
GO

PRINT ''
PRINT '========================================='
PRINT 'Database setup completed successfully!'
PRINT '========================================='
PRINT 'Created tables:'
PRINT '  - [ev_enova].[Certificate]'
PRINT '  - [ev_enova].[EnovaApi_Energiattest_url_log]'
PRINT '  - [ev_enova].[EnovaApi_Energiattest_url]'
PRINT ''
PRINT 'Created stored procedure:'
PRINT '  - [ev_enova].[Get_Enova_API_Parameters]'
PRINT ''
PRINT 'Created indexes for performance optimization'
PRINT '========================================='
