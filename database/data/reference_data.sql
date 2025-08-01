-- Sample reference data for Energy Certificate system
-- Insert basic lookup data that the application needs

USE [EnergyCertificate]
GO

-- Energy rating categories
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'EnergyRatings' AND schema_id = SCHEMA_ID('ev_enova'))
BEGIN
    CREATE TABLE [ev_enova].[EnergyRatings] (
        [RatingCode] CHAR(1) PRIMARY KEY,
        [RatingName] NVARCHAR(50) NOT NULL,
        [Description] NVARCHAR(255),
        [SortOrder] INT NOT NULL
    );
    
    INSERT INTO [ev_enova].[EnergyRatings] ([RatingCode], [RatingName], [Description], [SortOrder])
    VALUES 
        ('A', 'A - Excellent', 'Very energy efficient', 1),
        ('B', 'B - Good', 'Energy efficient', 2),
        ('C', 'C - Fairly Good', 'Fairly energy efficient', 3),
        ('D', 'D - Average', 'Average energy efficiency', 4),
        ('E', 'E - Below Average', 'Below average energy efficiency', 5),
        ('F', 'F - Poor', 'Poor energy efficiency', 6),
        ('G', 'G - Very Poor', 'Very poor energy efficiency', 7);
    
    PRINT 'Created and populated EnergyRatings reference table';
END
GO

-- Building types
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'BuildingTypes' AND schema_id = SCHEMA_ID('ev_enova'))
BEGIN
    CREATE TABLE [ev_enova].[BuildingTypes] (
        [TypeID] INT IDENTITY(1,1) PRIMARY KEY,
        [TypeCode] NVARCHAR(20) NOT NULL UNIQUE,
        [TypeName] NVARCHAR(100) NOT NULL,
        [Category] NVARCHAR(50)
    );
    
    INSERT INTO [ev_enova].[BuildingTypes] ([TypeCode], [TypeName], [Category])
    VALUES 
        ('RES_HOUSE', 'Residential House', 'Residential'),
        ('RES_APT', 'Residential Apartment', 'Residential'),
        ('COM_OFFICE', 'Commercial Office', 'Commercial'),
        ('COM_RETAIL', 'Commercial Retail', 'Commercial'),
        ('IND_WAREHOUSE', 'Industrial Warehouse', 'Industrial'),
        ('PUB_SCHOOL', 'Public School', 'Public'),
        ('PUB_HOSPITAL', 'Public Hospital', 'Public');
    
    PRINT 'Created and populated BuildingTypes reference table';
END
GO

-- Processing status codes
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ProcessingStatus' AND schema_id = SCHEMA_ID('ev_enova'))
BEGIN
    CREATE TABLE [ev_enova].[ProcessingStatus] (
        [StatusID] INT IDENTITY(1,1) PRIMARY KEY,
        [StatusCode] NVARCHAR(20) NOT NULL UNIQUE,
        [StatusName] NVARCHAR(50) NOT NULL,
        [Description] NVARCHAR(255),
        [IsActive] BIT DEFAULT 1
    );
    
    INSERT INTO [ev_enova].[ProcessingStatus] ([StatusCode], [StatusName], [Description])
    VALUES 
        ('PENDING', 'Pending', 'Awaiting processing'),
        ('PROCESSING', 'Processing', 'Currently being processed'),
        ('COMPLETED', 'Completed', 'Processing completed successfully'),
        ('ERROR', 'Error', 'Processing failed with error'),
        ('RETRY', 'Retry', 'Marked for retry processing'),
        ('ARCHIVED', 'Archived', 'Archived after processing');
    
    PRINT 'Created and populated ProcessingStatus reference table';
END
GO

PRINT 'Reference data setup completed';
