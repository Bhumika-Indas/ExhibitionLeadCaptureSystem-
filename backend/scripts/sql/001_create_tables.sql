-- INDAS Exhibition Lead Capture System (ELCS)
-- Database Schema Creation Script
-- Version: 1.0
-- Database: MSSQL Server

USE master;
GO

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ExhibitionLeads')
BEGIN
    CREATE DATABASE ExhibitionLeads;
    PRINT 'Database ExhibitionLeads created successfully.';
END
ELSE
BEGIN
    PRINT 'Database ExhibitionLeads already exists.';
END
GO

USE ExhibitionLeads;
GO

-- ============================================================
-- 1. LOOKUP TABLES
-- ============================================================

-- Lead Sources (employee_scan vs qr_whatsapp)
CREATE TABLE LeadSources (
    SourceCode VARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(255) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Lead Statuses
CREATE TABLE LeadStatuses (
    StatusCode VARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(255) NULL,
    DisplayOrder INT NOT NULL DEFAULT 0,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- Next Step Actions
CREATE TABLE NextStepActions (
    ActionCode VARCHAR(50) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL,
    Description NVARCHAR(255) NULL,
    DefaultDueDays INT NOT NULL DEFAULT 3,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

-- ============================================================
-- 2. CORE ENTITIES
-- ============================================================

-- Exhibitions
CREATE TABLE Exhibitions (
    ExhibitionId INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(200) NOT NULL,
    Location NVARCHAR(300) NULL,
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    Description NVARCHAR(MAX) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT CK_Exhibition_Dates CHECK (EndDate >= StartDate)
);

-- Employees
CREATE TABLE Employees (
    EmployeeId INT IDENTITY(1,1) PRIMARY KEY,
    FullName NVARCHAR(150) NOT NULL,
    Phone NVARCHAR(20) NOT NULL,
    Email NVARCHAR(150) NOT NULL,
    LoginName VARCHAR(100) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE INDEX IX_Employees_LoginName ON Employees(LoginName);
CREATE INDEX IX_Employees_Phone ON Employees(Phone);

-- ============================================================
-- 3. LEADS
-- ============================================================

-- Main Leads Table
CREATE TABLE Leads (
    LeadId BIGINT IDENTITY(1,1) PRIMARY KEY,
    ExhibitionId INT NOT NULL,
    SourceCode VARCHAR(50) NOT NULL,
    AssignedEmployeeId INT NULL,

    -- Company Information
    CompanyName NVARCHAR(200) NULL,

    -- Primary Visitor Information
    PrimaryVisitorName NVARCHAR(150) NULL,
    PrimaryVisitorDesignation NVARCHAR(100) NULL,
    PrimaryVisitorPhone NVARCHAR(20) NULL,
    PrimaryVisitorEmail NVARCHAR(150) NULL,

    -- Discussion & Next Steps
    DiscussionSummary NVARCHAR(MAX) NULL,
    NextStep VARCHAR(50) NULL,

    -- Status & Confirmation
    StatusCode VARCHAR(50) NOT NULL DEFAULT 'new',
    WhatsAppConfirmed BIT NULL,
    ConfirmedAt DATETIME2 NULL,

    -- Raw Data Storage (for AI re-processing)
    RawCardJson NVARCHAR(MAX) NULL,
    RawVoiceTranscript NVARCHAR(MAX) NULL,

    -- Metadata
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),

    -- Foreign Keys
    CONSTRAINT FK_Leads_Exhibitions FOREIGN KEY (ExhibitionId)
        REFERENCES Exhibitions(ExhibitionId),
    CONSTRAINT FK_Leads_Sources FOREIGN KEY (SourceCode)
        REFERENCES LeadSources(SourceCode),
    CONSTRAINT FK_Leads_Employees FOREIGN KEY (AssignedEmployeeId)
        REFERENCES Employees(EmployeeId),
    CONSTRAINT FK_Leads_Statuses FOREIGN KEY (StatusCode)
        REFERENCES LeadStatuses(StatusCode),
    CONSTRAINT FK_Leads_NextSteps FOREIGN KEY (NextStep)
        REFERENCES NextStepActions(ActionCode)
);

CREATE INDEX IX_Leads_Exhibition ON Leads(ExhibitionId);
CREATE INDEX IX_Leads_Source ON Leads(SourceCode);
CREATE INDEX IX_Leads_Status ON Leads(StatusCode);
CREATE INDEX IX_Leads_Employee ON Leads(AssignedEmployeeId);
CREATE INDEX IX_Leads_Phone ON Leads(PrimaryVisitorPhone);
CREATE INDEX IX_Leads_CreatedAt ON Leads(CreatedAt DESC);

-- ============================================================
-- 4. LEAD RELATED ENTITIES
-- ============================================================

-- Multiple Persons on Card
CREATE TABLE LeadPersons (
    LeadPersonId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    Name NVARCHAR(150) NOT NULL,
    Designation NVARCHAR(100) NULL,
    Phone NVARCHAR(20) NULL,
    Email NVARCHAR(150) NULL,
    IsPrimary BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadPersons_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadPersons_LeadId ON LeadPersons(LeadId);

-- Multiple Addresses
CREATE TABLE LeadAddresses (
    LeadAddressId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    AddressType VARCHAR(50) NULL, -- Factory, Corporate, Branch, etc.
    AddressText NVARCHAR(500) NOT NULL,
    City NVARCHAR(100) NULL,
    State NVARCHAR(100) NULL,
    Country NVARCHAR(100) NULL,
    PinCode VARCHAR(20) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadAddresses_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadAddresses_LeadId ON LeadAddresses(LeadId);

-- Company Websites
CREATE TABLE LeadWebsites (
    LeadWebsiteId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    WebsiteUrl NVARCHAR(300) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadWebsites_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadWebsites_LeadId ON LeadWebsites(LeadId);

-- Services/Products
CREATE TABLE LeadServices (
    LeadServiceId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    ServiceText NVARCHAR(200) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadServices_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadServices_LeadId ON LeadServices(LeadId);

-- Topics Discussed
CREATE TABLE LeadTopics (
    LeadTopicId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    TopicText NVARCHAR(200) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadTopics_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadTopics_LeadId ON LeadTopics(LeadId);

-- ============================================================
-- 5. ATTACHMENTS (FILE PATHS ONLY)
-- ============================================================

CREATE TABLE LeadAttachments (
    AttachmentId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    AttachmentType VARCHAR(50) NOT NULL, -- card_front, card_back, audio_note, document
    FileUrl NVARCHAR(500) NOT NULL,
    FileSizeBytes BIGINT NULL,
    MimeType VARCHAR(100) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadAttachments_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE
);

CREATE INDEX IX_LeadAttachments_LeadId ON LeadAttachments(LeadId);
CREATE INDEX IX_LeadAttachments_Type ON LeadAttachments(AttachmentType);

-- ============================================================
-- 6. MESSAGES & CHAT
-- ============================================================

-- Lead Messages (Chat conversation)
CREATE TABLE LeadMessages (
    MessageId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    SenderType VARCHAR(50) NOT NULL, -- employee, visitor, system
    SenderEmployeeId INT NULL,
    MessageText NVARCHAR(MAX) NOT NULL,
    WhatsAppMessageId VARCHAR(100) NULL, -- Link to WhatsApp message
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_LeadMessages_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE,
    CONSTRAINT FK_LeadMessages_Employees FOREIGN KEY (SenderEmployeeId)
        REFERENCES Employees(EmployeeId)
);

CREATE INDEX IX_LeadMessages_LeadId ON LeadMessages(LeadId);
CREATE INDEX IX_LeadMessages_CreatedAt ON LeadMessages(CreatedAt DESC);

-- ============================================================
-- 7. WHATSAPP INTEGRATION
-- ============================================================

CREATE TABLE WhatsAppMessages (
    WaMessageId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NULL,
    Direction VARCHAR(20) NOT NULL, -- inbound, outbound
    FromNumber NVARCHAR(20) NOT NULL,
    ToNumber NVARCHAR(20) NOT NULL,
    MessageType VARCHAR(50) NOT NULL, -- text, image, audio, template
    Body NVARCHAR(MAX) NULL,
    MediaUrl NVARCHAR(500) NULL,
    TemplateId VARCHAR(100) NULL,
    WaMessageIdExternal VARCHAR(200) NULL, -- WhatsApp's message ID
    RawPayloadJson NVARCHAR(MAX) NULL,
    Status VARCHAR(50) NULL, -- sent, delivered, read, failed
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_WhatsAppMessages_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId)
);

CREATE INDEX IX_WhatsAppMessages_LeadId ON WhatsAppMessages(LeadId);
CREATE INDEX IX_WhatsAppMessages_FromNumber ON WhatsAppMessages(FromNumber);
CREATE INDEX IX_WhatsAppMessages_CreatedAt ON WhatsAppMessages(CreatedAt DESC);
CREATE INDEX IX_WhatsAppMessages_External ON WhatsAppMessages(WaMessageIdExternal);

-- ============================================================
-- 8. FOLLOW-UPS
-- ============================================================

CREATE TABLE FollowUps (
    FollowUpId BIGINT IDENTITY(1,1) PRIMARY KEY,
    LeadId BIGINT NOT NULL,
    EmployeeId INT NOT NULL,
    NextAction VARCHAR(50) NOT NULL, -- demo, pricing, callback, integration
    ActionNotes NVARCHAR(MAX) NULL,
    DueAt DATETIME2 NOT NULL,
    CompletedAt DATETIME2 NULL,
    IsCompleted BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_FollowUps_Leads FOREIGN KEY (LeadId)
        REFERENCES Leads(LeadId) ON DELETE CASCADE,
    CONSTRAINT FK_FollowUps_Employees FOREIGN KEY (EmployeeId)
        REFERENCES Employees(EmployeeId)
);

CREATE INDEX IX_FollowUps_LeadId ON FollowUps(LeadId);
CREATE INDEX IX_FollowUps_Employee ON FollowUps(EmployeeId);
CREATE INDEX IX_FollowUps_DueAt ON FollowUps(DueAt);
CREATE INDEX IX_FollowUps_Completed ON FollowUps(IsCompleted, DueAt);

PRINT 'All tables created successfully.';
GO
