-- First, let's see the actual table structure
-- Run this to see what columns exist:
SELECT TOP 1 * FROM LeadSources;

-- If you see the columns, use this corrected INSERT:
-- (Adjust column names based on what you see above)

-- Most likely it's just SourceCode and Description, without SourceName
IF NOT EXISTS (SELECT 1 FROM LeadSources WHERE SourceCode = 'whatsapp_qr')
BEGIN
    INSERT INTO LeadSources (SourceCode, Description, IsActive)
    VALUES ('whatsapp_qr', 'Lead submitted via WhatsApp after scanning QR code', 1);
    PRINT '✅ Added whatsapp_qr source code';
END

IF NOT EXISTS (SELECT 1 FROM LeadSources WHERE SourceCode = 'employee_scan')
BEGIN
    INSERT INTO LeadSources (SourceCode, Description, IsActive)
    VALUES ('employee_scan', 'Lead scanned by employee using mobile app', 1);
    PRINT '✅ Added employee_scan source code';
END

-- Show all sources
SELECT * FROM LeadSources;

