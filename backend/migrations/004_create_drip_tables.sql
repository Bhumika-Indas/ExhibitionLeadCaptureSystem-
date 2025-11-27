-- =============================================
-- Migration 004: Create Drip System V2 Tables
-- Description: Message Templates, Drip Sequences, Drip Queue
-- Author: Claude
-- Date: 2025-11-24
-- =============================================

USE INDAS_DB;
GO

-- =============================================
-- 1. MESSAGE TEMPLATES (Template Library)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[MessageTemplates]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[MessageTemplates] (
        TemplateId INT IDENTITY(1,1) PRIMARY KEY,
        Title NVARCHAR(255) NOT NULL,
        MessageType NVARCHAR(50) NOT NULL CHECK (MessageType IN ('text', 'image', 'video', 'document', 'audio')),
        MessageBody NVARCHAR(MAX) NOT NULL,
        MediaFilePath NVARCHAR(500) NULL,
        Variables NVARCHAR(MAX) NULL, -- JSON array of variable names
        Category NVARCHAR(100) NULL, -- thank_you, value_prop, product, case_study, offer, followup, general
        CreatedBy INT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),
        IsActive BIT DEFAULT 1,

        CONSTRAINT FK_MessageTemplates_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Employees(EmployeeId)
    );

    CREATE INDEX IX_MessageTemplates_Category ON MessageTemplates(Category);
    CREATE INDEX IX_MessageTemplates_MessageType ON MessageTemplates(MessageType);
    PRINT 'Table MessageTemplates created successfully';
END
GO

-- =============================================
-- 2. DRIP MASTER (Drip Sequence Definitions)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DripMaster]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[DripMaster] (
        DripId INT IDENTITY(1,1) PRIMARY KEY,
        DripName NVARCHAR(255) NOT NULL,
        Description NVARCHAR(1000) NULL,
        Icon NVARCHAR(10) NULL, -- Emoji icon
        Status NVARCHAR(50) DEFAULT 'active' CHECK (Status IN ('active', 'inactive', 'archived')),
        CreatedBy INT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),
        UpdatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_DripMaster_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Employees(EmployeeId)
    );

    CREATE INDEX IX_DripMaster_Status ON DripMaster(Status);
    PRINT 'Table DripMaster created successfully';
END
GO

-- =============================================
-- 3. DRIP MESSAGES (Drip Sequence Steps)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DripMessages]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[DripMessages] (
        DripMessageId INT IDENTITY(1,1) PRIMARY KEY,
        DripId INT NOT NULL,
        TemplateId INT NOT NULL,
        DayOffset INT NOT NULL CHECK (DayOffset >= 0), -- 0 = same day, 1 = next day, etc.
        TimeOfDay TIME NOT NULL, -- e.g., '10:00:00', '17:30:00'
        OrderNo INT NOT NULL DEFAULT 0, -- Position within same day
        IsActive BIT DEFAULT 1,
        CreatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_DripMessages_DripId FOREIGN KEY (DripId) REFERENCES DripMaster(DripId) ON DELETE CASCADE,
        CONSTRAINT FK_DripMessages_TemplateId FOREIGN KEY (TemplateId) REFERENCES MessageTemplates(TemplateId)
    );

    CREATE INDEX IX_DripMessages_DripId ON DripMessages(DripId);
    CREATE INDEX IX_DripMessages_DayOffset ON DripMessages(DayOffset);
    PRINT 'Table DripMessages created successfully';
END
GO

-- =============================================
-- 4. LEAD DRIP ASSIGNMENTS (Drip Applied to Leads)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[LeadDripAssignments]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[LeadDripAssignments] (
        AssignmentId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId INT NOT NULL,
        DripId INT NOT NULL,
        StartDate DATETIME NOT NULL DEFAULT GETDATE(),
        Status NVARCHAR(50) DEFAULT 'active' CHECK (Status IN ('active', 'paused', 'completed', 'cancelled')),
        CompletedAt DATETIME NULL,
        CancelledAt DATETIME NULL,
        CancelledBy INT NULL,
        CancellationReason NVARCHAR(500) NULL,
        CreatedBy INT NULL,
        CreatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_LeadDripAssignments_LeadId FOREIGN KEY (LeadId) REFERENCES Leads(LeadId) ON DELETE CASCADE,
        CONSTRAINT FK_LeadDripAssignments_DripId FOREIGN KEY (DripId) REFERENCES DripMaster(DripId),
        CONSTRAINT FK_LeadDripAssignments_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Employees(EmployeeId),
        CONSTRAINT FK_LeadDripAssignments_CancelledBy FOREIGN KEY (CancelledBy) REFERENCES Employees(EmployeeId)
    );

    CREATE INDEX IX_LeadDripAssignments_LeadId ON LeadDripAssignments(LeadId);
    CREATE INDEX IX_LeadDripAssignments_Status ON LeadDripAssignments(Status);
    CREATE INDEX IX_LeadDripAssignments_StartDate ON LeadDripAssignments(StartDate);
    PRINT 'Table LeadDripAssignments created successfully';
END
GO

-- =============================================
-- 5. DRIP QUEUE (Scheduled Messages)
-- =============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DripQueue]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[DripQueue] (
        QueueId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId INT NOT NULL,
        AssignmentId INT NOT NULL,
        DripId INT NOT NULL,
        DripMessageId INT NOT NULL,
        TemplateId INT NOT NULL,
        ScheduledAt DATETIME NOT NULL,
        Status NVARCHAR(50) DEFAULT 'pending' CHECK (Status IN ('pending', 'sent', 'failed', 'cancelled')),
        SentAt DATETIME NULL,
        FailureReason NVARCHAR(1000) NULL,
        Attempts INT DEFAULT 0,
        WhatsAppMessageId NVARCHAR(255) NULL, -- External message ID from WhatsApp API
        CreatedAt DATETIME DEFAULT GETDATE(),

        CONSTRAINT FK_DripQueue_LeadId FOREIGN KEY (LeadId) REFERENCES Leads(LeadId) ON DELETE CASCADE,
        CONSTRAINT FK_DripQueue_AssignmentId FOREIGN KEY (AssignmentId) REFERENCES LeadDripAssignments(AssignmentId) ON DELETE CASCADE,
        CONSTRAINT FK_DripQueue_DripId FOREIGN KEY (DripId) REFERENCES DripMaster(DripId),
        CONSTRAINT FK_DripQueue_DripMessageId FOREIGN KEY (DripMessageId) REFERENCES DripMessages(DripMessageId),
        CONSTRAINT FK_DripQueue_TemplateId FOREIGN KEY (TemplateId) REFERENCES MessageTemplates(TemplateId)
    );

    CREATE INDEX IX_DripQueue_LeadId ON DripQueue(LeadId);
    CREATE INDEX IX_DripQueue_Status ON DripQueue(Status);
    CREATE INDEX IX_DripQueue_ScheduledAt ON DripQueue(ScheduledAt);
    CREATE INDEX IX_DripQueue_AssignmentId ON DripQueue(AssignmentId);
    PRINT 'Table DripQueue created successfully';
END
GO

-- =============================================
-- 6. INSERT SAMPLE MESSAGE TEMPLATES
-- =============================================
IF NOT EXISTS (SELECT 1 FROM MessageTemplates)
BEGIN
    SET IDENTITY_INSERT MessageTemplates ON;

    INSERT INTO MessageTemplates (TemplateId, Title, MessageType, MessageBody, Category, IsActive)
    VALUES
        (1, 'Welcome Message', 'text', 'Welcome to Indas Analytics! Thank you for visiting our booth at {{exhibition_name}}.', 'thank_you', 1),
        (2, 'Company Profile', 'document', 'Here is our company profile with detailed information about our solutions.', 'product', 1),
        (3, 'Demo Request', 'text', 'Hi {{name}}! Would you be interested in scheduling a product demo? We can show you how our solutions can help {{company}}.', 'followup', 1),
        (4, 'Pricing Overview', 'image', 'Here is our pricing overview. Special exhibition discount available!', 'offer', 1),
        (5, 'Final Follow-up', 'text', 'Just following up on our previous messages. Any questions we can help with?', 'followup', 1),
        (6, 'Thank You Booth Visit', 'text', 'Thank you for visiting our booth! We appreciate your interest.', 'thank_you', 1),
        (7, 'Intro Video', 'video', 'Watch this 2-minute video about our solutions.', 'product', 1),
        (8, 'Follow-up Reminder', 'text', 'Just a quick reminder about our special exhibition offer! Valid until {{offer_expiry}}.', 'offer', 1),
        (9, 'Pricing Sheet', 'image', 'Our pricing sheet with special exhibition discounts.', 'offer', 1),
        (10, 'Case Study', 'text', 'Here is a case study from one of our clients in your industry - {{company_industry}}.', 'case_study', 1),
        (11, 'Urgency Message', 'text', 'Special offer expires in 2 days! Let us know if you would like to proceed.', 'offer', 1),
        (12, 'Final Touchpoint', 'text', 'Thank you for considering Indas Analytics. Feel free to reach out anytime!', 'followup', 1),
        (13, 'Demo Invitation', 'text', 'Great to meet you {{name}}! When would be a good time for a personalized demo?', 'followup', 1),
        (14, 'Demo Follow-up', 'text', 'Hi {{name}}, just checking if you had a chance to review our proposal?', 'followup', 1),
        (15, 'Demo Highlights', 'document', 'Here are the key highlights from our demo presentation.', 'product', 1),
        (16, 'Final Check-in', 'text', 'Let me know if you need any assistance with {{product_name}}!', 'followup', 1);

    SET IDENTITY_INSERT MessageTemplates OFF;
    PRINT 'Sample Message Templates inserted successfully';
END
GO

-- =============================================
-- 7. INSERT SAMPLE DRIP SEQUENCES
-- =============================================
IF NOT EXISTS (SELECT 1 FROM DripMaster)
BEGIN
    SET IDENTITY_INSERT DripMaster ON;

    INSERT INTO DripMaster (DripId, DripName, Description, Icon, Status)
    VALUES
        (1, 'Hot Lead Drip', 'Follow-up sequence for hot leads', '🔥', 'active'),
        (2, 'Exhibition Follow-Up Drip', 'Standard exhibition visitor nurture sequence', '📄', 'active'),
        (3, 'Demo Conversion Drip', 'Focused on demo scheduling', '🤝', 'active');

    SET IDENTITY_INSERT DripMaster OFF;
    PRINT 'Sample Drip Masters inserted successfully';
END
GO

-- =============================================
-- 8. INSERT SAMPLE DRIP MESSAGES
-- =============================================
IF NOT EXISTS (SELECT 1 FROM DripMessages)
BEGIN
    -- Hot Lead Drip (DripId = 1)
    INSERT INTO DripMessages (DripId, TemplateId, DayOffset, TimeOfDay, OrderNo)
    VALUES
        (1, 1, 0, '10:00:00', 1),  -- Welcome Message
        (1, 2, 1, '11:00:00', 1),  -- Company Profile
        (1, 3, 2, '17:00:00', 1),  -- Demo Request
        (1, 4, 3, '16:00:00', 1),  -- Pricing Overview
        (1, 5, 5, '14:00:00', 1);  -- Final Follow-up

    -- Exhibition Follow-Up Drip (DripId = 2)
    INSERT INTO DripMessages (DripId, TemplateId, DayOffset, TimeOfDay, OrderNo)
    VALUES
        (2, 6, 0, '10:00:00', 1),  -- Thank You Message
        (2, 7, 0, '10:05:00', 2),  -- Intro Video
        (2, 8, 1, '11:00:00', 1),  -- Follow-up Reminder
        (2, 9, 3, '10:00:00', 1),  -- Pricing Sheet
        (2, 10, 4, '15:00:00', 1), -- Case Study
        (2, 11, 5, '11:00:00', 1), -- Urgency Message
        (2, 12, 5, '17:00:00', 2); -- Final Touchpoint

    -- Demo Conversion Drip (DripId = 3)
    INSERT INTO DripMessages (DripId, TemplateId, DayOffset, TimeOfDay, OrderNo)
    VALUES
        (3, 13, 0, '09:00:00', 1), -- Demo Invitation
        (3, 14, 1, '14:00:00', 1), -- Demo Follow-up
        (3, 15, 2, '11:00:00', 1), -- Demo Highlights
        (3, 16, 3, '16:00:00', 1); -- Final Check-in

    PRINT 'Sample Drip Messages inserted successfully';
END
GO

PRINT '==============================================';
PRINT 'Migration 004 completed successfully!';
PRINT 'Drip System V2 tables created and populated';
PRINT '==============================================';
GO
