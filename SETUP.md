# 🚀 INDAS Exhibition Lead Capture System - Complete Setup Guide

This guide will help you set up the complete ELCS system from scratch, including backend, frontend, database, and external services.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Backend Setup](#backend-setup)
4. [Database Setup](#database-setup)
5. [Frontend Setup](#frontend-setup)
6. [WhatsApp Integration](#whatsapp-integration)
7. [Testing the System](#testing-the-system)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Prerequisites

### Required Software

#### 1. **Python 3.11 or 3.12**
- Download: https://www.python.org/downloads/
- During installation, check "Add Python to PATH"
- Verify installation:
  ```bash
  python --version
  # Should show: Python 3.11.x or 3.12.x
  ```

#### 2. **Node.js 18+ and npm**
- Download: https://nodejs.org/ (LTS version recommended)
- Verify installation:
  ```bash
  node --version  # Should show: v18.x.x or higher
  npm --version   # Should show: 9.x.x or higher
  ```

#### 3. **Microsoft SQL Server 2019+**
- **Option A**: SQL Server Express (Free)
  - Download: https://www.microsoft.com/en-us/sql-server/sql-server-downloads
  - Choose "Express" edition
  - Install with default settings

- **Option B**: Azure SQL Database (Cloud)
  - Sign up: https://azure.microsoft.com/
  - Create SQL Database instance

- **Verify Installation**:
  - Open SQL Server Management Studio (SSMS)
  - Connect to your server
  - Server name format: `localhost\SQLEXPRESS` or `your-server.database.windows.net`

#### 4. **FFmpeg** (for audio processing)
- **Windows**:
  1. Download: https://ffmpeg.org/download.html
  2. Extract to `C:\ffmpeg`
  3. Add to PATH: `C:\ffmpeg\bin`
  4. Verify: `ffmpeg -version`

- **Linux/Mac**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # MacOS
  brew install ffmpeg
  ```

### Required Services & API Keys

#### 1. **OpenAI API Key**
- Sign up: https://platform.openai.com/
- Navigate to API keys section
- Click "Create new secret key"
- Copy and save the key (starts with `sk-`)
- **Cost**: ~$0.50-$2.00 per 100 leads (depending on usage)

#### 2. **WhatsApp Business API**

Choose one option:

**Option A: Meta Cloud API (Recommended)**
- Sign up: https://developers.facebook.com/
- Create app → Select "WhatsApp"
- Get Phone Number ID and Access Token
- **Cost**: Free for first 1,000 conversations/month

**Option B: Third-Party Gateway (Easier)**
- Use services like Whatsify, Twilio, MessageBird
- Provides webhook URL and API credentials
- **Cost**: Varies by provider

**Option C: Self-Hosted (Advanced)**
- Use Baileys library
- Requires technical expertise
- **Cost**: Free (infrastructure costs only)

---

## 🖥️ System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 10 GB
- **OS**: Windows 10+, Ubuntu 20.04+, macOS 11+

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8 GB
- **Storage**: 20 GB SSD
- **OS**: Windows 11, Ubuntu 22.04, macOS 13+

### Production Requirements
- **CPU**: 8+ cores
- **RAM**: 16 GB
- **Storage**: 50 GB SSD
- **Database**: Dedicated SQL Server instance
- **Network**: Static IP, domain with SSL

---

## 🔧 Backend Setup

### Step 1: Clone Repository

```bash
git clone <your-repository-url>
cd ExhibitionVistingCard
```

### Step 2: Create Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all Python packages
pip install -r requirements.txt

# This will install:
# - fastapi
# - uvicorn
# - pyodbc
# - openai
# - easyocr
# - opencv-python
# - pillow
# - pydub
# - python-multipart
# - python-dotenv
# - apscheduler
# - websockets
# - requests
# - and more...
```

### Step 4: Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Copy example file
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Contents of `.env`**:

```env
# Application
APP_NAME=INDAS Exhibition Lead Capture System
APP_VERSION=2.0.0
ENVIRONMENT=development
DEBUG=True

# Database (MSSQL)
MSSQL_CONN_STRING=Driver={ODBC Driver 17 for SQL Server};Server=localhost\SQLEXPRESS;Database=ELCS_DB;Trusted_Connection=yes;
# For Azure SQL:
# MSSQL_CONN_STRING=Driver={ODBC Driver 17 for SQL Server};Server=your-server.database.windows.net;Database=ELCS_DB;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=2000

# WhatsApp (adjust based on your provider)
WHATSAPP_API_URL=http://103.150.136.76:8090
WHATSAPP_API_KEY=your-api-key-here
WHATSAPP_ACCOUNT_TOKEN=your-account-token-here
WHATSAPP_PHONE_NUMBER=919876543210
EXHIBITION_ADMIN_PHONE=916263235861

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
```

### Step 5: Verify Installation

```bash
# Test imports
python -c "import fastapi, openai, easyocr, cv2, pyodbc"

# If no errors, installation is successful!
```

---

## 🗄️ Database Setup

### Step 1: Create Database

Open SQL Server Management Studio (SSMS) and run:

```sql
CREATE DATABASE ELCS_DB;
GO

USE ELCS_DB;
GO
```

### Step 2: Run Migration Scripts

Execute the SQL scripts in order:

#### **Script 1: Create Tables**

```bash
# Location: backend/scripts/sql/001_create_tables.sql
```

In SSMS:
1. File → Open → `backend/scripts/sql/001_create_tables.sql`
2. Click "Execute" (F5)
3. Verify: 22 tables created

#### **Script 2: Drip System V2**

```bash
# Location: backend/scripts/sql/002_drip_v2.sql
```

In SSMS:
1. File → Open → `backend/scripts/sql/002_drip_v2.sql`
2. Click "Execute" (F5)
3. Verify: 5 additional tables created

#### **Script 3: Conversation State**

```bash
# Location: backend/scripts/sql/add_conversation_state.sql
```

In SSMS:
1. File → Open → `backend/scripts/sql/add_conversation_state.sql`
2. Click "Execute" (F5)
3. Verify: `ConversationState` column added to Leads table

#### **Script 4: Sample Data (Optional)**

```bash
# Location: backend/scripts/sql/003_sample_data.sql
```

This creates test data for development.

### Step 3: Verify Database Setup

```sql
-- Check tables
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- Should show 27+ tables

-- Check Leads table has ConversationState
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'Leads';
```

---

## 🎨 Frontend Setup

### Step 1: Install Dependencies

```bash
cd ../frontend

# Install all Node packages
npm install

# This will install:
# - next
# - react
# - typescript
# - tailwindcss
# - axios
# - recharts
# - lucide-react
# - and more...
```

### Step 2: Configure Environment

Create `.env.local` file in `frontend/` directory:

```env
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# App Info
NEXT_PUBLIC_APP_NAME=INDAS ELCS
```

### Step 3: Verify Installation

```bash
# Check for errors
npm run build

# If successful, the build will complete without errors
```

---

## ▶️ Running the System

### Start Backend Server

```bash
cd backend

# Activate virtual environment (if not already active)
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Start FastAPI server
uvicorn app.main:app --reload --port 8000

# Server will start at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
✅ Storage directories initialized
✅ Database connection established
✅ APScheduler started
```

### Start Frontend Server

Open a **new terminal**:

```bash
cd frontend

# Start Next.js development server
npm run dev

# Server will start at: http://localhost:3000
```

**Expected Output**:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
event - compiled client and server successfully
```

### Access the Application

Open browser and navigate to:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

---

## 📱 WhatsApp Integration

### Step 1: Set Up Webhook

1. **Get Public URL**:
   - Use ngrok: `ngrok http 8000`
   - Or deploy backend to a server with public IP
   - Example: `https://your-domain.com` or `https://abc123.ngrok.io`

2. **Configure Webhook in WhatsApp**:
   - Go to your WhatsApp Business API dashboard
   - Set webhook URL: `https://your-domain.com/api/whatsapp/webhook`
   - Set verify token: `exhibition_lead_capture_verify`
   - Subscribe to events: `messages`, `message_status`

### Step 2: Test WhatsApp Connection

```bash
# Test sending a message via API
curl -X POST http://localhost:8000/api/whatsapp/send-test \
  -H "Content-Type: application/json" \
  -d '{"phone": "919876543210", "message": "Test message"}'
```

### Step 3: Create QR Code

```sql
-- Insert exhibition with QR code
INSERT INTO Exhibitions (ExhibitionName, StartDate, EndDate, Location, QRCodeData)
VALUES (
  'Test Exhibition 2025',
  '2025-01-01',
  '2025-01-05',
  'Delhi',
  'https://wa.me/919876543210?text=Hi%20INDAS%20Analytics'
);
```

Generate QR code at: http://localhost:3000/whatsapp-qr

---

## 🧪 Testing the System

### Test 1: Employee Card Scanning

1. Navigate to http://localhost:3000/capture
2. Login with test employee:
   - Username: `admin` or `jatin`
   - Password: `admin123` or `jatin123`
3. Upload a business card image
4. Wait for extraction
5. Review extracted data
6. Submit lead

**Expected**: Lead created in database with all extracted fields

### Test 2: WhatsApp Flow

1. Send business card image to WhatsApp number
2. System should reply: "Card received! Extracting data..."
3. Wait ~5 seconds
4. System sends extracted data for confirmation
5. Reply "Yes" to confirm
6. System confirms: "Thank you! Data saved."

**Expected**: Lead created with `StatusCode='confirmed'`

### Test 3: Correction Flow

1. After extraction confirmation, reply: "Designation-HR"
2. System should apply correction instantly
3. Reply with: "✅ Thank you! The following corrections have been applied: • Designation: HR"

**Expected**: `PrimaryVisitorDesignation` updated to "HR" in database

### Test 4: Demo Scheduling

1. From visitor WhatsApp, send: "schedule demo"
2. System should reply with scheduled time (tomorrow 4 PM)
3. Check employee WhatsApp for notification

**Expected**: FollowUp created, employee receives notification

### Test 5: Employee Internal Message

1. From employee Jatin's WhatsApp, send: "Hii"
2. System should NOT send auto-reply
3. Message logged internally

**Expected**: No reply sent, message in database

---

## 🐛 Troubleshooting

### Backend Issues

#### **Error: "Module not found"**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### **Error: "Database connection failed"**
- Check SQL Server is running
- Verify connection string in `.env`
- Test with SSMS connection
- Check firewall settings

#### **Error: "OpenAI API key invalid"**
- Verify API key format (should start with `sk-`)
- Check OpenAI account has credits
- Test key at https://platform.openai.com/playground

### Frontend Issues

#### **Error: "Cannot connect to API"**
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS settings in backend

#### **Error: "Module not found"**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### WhatsApp Issues

#### **Webhook not receiving messages**
- Check webhook URL is public (not localhost)
- Verify webhook verification token matches
- Check WhatsApp webhook logs for errors
- Test with ngrok if local development

#### **Messages not sending**
- Verify WhatsApp API credentials
- Check WhatsApp phone number is correct
- Ensure recipient opted in (business requirement)
- Check API rate limits

### Database Issues

#### **Table does not exist**
- Run migration scripts in order
- Check database name is correct
- Verify user has create table permissions

#### **ConversationState column missing**
- Run `add_conversation_state.sql` migration
- Check column exists:
  ```sql
  SELECT * FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_NAME='Leads' AND COLUMN_NAME='ConversationState'
  ```

---

## 🔒 Security Checklist

Before going to production:

- [ ] Change `JWT_SECRET` to a strong random value
- [ ] Set `DEBUG=False` in production
- [ ] Use HTTPS for all endpoints
- [ ] Set up firewall rules
- [ ] Enable SQL Server authentication (not Trusted_Connection)
- [ ] Rotate OpenAI API key regularly
- [ ] Set up database backups
- [ ] Enable WhatsApp webhook signature verification
- [ ] Use environment variables (never commit `.env`)
- [ ] Set up monitoring and logging

---

## 📞 Support

If you encounter issues not covered here:

1. Check **API documentation**: http://localhost:8000/docs
2. Review **project status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
3. Read **main documentation**: [README.md](README.md)
4. Check backend logs for error messages
5. Verify all environment variables are set correctly

---

## 🎉 Next Steps

After successful setup:

1. **Create employees**: http://localhost:3000/employees
2. **Create exhibition**: Insert into Exhibitions table
3. **Generate QR code**: http://localhost:3000/whatsapp-qr
4. **Set up drip campaigns**: http://localhost:3000/drips
5. **Create message templates**: http://localhost:3000/messages
6. **Test with real business cards**
7. **Monitor analytics**: http://localhost:3000/analytics

---

## 🚀 Production Deployment

For production deployment:

1. **Database**: Migrate to production SQL Server or Azure SQL
2. **Backend**: Deploy to cloud (Azure, AWS, DigitalOcean)
3. **Frontend**: Deploy to Vercel, Netlify, or cloud hosting
4. **Domain**: Configure custom domain with SSL
5. **WhatsApp**: Use production WhatsApp Business API
6. **Monitoring**: Set up application monitoring (Sentry, DataDog)
7. **Backups**: Configure automated database backups

---

*Last Updated: November 26, 2025*
*Version: 2.0.0*
