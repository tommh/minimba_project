-- Index: Certificate table performance indexes
-- Improve query performance for common operations

USE [EnergyCertificate]
GO

-- Index for Certificate lookups by EnovaReference
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Certificate_EnovaReference')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Certificate_EnovaReference] 
    ON [ev_enova].[Certificate] ([EnovaReference])
    WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, 
          DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
    
    PRINT 'Created index: IX_Certificate_EnovaReference'
END
ELSE
BEGIN
    PRINT 'Index IX_Certificate_EnovaReference already exists'
END
GO

-- Index for Certificate lookups by date range
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Certificate_CreatedDate')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Certificate_CreatedDate] 
    ON [ev_enova].[Certificate] ([CreatedDate])
    INCLUDE ([EnovaReference], [BuildingType])
    WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, 
          DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
    
    PRINT 'Created index: IX_Certificate_CreatedDate'
END
ELSE
BEGIN
    PRINT 'Index IX_Certificate_CreatedDate already exists'
END
GO

-- Index for EnergyLabelID foreign key lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Certificate_EnergyLabelID')
BEGIN
    CREATE NONCLUSTERED INDEX [IX_Certificate_EnergyLabelID] 
    ON [ev_enova].[Certificate] ([EnergyLabelID])
    WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, 
          DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON)
    
    PRINT 'Created index: IX_Certificate_EnergyLabelID'
END
ELSE
BEGIN
    PRINT 'Index IX_Certificate_EnergyLabelID already exists'
END
GO

PRINT 'Certificate indexes deployment completed'
