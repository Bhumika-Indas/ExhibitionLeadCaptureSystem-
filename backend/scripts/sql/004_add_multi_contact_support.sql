-- =====================================================
-- Migration: Add Multi-Contact Support
-- Version: 004
-- Description: Adds tables for multiple phones, emails, and brands
-- =====================================================

-- =====================================================
-- TABLE: LeadBrands (for dealer/distributor cards)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'LeadBrands')
BEGIN
    CREATE TABLE LeadBrands (
        LeadBrandId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId INT NOT NULL,
        BrandName NVARCHAR(200) NOT NULL,
        Relationship NVARCHAR(50) NULL,  -- Dealer, Distributor, Authorized, Stockist
        CreatedAt DATETIME2 DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_LeadBrands_Leads FOREIGN KEY (LeadId)
            REFERENCES Leads(LeadId) ON DELETE CASCADE
    );

    CREATE INDEX IX_LeadBrands_LeadId ON LeadBrands(LeadId);
    PRINT 'Created table: LeadBrands';
END
GO

-- =====================================================
-- TABLE: LeadPhones (multiple phone numbers per lead)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'LeadPhones')
BEGIN
    CREATE TABLE LeadPhones (
        LeadPhoneId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId INT NOT NULL,
        PhoneNumber NVARCHAR(20) NOT NULL,
        PhoneType NVARCHAR(20) NULL,  -- Mobile, Landline, WhatsApp, Fax
        IsPrimary BIT DEFAULT 0,
        IsVerified BIT DEFAULT 0,
        CreatedAt DATETIME2 DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_LeadPhones_Leads FOREIGN KEY (LeadId)
            REFERENCES Leads(LeadId) ON DELETE CASCADE
    );

    CREATE INDEX IX_LeadPhones_LeadId ON LeadPhones(LeadId);
    CREATE INDEX IX_LeadPhones_PhoneNumber ON LeadPhones(PhoneNumber);
    PRINT 'Created table: LeadPhones';
END
GO

-- =====================================================
-- TABLE: LeadEmails (multiple emails per lead)
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'LeadEmails')
BEGIN
    CREATE TABLE LeadEmails (
        LeadEmailId INT IDENTITY(1,1) PRIMARY KEY,
        LeadId INT NOT NULL,
        EmailAddress NVARCHAR(200) NOT NULL,
        IsPrimary BIT DEFAULT 0,
        IsVerified BIT DEFAULT 0,
        CreatedAt DATETIME2 DEFAULT SYSUTCDATETIME(),

        CONSTRAINT FK_LeadEmails_Leads FOREIGN KEY (LeadId)
            REFERENCES Leads(LeadId) ON DELETE CASCADE
    );

    CREATE INDEX IX_LeadEmails_LeadId ON LeadEmails(LeadId);
    CREATE INDEX IX_LeadEmails_EmailAddress ON LeadEmails(EmailAddress);
    PRINT 'Created table: LeadEmails';
END
GO

-- =====================================================
-- ADD BusinessType column to Leads table
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Leads') AND name = 'BusinessType')
BEGIN
    ALTER TABLE Leads ADD BusinessType NVARCHAR(50) NULL;
    PRINT 'Added column: Leads.BusinessType';
END
GO

-- =====================================================
-- UPDATE LeadPersons table to support multiple phones/emails per person
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('LeadPersons') AND name = 'Phones')
BEGIN
    -- Add JSON column for multiple phones per person
    ALTER TABLE LeadPersons ADD Phones NVARCHAR(500) NULL;
    PRINT 'Added column: LeadPersons.Phones (JSON array)';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('LeadPersons') AND name = 'Emails')
BEGIN
    -- Add JSON column for multiple emails per person
    ALTER TABLE LeadPersons ADD Emails NVARCHAR(500) NULL;
    PRINT 'Added column: LeadPersons.Emails (JSON array)';
END
GO

PRINT '=== Migration 004 Complete: Multi-Contact Support Added ===';
