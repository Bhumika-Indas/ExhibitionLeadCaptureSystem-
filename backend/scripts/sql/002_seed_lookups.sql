-- INDAS Exhibition Lead Capture System (ELCS)
-- Seed Data for Lookup Tables
-- Version: 1.0

USE ExhibitionLeads;
GO

-- ============================================================
-- 1. LEAD SOURCES
-- ============================================================

INSERT INTO LeadSources (SourceCode, Name, Description, IsActive)
VALUES
    ('employee_scan', 'Employee Scan', 'Lead captured by employee using app', 1),
    ('qr_whatsapp', 'QR WhatsApp', 'Lead self-submitted via QR code and WhatsApp', 1),
    ('manual_entry', 'Manual Entry', 'Manually entered lead (fallback)', 1);

PRINT 'Lead Sources seeded successfully.';

-- ============================================================
-- 2. LEAD STATUSES
-- ============================================================

INSERT INTO LeadStatuses (StatusCode, Name, Description, DisplayOrder, IsActive)
VALUES
    ('new', 'New', 'Newly captured lead, awaiting WhatsApp confirmation', 1, 1),
    ('confirmed', 'Confirmed', 'Visitor confirmed details via WhatsApp', 2, 1),
    ('needs_correction', 'Needs Correction', 'Visitor indicated corrections needed', 3, 1),
    ('in_progress', 'In Progress', 'Follow-up in progress', 4, 1),
    ('contacted', 'Contacted', 'Initial contact made', 5, 1),
    ('qualified', 'Qualified', 'Lead qualified as potential customer', 6, 1),
    ('demo_scheduled', 'Demo Scheduled', 'Product demo scheduled', 7, 1),
    ('proposal_sent', 'Proposal Sent', 'Pricing proposal sent', 8, 1),
    ('won', 'Won', 'Lead converted to customer', 9, 1),
    ('lost', 'Lost', 'Lead lost or not interested', 10, 1),
    ('on_hold', 'On Hold', 'Lead on hold temporarily', 11, 1),
    ('closed', 'Closed', 'Lead closed (generic)', 12, 1);

PRINT 'Lead Statuses seeded successfully.';

-- ============================================================
-- 3. NEXT STEP ACTIONS
-- ============================================================

INSERT INTO NextStepActions (ActionCode, Name, Description, DefaultDueDays, IsActive)
VALUES
    ('demo', 'Schedule Demo', 'Schedule product demonstration', 3, 1),
    ('pricing', 'Send Pricing', 'Send pricing and quotation', 2, 1),
    ('integration', 'Discuss Integration', 'Discuss technical integration details', 5, 1),
    ('callback', 'Call Back', 'Follow-up call required', 1, 1),
    ('meeting', 'Schedule Meeting', 'Schedule in-person or virtual meeting', 7, 1),
    ('proposal', 'Send Proposal', 'Send detailed proposal', 3, 1),
    ('trial', 'Setup Trial', 'Setup trial/POC environment', 7, 1),
    ('followup', 'General Follow-up', 'General follow-up contact', 3, 1);

PRINT 'Next Step Actions seeded successfully.';

-- ============================================================
-- 4. SAMPLE EXHIBITION (Optional - for testing)
-- ============================================================

-- Current exhibition for testing
INSERT INTO Exhibitions (Name, Location, StartDate, EndDate, Description, IsActive)
VALUES
    ('PrintPack India 2025', 'India Expo Centre, Greater Noida', '2025-02-01', '2025-02-06', 'Leading printing and packaging exhibition', 1),
    ('PackPlus 2025', 'Pragati Maidan, New Delhi', '2025-03-15', '2025-03-18', 'Packaging and processing expo', 1);

PRINT 'Sample Exhibitions seeded successfully.';

-- ============================================================
-- 5. TEST EMPLOYEE (Optional - for development)
-- ============================================================

-- Default password: 'Admin@123' (hashed using bcrypt)
-- Note: In production, use proper password hashing via Python backend
INSERT INTO Employees (FullName, Phone, Email, LoginName, PasswordHash, IsActive)
VALUES
    ('Test Employee', '+917000090823', 'test@indas.app', 'test.employee',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lWjVhZd0bXua', -- Admin@123
     1),
    ('Bhumika ', '+919691139890', 'bhumika@indas.app', 'bhumika.singh',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lWjVhZd0bXua', -- Admin@123
     1);

PRINT 'Test Employees seeded successfully.';

-- ============================================================
-- COMPLETE
-- ============================================================

PRINT '';
PRINT '========================================';
PRINT 'Database seeding completed successfully!';
PRINT '========================================';
PRINT '';
PRINT 'Default Login Credentials (for testing):';
PRINT '  Username: test.employee';
PRINT '  Password: Admin@123';
PRINT '';
PRINT '  Username: bhumika';
PRINT '  Password: Admin@123';
PRINT '';
PRINT 'IMPORTANT: Change passwords in production!';
PRINT '';
GO
