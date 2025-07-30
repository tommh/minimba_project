-- Sample data for testing the Enova API client
-- Run this after creating the tables to insert test data

USE [EnergyCertificate]
GO

-- =====================================================
-- Insert sample data into Certificate table for testing
-- =====================================================

-- Clear existing test data if any
DELETE FROM [ev_enova].[Certificate] WHERE [Attestnummer] LIKE 'TEST-%'
GO

-- Insert sample certificates that match the API requirements
INSERT INTO [ev_enova].[Certificate] (
    [Knr], [Gnr], [Bnr], [Snr], [BruksEnhetsNummer], [Bygningsnummer], 
    [Attestnummer], [Utstedelsesdato], [TypeRegistrering]
) VALUES 
-- Sample data based on your original API example
(301, 105, 61, 0, 'H0202', '81309310', 'TEST-b9075f38-0762-4e52-833c-c4b8e684d3d7', '2025-03-20 09:19:51', 'Schema'),
(301, 105, 61, 0, 'H0202', '81309310', 'TEST-00028632-f111-4721-b582-d7ad5d09f7e9', '2023-04-14 08:11:43', 'Schema'),
(301, 105, 61, 0, 'H0202', '81309310', 'TEST-02d61d13-159f-458b-a440-a8f2778e88d8', '2023-04-13 09:06:31', 'Schema'),
(301, 105, 61, 0, 'H0202', '81309310', 'TEST-c99d2d6b-e74d-4f99-8289-6f3495194343', '2023-03-31 07:43:08', 'Schema'),
(301, 105, 61, 0, 'H0202', '', 'TEST-A2015-561357', '2015-05-29 19:27:44', 'Schema'),

-- Additional test data for different scenarios
(101, 200, 50, 1, 'H0101', '12345678', 'TEST-12345678-1234-5678-9012-123456789012', '2025-01-15 10:30:00', 'Schema'),
(102, 201, 51, 0, 'H0201', '87654321', 'TEST-87654321-8765-4321-0987-654321098765', '2025-02-20 14:45:00', 'Schema'),
(103, 202, 52, 2, 'H0301', '11111111', 'TEST-11111111-1111-1111-1111-111111111111', '2025-03-10 08:15:00', 'Schema'),

-- Test data with missing optional fields
(104, 203, 53, 0, NULL, NULL, 'TEST-22222222-2222-2222-2222-222222222222', '2025-04-05 16:20:00', 'Schema'),
(105, 204, 54, 0, 'H0401', '33333333', 'TEST-33333333-3333-3333-3333-333333333333', '2025-05-12 11:10:00', 'Schema')
GO

PRINT 'Inserted sample test data into [ev_enova].[Certificate]'

-- Show the inserted data
SELECT 
    CertificateID,
    RIGHT('0000' + CAST(Knr AS VARCHAR(4)), 4) AS kommunenummer,
    Gnr AS gardsnummer,
    Bnr AS bruksnummer,
    Snr AS seksjonsnummer,
    BruksEnhetsNummer AS bruksenhetnummer,
    Bygningsnummer AS bygningsnummer,
    Attestnummer,
    Utstedelsesdato,
    TypeRegistrering
FROM [ev_enova].[Certificate] 
WHERE [Attestnummer] LIKE 'TEST-%'
ORDER BY Utstedelsesdato DESC
GO

-- =====================================================
-- Test the stored procedure
-- =====================================================
PRINT ''
PRINT 'Testing stored procedure with @TopRows = 5:'
PRINT '============================================='

EXEC [ev_enova].[Get_Enova_API_Parameters] @TopRows = 5
GO

-- =====================================================
-- Verification queries
-- =====================================================
PRINT ''
PRINT 'Verification queries:'
PRINT '===================='

-- Count total certificates
SELECT 'Total Certificates' AS Description, COUNT(*) AS Count
FROM [ev_enova].[Certificate]

UNION ALL

-- Count test certificates
SELECT 'Test Certificates' AS Description, COUNT(*) AS Count
FROM [ev_enova].[Certificate] 
WHERE [Attestnummer] LIKE 'TEST-%'

UNION ALL

-- Count 2025 certificates
SELECT '2025 Certificates' AS Description, COUNT(*) AS Count
FROM [ev_enova].[Certificate] 
WHERE YEAR(Utstedelsesdato) = 2025

UNION ALL

-- Count Schema type certificates
SELECT 'Schema Type Certificates' AS Description, COUNT(*) AS Count
FROM [ev_enova].[Certificate] 
WHERE TypeRegistrering = 'Schema'
GO

PRINT ''
PRINT '========================================='
PRINT 'Sample data setup completed!'
PRINT '========================================='
PRINT ''
PRINT 'You can now test the API client with:'
PRINT '  python tests/test_api_client.py --rows 5'
PRINT ''
PRINT 'To clean up test data later, run:'
PRINT '  DELETE FROM [ev_enova].[Certificate] WHERE [Attestnummer] LIKE ''TEST-%'''
PRINT '========================================='
