-- =====================================================
-- Drip System V2 - Complete Message & Drip Management
-- =====================================================

-- 1. MESSAGE MASTER - Reusable message templates
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'MessageMaster') AND type = 'U')
BEGIN
    CREATE TABLE MessageMaster (
        MessageId INT IDENTITY(1,1) PRIMARY KEY,
        MessageTitle NVARCHAR(200) NOT NULL,
        MessageType NVARCHAR(20) NOT NULL CHECK (MessageType IN ('text', 'image', 'document', 'video')),
        MessageBody NVARCHAR(MAX) NULL,          -- For text messages
        FileUrl NVARCHAR(500) NULL,              -- For media messages
        FileName NVARCHAR(200) NULL,             -- Original filename
        FileMimeType NVARCHAR(100) NULL,         -- MIME type
        Variables NVARCHAR(MAX) NULL,            -- JSON array of placeholder variables like ["name", "company"]
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    PRINT 'Created MessageMaster table';
END
GO

-- 2. DRIP MASTER - Drip sequence definitions
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DripMaster') AND type = 'U')
BEGIN
    CREATE TABLE DripMaster (
        DripId INT IDENTITY(1,1) PRIMARY KEY,
        DripName NVARCHAR(200) NOT NULL,
        DripDescription NVARCHAR(500) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    PRINT 'Created DripMaster table';
END
GO

-- 3. DRIP MESSAGES - Messages within a drip with Day + Time
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'DripMessages') AND type = 'U')
BEGIN
    CREATE TABLE DripMessages (
        DripMessageId INT IDENTITY(1,1) PRIMARY KEY,
        DripId INT NOT NULL FOREIGN KEY REFERENCES DripMaster(DripId) ON DELETE CASCADE,
        MessageId INT NOT NULL FOREIGN KEY REFERENCES MessageMaster(MessageId),
        DayNumber INT NOT NULL DEFAULT 0,        -- 0 = immediate, 1 = next day, etc.
        SendTime TIME NOT NULL DEFAULT '10:00',  -- Time to send (HH:mm)
        SortOrder INT NOT NULL DEFAULT 0,        -- Order within same day
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    PRINT 'Created DripMessages table';

    -- Index for efficient queries
    CREATE INDEX IX_DripMessages_DripId ON DripMessages(DripId);
    CREATE INDEX IX_DripMessages_DayNumber ON DripMessages(DayNumber);
END
GO

-- 4. LEAD DRIP ASSIGNMENTS - Track which drip is applied to which lead
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'LeadDripAssignments') AND type = 'U')
BEGIN
    CREATE TABLE LeadDripAssignments (
        AssignmentId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId BIGINT NOT NULL FOREIGN KEY REFERENCES Leads(LeadId) ON DELETE CASCADE,
        DripId INT NOT NULL FOREIGN KEY REFERENCES DripMaster(DripId),
        Status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (Status IN ('active', 'paused', 'stopped', 'completed')),
        StartedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        PausedAt DATETIME2 NULL,
        StoppedAt DATETIME2 NULL,
        CompletedAt DATETIME2 NULL,
        CurrentDayNumber INT NOT NULL DEFAULT 0,  -- Track progress
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    PRINT 'Created LeadDripAssignments table';

    -- Indexes
    CREATE INDEX IX_LeadDripAssignments_LeadId ON LeadDripAssignments(LeadId);
    CREATE INDEX IX_LeadDripAssignments_Status ON LeadDripAssignments(Status);
END
GO

-- 5. SCHEDULED DRIP MESSAGES - Individual scheduled messages for each lead
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'ScheduledDripMessages') AND type = 'U')
BEGIN
    CREATE TABLE ScheduledDripMessages (
        ScheduledId INT IDENTITY(1,1) PRIMARY KEY,
        AssignmentId INT NOT NULL FOREIGN KEY REFERENCES LeadDripAssignments(AssignmentId) ON DELETE CASCADE,
        LeadId BIGINT NOT NULL FOREIGN KEY REFERENCES Leads(LeadId),
        DripMessageId INT NOT NULL FOREIGN KEY REFERENCES DripMessages(DripMessageId),
        MessageId INT NOT NULL FOREIGN KEY REFERENCES MessageMaster(MessageId),
        ScheduledAt DATETIME2 NOT NULL,          -- Exact datetime to send
        Status NVARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (Status IN ('pending', 'sent', 'failed', 'skipped', 'cancelled')),
        SentAt DATETIME2 NULL,
        ErrorMessage NVARCHAR(500) NULL,
        WhatsAppMessageId NVARCHAR(100) NULL,    -- External message ID if sent
        CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );
    PRINT 'Created ScheduledDripMessages table';

    -- Indexes for scheduler queries
    CREATE INDEX IX_ScheduledDripMessages_Status ON ScheduledDripMessages(Status);
    CREATE INDEX IX_ScheduledDripMessages_ScheduledAt ON ScheduledDripMessages(ScheduledAt);
    CREATE INDEX IX_ScheduledDripMessages_LeadId ON ScheduledDripMessages(LeadId);
END
GO

-- 6. Seed some sample message templates
IF NOT EXISTS (SELECT 1 FROM MessageMaster WHERE MessageTitle = 'Welcome Message')
BEGIN
    INSERT INTO MessageMaster (MessageTitle, MessageType, MessageBody, Variables)
    VALUES
    ('Welcome Message', 'text', 'Hello {{name}}! Thank you for connecting with us at the exhibition. We look forward to working with {{company}}.', '["name", "company"]'),
    ('Day 1 Follow-up', 'text', 'Hi {{name}}, hope you had a great time at the exhibition! We wanted to share more about how we can help {{company}}.', '["name", "company"]'),
    ('Product Brochure', 'text', 'Hi {{name}}, here is our product brochure for your reference. Feel free to reach out with any questions!', '["name"]'),
    ('Special Offer', 'text', 'Exclusive for {{company}}! As a valued exhibition contact, we are offering special pricing. Reply to know more.', '["company"]'),
    ('Final Follow-up', 'text', 'Hi {{name}}, this is our last follow-up. If you are interested in our solutions for {{company}}, please reply or call us.', '["name", "company"]');

    PRINT 'Inserted sample message templates';
END
GO

-- 7. Seed a sample drip
IF NOT EXISTS (SELECT 1 FROM DripMaster WHERE DripName = 'Exhibition Follow-up Drip')
BEGIN
    -- Create drip
    INSERT INTO DripMaster (DripName, DripDescription)
    VALUES ('Exhibition Follow-up Drip', 'Standard 5-day follow-up sequence for exhibition leads');

    DECLARE @DripId INT = SCOPE_IDENTITY();

    -- Add messages to drip
    INSERT INTO DripMessages (DripId, MessageId, DayNumber, SendTime, SortOrder)
    SELECT @DripId, MessageId,
        CASE MessageTitle
            WHEN 'Welcome Message' THEN 0
            WHEN 'Day 1 Follow-up' THEN 1
            WHEN 'Product Brochure' THEN 2
            WHEN 'Special Offer' THEN 4
            WHEN 'Final Follow-up' THEN 7
        END,
        '10:00',
        ROW_NUMBER() OVER (ORDER BY MessageId)
    FROM MessageMaster
    WHERE MessageTitle IN ('Welcome Message', 'Day 1 Follow-up', 'Product Brochure', 'Special Offer', 'Final Follow-up');

    PRINT 'Created sample drip with messages';
END
GO

PRINT '✅ Drip System V2 migration complete!';
