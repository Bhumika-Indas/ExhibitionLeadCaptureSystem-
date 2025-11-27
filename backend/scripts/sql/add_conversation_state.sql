-- Migration: Add ConversationState to Leads table
-- Purpose: Track conversation flow state for better intent handling
-- Date: 2025-11-26

-- Step 1: Add ConversationState column
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID('Leads')
    AND name = 'ConversationState'
)
BEGIN
    ALTER TABLE Leads
    ADD ConversationState VARCHAR(50) NULL;

    PRINT '✅ Added ConversationState column to Leads table';
END
ELSE
BEGIN
    PRINT '⚠️ ConversationState column already exists';
END
GO

-- Step 2: Set default values for existing leads based on StatusCode
UPDATE Leads
SET ConversationState = CASE
    WHEN StatusCode = 'new' AND PrimaryVisitorName IS NULL THEN 'need_card'
    WHEN StatusCode = 'new' AND PrimaryVisitorName IS NOT NULL AND WhatsAppConfirmed IS NULL THEN 'awaiting_confirmation'
    WHEN StatusCode = 'needs_correction' THEN 'needs_correction'
    WHEN StatusCode = 'confirmed' THEN 'confirmed'
    WHEN StatusCode = 'demo_scheduled' THEN 'scheduled_demo'
    ELSE 'extraction_done'
END
WHERE ConversationState IS NULL;

PRINT '✅ Updated ConversationState for existing leads';
GO

-- Step 3: Create index for performance
IF NOT EXISTS (
    SELECT * FROM sys.indexes
    WHERE name = 'IX_Leads_ConversationState'
    AND object_id = OBJECT_ID('Leads')
)
BEGIN
    CREATE INDEX IX_Leads_ConversationState ON Leads(ConversationState);
    PRINT '✅ Created index on ConversationState';
END
ELSE
BEGIN
    PRINT '⚠️ Index IX_Leads_ConversationState already exists';
END
GO

PRINT '🎉 ConversationState migration completed successfully!';
GO
