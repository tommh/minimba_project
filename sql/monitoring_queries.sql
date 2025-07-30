-- Query scripts for monitoring Enova API processing
-- Use these queries to monitor and analyze API processing results

USE [EnergyCertificate]
GO

-- =====================================================
-- 1. Current processing status overview
-- =====================================================
SELECT 
    status_message,
    COUNT(*) as call_count,
    SUM(ISNULL(records_returned, 0)) as total_records_returned,
    AVG(CAST(ISNULL(records_returned, 0) AS FLOAT)) as avg_records_per_call,
    MIN(LogDate) as first_call,
    MAX(LogDate) as last_call
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
GROUP BY status_message
ORDER BY call_count DESC;

-- =====================================================
-- 2. Recent processing batches (last 24 hours)
-- =====================================================
SELECT 
    CAST(LogDate AS DATE) as processing_date,
    DATEPART(HOUR, LogDate) as processing_hour,
    status_message,
    COUNT(*) as calls,
    SUM(ISNULL(records_returned, 0)) as records_returned
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
WHERE LogDate >= DATEADD(DAY, -1, GETDATE())
GROUP BY CAST(LogDate AS DATE), DATEPART(HOUR, LogDate), status_message
ORDER BY processing_date DESC, processing_hour DESC, calls DESC;

-- =====================================================
-- 3. Certificates that returned no data
-- =====================================================
SELECT TOP 20
    l.CertificateID,
    l.kommunenummer,
    l.gardsnummer,
    l.bruksnummer,
    l.seksjonsnummer,
    l.bruksenhetnummer,
    l.bygningsnummer,
    l.Attestnummer,
    l.status_message,
    l.LogDate
FROM [ev_enova].[EnovaApi_Energiattest_url_log] l
WHERE l.status_message = 'No records found'
ORDER BY l.LogDate DESC;

-- =====================================================
-- 4. Error analysis - failed API calls
-- =====================================================
SELECT TOP 20
    l.CertificateID,
    l.status_message,
    l.LogDate,
    l.kommunenummer,
    l.gardsnummer,
    l.bruksnummer,
    l.Attestnummer
FROM [ev_enova].[EnovaApi_Energiattest_url_log] l
WHERE l.status_message LIKE 'Error:%'
ORDER BY l.LogDate DESC;

-- =====================================================
-- 5. Success rate analysis
-- =====================================================
WITH StatusSummary AS (
    SELECT 
        CASE 
            WHEN status_message = 'Success' THEN 'Success'
            WHEN status_message = 'No records found' THEN 'No Data'
            WHEN status_message LIKE 'Error:%' THEN 'Error'
            ELSE 'Other'
        END as status_category,
        COUNT(*) as count
    FROM [ev_enova].[EnovaApi_Energiattest_url_log]
    GROUP BY CASE 
            WHEN status_message = 'Success' THEN 'Success'
            WHEN status_message = 'No records found' THEN 'No Data'
            WHEN status_message LIKE 'Error:%' THEN 'Error'
            ELSE 'Other'
        END
)
SELECT 
    status_category,
    count,
    CAST(count * 100.0 / SUM(count) OVER() AS DECIMAL(5,2)) as percentage
FROM StatusSummary
ORDER BY count DESC;

-- =====================================================
-- 6. Processing performance by hour of day
-- =====================================================
SELECT 
    DATEPART(HOUR, LogDate) as hour_of_day,
    COUNT(*) as api_calls,
    SUM(ISNULL(records_returned, 0)) as total_records,
    AVG(CAST(ISNULL(records_returned, 0) AS FLOAT)) as avg_records_per_call,
    SUM(CASE WHEN status_message = 'Success' THEN 1 ELSE 0 END) as successful_calls
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
WHERE LogDate >= DATEADD(DAY, -7, GETDATE()) -- Last 7 days
GROUP BY DATEPART(HOUR, LogDate)
ORDER BY hour_of_day;

-- =====================================================
-- 7. Top performing certificates (most data returned)
-- =====================================================
SELECT TOP 20
    l.CertificateID,
    l.kommunenummer,
    l.gardsnummer,
    l.bruksnummer,
    l.Attestnummer,
    l.records_returned,
    l.LogDate,
    -- Count how many actual records were saved
    (SELECT COUNT(*) 
     FROM [ev_enova].[EnovaApi_Energiattest_url] u 
     WHERE u.CertificateID = l.CertificateID) as records_saved
FROM [ev_enova].[EnovaApi_Energiattest_url_log] l
WHERE l.status_message = 'Success' 
  AND l.records_returned > 0
ORDER BY l.records_returned DESC;

-- =====================================================
-- 8. Certificates pending processing
-- =====================================================
SELECT 
    COUNT(*) as pending_certificates
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
WHERE status_message = 'Pending';

-- Show some examples of pending certificates
SELECT TOP 10
    CertificateID,
    kommunenummer,
    gardsnummer,
    bruksnummer,
    Attestnummer,
    LogDate
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
WHERE status_message = 'Pending'
ORDER BY LogDate DESC;

-- =====================================================
-- 9. Daily processing summary (last 30 days)
-- =====================================================
SELECT 
    CAST(LogDate AS DATE) as processing_date,
    COUNT(*) as total_calls,
    SUM(CASE WHEN status_message = 'Success' THEN 1 ELSE 0 END) as successful_calls,
    SUM(CASE WHEN status_message = 'No records found' THEN 1 ELSE 0 END) as no_data_calls,
    SUM(CASE WHEN status_message LIKE 'Error:%' THEN 1 ELSE 0 END) as error_calls,
    SUM(ISNULL(records_returned, 0)) as total_records_returned,
    -- Calculate success rate
    CAST(SUM(CASE WHEN status_message = 'Success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as success_rate_percent
FROM [ev_enova].[EnovaApi_Energiattest_url_log]
WHERE LogDate >= DATEADD(DAY, -30, GETDATE())
GROUP BY CAST(LogDate AS DATE)
ORDER BY processing_date DESC;

-- =====================================================
-- 10. Certificates with mismatched data 
-- (logged vs actually saved)
-- =====================================================
SELECT 
    l.CertificateID,
    l.records_returned as logged_records,
    COUNT(u.EnovaApiImportID) as actually_saved_records,
    l.records_returned - COUNT(u.EnovaApiImportID) as difference,
    l.status_message,
    l.LogDate
FROM [ev_enova].[EnovaApi_Energiattest_url_log] l
LEFT JOIN [ev_enova].[EnovaApi_Energiattest_url] u ON l.CertificateID = u.CertificateID
WHERE l.status_message = 'Success' AND l.records_returned > 0
GROUP BY l.CertificateID, l.records_returned, l.status_message, l.LogDate
HAVING l.records_returned != COUNT(u.EnovaApiImportID)
ORDER BY difference DESC;

PRINT '============================================='
PRINT 'API Processing Monitoring Queries Complete'
PRINT '============================================='
PRINT ''
PRINT 'Use these queries to monitor:'
PRINT '• Processing success rates'
PRINT '• Error patterns'
PRINT '• Performance trends'
PRINT '• Data quality issues'
