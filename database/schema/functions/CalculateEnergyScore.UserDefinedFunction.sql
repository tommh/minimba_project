-- User-defined function: Calculate energy efficiency score
-- Returns a numeric score based on energy rating

USE [EnergyCertificate]
GO

-- Drop function if it exists
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'FN' AND name = 'CalculateEnergyScore' AND schema_id = SCHEMA_ID('ev_enova'))
BEGIN
    DROP FUNCTION [ev_enova].[CalculateEnergyScore]
    PRINT 'Dropped existing function: CalculateEnergyScore'
END
GO

-- Create the function
CREATE FUNCTION [ev_enova].[CalculateEnergyScore]
(
    @EnergyRating NVARCHAR(10)
)
RETURNS INT
AS
BEGIN
    DECLARE @Score INT
    
    SET @Score = CASE UPPER(LTRIM(RTRIM(@EnergyRating)))
        WHEN 'A' THEN 100
        WHEN 'B' THEN 85
        WHEN 'C' THEN 70
        WHEN 'D' THEN 55
        WHEN 'E' THEN 40
        WHEN 'F' THEN 25
        WHEN 'G' THEN 10
        ELSE 0  -- Unknown rating
    END
    
    RETURN @Score
END
GO

-- Add function description
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Calculates a numeric energy efficiency score (0-100) based on energy rating letter',
    @level0type = N'SCHEMA',
    @level0name = N'ev_enova',
    @level1type = N'FUNCTION',
    @level1name = N'CalculateEnergyScore'
GO

PRINT 'Created function: ev_enova.CalculateEnergyScore'
