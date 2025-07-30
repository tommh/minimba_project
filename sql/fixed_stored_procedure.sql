USE [EnergyCertificate]
GO
/****** Object:  StoredProcedure [ev_enova].[Get_Enova_API_Parameters]    Script Date: 30.07.2025 15:45:33 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [ev_enova].[Get_Enova_API_Parameters] 
    @TopRows INT = 10  -- valgfri parameter med default 10
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
        --AND TypeRegistrering = 'Advanced'
        
        -- Exclude certificates that have been successfully processed
        AND NOT EXISTS (
            SELECT 1 FROM [ev_enova].[EnovaApi_Energiattest_url_log] EU
            WHERE EU.[CertificateID] = IH.[CertificateID]
              AND EU.status_message != 'Pending'  -- Any successful/failed processing
        )
        
        -- Also exclude certificates with recent pending records (currently being processed)
        AND NOT EXISTS (
            SELECT 1 FROM [ev_enova].[EnovaApi_Energiattest_url_log] EU
            WHERE EU.[CertificateID] = IH.[CertificateID]
              AND EU.status_message = 'Pending'
              AND EU.LogDate > DATEADD(HOUR, -1, GETDATE())  -- Recent pending (last hour)
        )
        
    ORDER BY IH.Utstedelsesdato DESC;
END
