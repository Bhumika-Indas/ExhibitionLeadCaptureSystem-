-- INDAS Exhibition Lead Capture System (ELCS)
-- Migration: Add Drip Sequence Support
-- Version: 1.1
-- Description: Updates FollowUps table to support automated drip sequences

USE ExhibitionLeads;
GO

-- ============================================================
-- 1. DROP EXISTING FOLLOWUPS TABLE (if it exists)
-- ============================================================

IF OBJECT_ID('dbo.FollowUps', 'U') IS NOT NULL
BEGIN
    PRINT 'Dropping existing FollowUps table...';

    -- Drop foreign keys first
    IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_FollowUps_Leads')
        ALTER TABLE FollowUps DROP CONSTRAINT FK_FollowUps_Leads;

    IF EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_FollowUps_Employees')
        ALTER TABLE FollowUps DROP CONSTRAINT FK_FollowUps_Employees;

    -- Drop indexes
    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FollowUps_LeadId')
        DROP INDEX IX_FollowUps_LeadId ON FollowUps;

    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FollowUps_Employee')
        DROP INDEX IX_FollowUps_Employee ON FollowUps;

    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FollowUps_DueAt')
        DROP INDEX IX_FollowUps_DueAt ON FollowUps;

    IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_FollowUps_Completed')
        DROP INDEX IX_FollowUps_Completed ON FollowUps;

    -- Drop table
    DROP TABLE FollowUps;
    PRINT 'Existing FollowUps table dropped.';
END
ELSE
BEGIN
    PRINT 'FollowUps table does not exist. Creating new...';
END
GO

-- ============================================================
-- 2. CREATE NEW FOLLOWUPS TABLE WITH DRIP SEQUENCE SUPPORT
-- ============================================================

CREATE TABLE FollowUps (
    FollowUpId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,

    -- Action Type: drip_1 (24h), drip_2 (72h), drip_3 (120h), manual, callback, demo, etc.
    ActionType VARCHAR(50) NOT NULL,

    -- Scheduling
    ScheduledAt DATETIME2 NOT NULL,
    CompletedAt DATETIME2 NULL,

    -- Status: pending, completed, cancelled, failed
    Status VARCHAR(50) NOT NULL DEFAULT 'pending',

    -- Optional notes
    Notes NVARCHAR(MAX) NULL,

    -- Employee who created/handled this follow-up (optional for automated drips)
    CreatedByEmployeeId INT NULL,
    CompletedByEmployeeId INT NULL,

    -- Metadata
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NULL,

    -- Foreign Keys
    CONSTRAINT FK_FollowUps_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE,
    CONSTRAINT FK_FollowUps_CreatedBy FOREIGN KEY (CreatedByEmployeeId)
        REFERENCES Employees(EmployeeId),
    CONSTRAINT FK_FollowUps_CompletedBy FOREIGN KEY (CompletedByEmployeeId)
        REFERENCES Employees(EmployeeId)
);
GO

-- ============================================================
-- 3. CREATE INDEXES FOR PERFORMANCE
-- ============================================================

CREATE INDEX IX_FollowUps_LeadId ON FollowUps(LeadId);
CREATE INDEX IX_FollowUps_ActionType ON FollowUps(ActionType);
CREATE INDEX IX_FollowUps_ScheduledAt ON FollowUps(ScheduledAt);
CREATE INDEX IX_FollowUps_Status ON FollowUps(Status);
CREATE INDEX IX_FollowUps_Status_Scheduled ON FollowUps(Status, ScheduledAt) WHERE Status = 'pending';
CREATE INDEX IX_FollowUps_CreatedAt ON FollowUps(CreatedAt DESC);
GO

PRINT 'FollowUps table created successfully with drip sequence support.';
GO

-- ============================================================
-- 4. CREATE DRIP ACTION TYPES LOOKUP (OPTIONAL)
-- ============================================================

IF OBJECT_ID('dbo.DripActionTypes', 'U') IS NULL
BEGIN
    CREATE TABLE DripActionTypes (
        ActionType VARCHAR(50) PRIMARY KEY,
        Name NVARCHAR(100) NOT NULL,
        Description NVARCHAR(255) NULL,
        DefaultDelayHours INT NOT NULL,
        IsAutomated BIT NOT NULL DEFAULT 0,
        MessageTemplate NVARCHAR(MAX) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

    -- Insert drip sequence types
    INSERT INTO DripActionTypes (ActionType, Name, Description, DefaultDelayHours, IsAutomated, MessageTemplate, IsActive)
    VALUES
        ('drip_1', 'First Follow-up (24h)', 'Automated follow-up 24 hours after lead capture', 24, 1,
         'Hi {name}, thank you for visiting our booth at {exhibition}. We would love to discuss how we can help {company}. Are you available for a quick call?', 1),

        ('drip_2', 'Second Follow-up (72h)', 'Automated follow-up 72 hours (3 days) after lead capture', 72, 1,
         'Hi {name}, following up on our conversation at {exhibition}. I wanted to share more details about our solutions for {company}. Would you like to schedule a demo?', 1),

        ('drip_3', 'Third Follow-up (120h)', 'Automated follow-up 120 hours (5 days) after lead capture', 120, 1,
         'Hi {name}, this is my final follow-up regarding our discussion at {exhibition}. If you''re still interested in learning about our solutions for {company}, please let me know. Happy to help!', 1),

        ('manual', 'Manual Follow-up', 'Manually created follow-up task', 0, 0, NULL, 1),
        ('demo', 'Demo Scheduled', 'Product demonstration scheduled', 0, 0, NULL, 1),
        ('callback', 'Callback Requested', 'Lead requested a callback', 0, 0, NULL, 1),
        ('pricing', 'Send Pricing', 'Send pricing information to lead', 0, 0, NULL, 1),
        ('proposal', 'Send Proposal', 'Send business proposal to lead', 0, 0, NULL, 1);

    PRINT 'DripActionTypes lookup table created and populated.';
END
ELSE
BEGIN
    PRINT 'DripActionTypes table already exists.';
END
GO

-- ============================================================
-- 5. ADD MESSAGE TABLE IF NOT EXISTS (FOR WEBSOCKET CHAT)
-- ============================================================

-- Check if Messages table exists (different from LeadMessages)
IF OBJECT_ID('dbo.Messages', 'U') IS NULL
BEGIN
    CREATE TABLE Messages (
        MessageId BIGINT IDENTITY(1,1) PRIMARY KEY,
        LeadId BIGINT NOT NULL,
        SenderType VARCHAR(50) NOT NULL, -- employee, lead, system
        Message NVARCHAR(MAX) NOT NULL,
        SentAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        ReadAt DATETIME2 NULL,

        CONSTRAINT FK_Messages_Leads FOREIGN KEY (LeadId)
            REFERENCES Leads(LeadId) ON DELETE CASCADE
    );

    CREATE INDEX IX_Messages_LeadId ON Messages(LeadId);
    CREATE INDEX IX_Messages_SentAt ON Messages(SentAt DESC);

    PRINT 'Messages table created for WebSocket chat support.';
END
ELSE
BEGIN
    PRINT 'Messages table already exists.';
END
GO

-- ============================================================
-- 6. VERIFICATION
-- ============================================================

PRINT '';
PRINT '===== MIGRATION SUMMARY =====';
PRINT 'FollowUps table: ' + CASE WHEN OBJECT_ID('dbo.FollowUps', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END;
PRINT 'DripActionTypes table: ' + CASE WHEN OBJECT_ID('dbo.DripActionTypes', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END;
PRINT 'Messages table: ' + CASE WHEN OBJECT_ID('dbo.Messages', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END;
PRINT '';

-- Count existing records
IF OBJECT_ID('dbo.FollowUps', 'U') IS NOT NULL
BEGIN
    DECLARE @followupCount INT;
    SELECT @followupCount = COUNT(*) FROM FollowUps;
    PRINT 'Total FollowUps: ' + CAST(@followupCount AS VARCHAR(10));
END

IF OBJECT_ID('dbo.DripActionTypes', 'U') IS NOT NULL
BEGIN
    DECLARE @actionTypeCount INT;
    SELECT @actionTypeCount = COUNT(*) FROM DripActionTypes;
    PRINT 'Total DripActionTypes: ' + CAST(@actionTypeCount AS VARCHAR(10));
END

IF OBJECT_ID('dbo.Messages', 'U') IS NOT NULL
BEGIN
    DECLARE @messageCount INT;
    SELECT @messageCount = COUNT(*) FROM Messages;
    PRINT 'Total Messages: ' + CAST(@messageCount AS VARCHAR(10));
END

PRINT '';
PRINT '✅ Migration completed successfully!';
GO
