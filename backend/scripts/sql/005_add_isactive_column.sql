-- Add IsActive column to Leads table for soft delete functionality
-- This allows marking leads as inactive without losing data

USE ExhibitionLeads;
GO

-- Check if column already exists
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.Leads')
    AND name = 'IsActive'
)
BEGIN
    -- Add IsActive column with default value TRUE
    ALTER TABLE Leads
    ADD IsActive BIT NOT NULL DEFAULT 1;

    PRINT 'IsActive column added to Leads table successfully.';
END
ELSE
BEGIN
    PRINT 'IsActive column already exists in Leads table.';
END
GO

-- Create index for faster filtering by active leads
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Leads_IsActive' AND object_id = OBJECT_ID('Leads'))
BEGIN
    CREATE INDEX IX_Leads_IsActive ON Leads(IsActive);
    PRINT 'Index IX_Leads_IsActive created successfully.';
END
ELSE
BEGIN
    PRINT 'Index IX_Leads_IsActive already exists.';
END
GO

-- Set all existing leads to active
UPDATE Leads SET IsActive = 1 WHERE IsActive IS NULL;
PRINT 'All existing leads marked as active.';
GO
