-- Check if whatsapp_qr source exists
IF NOT EXISTS (SELECT 1 FROM LeadSources WHERE SourceCode = 'whatsapp_qr')
BEGIN
    INSERT INTO LeadSources (SourceCode, SourceName, Description, IsActive)
    VALUES ('whatsapp_qr', 'WhatsApp QR', 'Lead submitted via WhatsApp after scanning QR code', 1);
    PRINT '✅ Added whatsapp_qr source code';
END
ELSE
BEGIN
    PRINT 'ℹ️ whatsapp_qr source code already exists';
END
GO

-- Also check for employee_scan source
IF NOT EXISTS (SELECT 1 FROM LeadSources WHERE SourceCode = 'employee_scan')
BEGIN
    INSERT INTO LeadSources (SourceCode, SourceName, Description, IsActive)
    VALUES ('employee_scan', 'Employee Scan', 'Lead scanned by employee using mobile app', 1);
    PRINT '✅ Added employee_scan source code';
END
ELSE
BEGIN
    PRINT 'ℹ️ employee_scan source code already exists';
END
GO

-- Show all sources
SELECT SourceCode, SourceName, Description FROM LeadSources;

